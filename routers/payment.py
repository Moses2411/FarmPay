"""
FarmPay Payment Router - Squad Payment Gateway
"""

import os
import hmac
import hashlib
import json
from uuid import UUID
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Order, Payment, User, Notification
from db.schemas import PaymentVerifyRequest
from services.squad_payment import (
    initiate_payment as squad_initiate,
    verify_payment as squad_verify,
)
from authentication.OAuth2 import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY", "")


def _is_success(status: str) -> bool:
    return str(status).strip().lower() == "success"


def _verify_squad_signature(raw_body: bytes, signature: str) -> bool:
    if not SQUAD_SECRET_KEY or not signature:
        return True
    expected = hmac.new(
        SQUAD_SECRET_KEY.encode(),
        raw_body,
        hashlib.sha512,
    ).hexdigest().upper()
    return hmac.compare_digest(expected, signature.strip().upper())


def _confirm_payment(payment: Payment, order: Order, db: Session):
    if payment.status == "paid":
        return
    payment.status = "paid"
    payment.paid_at = datetime.utcnow()
    payment.escrow_status = "held"
    order.payment_status = "paid"
    order.status = "paid"
    order.escrow_status = "held"
    notification = Notification(
        user_id=order.buyer_id,
        title="Payment Confirmed",
        message=f"Your payment of N{payment.amount:,.2f} has been confirmed.",
    )
    db.add(notification)
    db.commit()


@router.post("/initiate/{order_id}")
def initiate_payment(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "buyer":
        raise HTTPException(403, "Only buyers can initiate payments")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.buyer_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(404, "Order not found")

    if order.payment_status == "paid":
        raise HTTPException(400, "Order already paid")

    existing_payment = db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.status == "paid",
    ).first()

    if existing_payment:
        raise HTTPException(400, "Payment already completed")

    existing_payment = db.query(Payment).filter(
        Payment.order_id == order.id,
    ).first()

    try:
        payment_info = squad_initiate(
            amount_kobo=int(order.total_amount * 100),
            buyer_email=current_user.email,
            buyer_name=current_user.full_name,
        )
    except Exception as e:
        raise HTTPException(502, f"Could not reach Squad: {str(e)}")

    if existing_payment:
        existing_payment.payment_reference = payment_info["transaction_ref"]
        existing_payment.payment_gateway = "squad"
        existing_payment.status = "pending"
    else:
        db.add(Payment(
            order_id=order.id,
            payment_reference=payment_info["transaction_ref"],
            payment_gateway="squad",
            amount=order.total_amount,
            status="pending",
            escrow_status="held",
        ))
    db.commit()

    return {
        "checkout_url": payment_info["checkout_url"],
        "transaction_ref": payment_info["transaction_ref"],
        "amount": order.total_amount,
        "transaction_amount": payment_info["transaction_amount"],
        "authorized_channels": payment_info["authorized_channels"],
        "currency": payment_info["currency"],
        "merchant_id": payment_info["merchant_id"],
        "order_id": str(order.id),
    }


@router.post("/verify")
def verify_payment(
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(
        Payment.payment_reference == payload.transaction_ref
    ).first()

    if not payment:
        raise HTTPException(404, "Transaction reference not found")

    if payment.status == "paid":
        return {
            "message": "Payment already confirmed",
            "order_id": str(payment.order_id),
            "escrow_status": payment.escrow_status,
        }

    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    try:
        result = squad_verify(payload.transaction_ref)
    except Exception as e:
        raise HTTPException(502, f"Could not reach Squad: {str(e)}")

    if result.get("transaction_status") == "Success":
        _confirm_payment(payment, order, db)
        return {
            "message": "Payment confirmed. Funds held in escrow until delivery.",
            "order_id": str(order.id),
            "amount": payment.amount,
            "escrow_status": payment.escrow_status,
        }
    else:
        payment.status = "failed"
        order.payment_status = "failed"
        db.commit()
        raise HTTPException(
            400,
            f"Payment not successful. Status: {result.get('transaction_status')}"
        )


@router.post("/webhook")
async def squad_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("x-squad-encrypted-body", "")

    if SQUAD_SECRET_KEY and signature:
        if not _verify_squad_signature(raw_body, signature):
            return Response(status_code=200, content="invalid signature")

    try:
        event_data = json.loads(raw_body)
    except Exception:
        return Response(status_code=200, content="bad json")

    event_type = event_data.get("Event", "")
    body = event_data.get("Body", {})

    transaction_ref = body.get("transaction_ref", "")
    transaction_status = body.get("transaction_status", "")

    if event_type != "charge_completed":
        return Response(status_code=200, content="event not handled")

    if not _is_success(transaction_status):
        return Response(status_code=200, content="not success")

    if not transaction_ref:
        return Response(status_code=200, content="no ref")

    payment = db.query(Payment).filter(
        Payment.payment_reference == transaction_ref
    ).first()

    if not payment:
        return Response(status_code=200, content="no record")

    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if order:
        _confirm_payment(payment, order, db)

    return Response(status_code=200, content="ok")


@router.get("/callback")
def squad_callback(
    transaction_ref: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not transaction_ref:
        return {"message": "No transaction reference"}

    payment = db.query(Payment).filter(
        Payment.payment_reference == transaction_ref
    ).first()

    if not payment:
        return {"message": "Transaction not found", "transaction_ref": transaction_ref}

    if payment.status == "paid":
        return {
            "message": "Payment confirmed",
            "order_id": str(payment.order_id),
            "status": "paid",
        }

    try:
        result = squad_verify(transaction_ref)
        transaction_status = result.get("transaction_status", "")
    except Exception:
        transaction_status = ""

    if _is_success(transaction_status):
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            _confirm_payment(payment, order, db)
        return {
            "message": "Payment confirmed",
            "order_id": str(payment.order_id),
            "status": "paid",
        }

    return {
        "message": "Payment pending",
        "transaction_ref": transaction_ref,
        "hint": "Complete payment on checkout page, then call /payments/verify",
    }
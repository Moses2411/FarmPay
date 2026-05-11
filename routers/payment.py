import os
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from db.database import get_db
from db.model import Order, Payment, FarmerProfile, User, Dispute
from db.schemas import (
    PaymentVerifyRequest,
    OTPVerifyRequest,
    DisputeCreate,
    SquadInitiateRequest,
    SquadInitiateResponse,
    SquadWebhookPayload,
)
from services.payment import initiate_payment as isw_initiate, verify_payment as isw_verify
from services.squad_payment import (
    initiate_payment as squad_initiate,
    verify_payment as squad_verify,
)
from services.payout import release_funds_to_farmer
from authentication.OAuth2 import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate/{order_id}")
def initiate_order_payment(
    order_id: UUID,
    payment_gateway: str = "squad",
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
        Payment.order_id == order.id
    ).first()

    if existing_payment and existing_payment.status == "paid":
        raise HTTPException(400, "Payment already completed")

    if payment_gateway == "squad":
        amount_kobo = int(order.total_amount * 100)
        payment_info = squad_initiate(
            amount_kobo=amount_kobo,
            buyer_email=current_user.email,
            buyer_name=current_user.full_name,
        )

        if existing_payment:
            existing_payment.payment_reference = payment_info["transaction_ref"]
            existing_payment.payment_gateway = "squad"
            existing_payment.status = "pending"
        else:
            new_payment = Payment(
                order_id=order.id,
                payment_reference=payment_info["transaction_ref"],
                payment_gateway="squad",
                amount=order.total_amount,
                status="pending",
                escrow_status="held",
            )
            db.add(new_payment)

        db.commit()

        return {
            "transaction_ref": payment_info["transaction_ref"],
            "checkout_url": payment_info["checkout_url"],
            "transaction_amount": payment_info["transaction_amount"],
            "authorized_channels": payment_info["authorized_channels"],
            "currency": payment_info["currency"],
            "merchant_id": payment_info["merchant_id"],
            "order_id": str(order.id),
            "payment_gateway": "squad",
        }

    else:
        payment_info = isw_initiate(
            amount_naira=order.total_amount,
            buyer_email=current_user.email,
            buyer_name=current_user.full_name,
        )

        if existing_payment:
            existing_payment.payment_reference = payment_info["transaction_ref"]
            existing_payment.payment_gateway = "interswitch"
            existing_payment.status = "pending"
        else:
            new_payment = Payment(
                order_id=order.id,
                payment_reference=payment_info["transaction_ref"],
                payment_gateway="interswitch",
                amount=order.total_amount,
                status="pending",
                escrow_status="held",
            )
            db.add(new_payment)

        db.commit()

        return {
            "merchant_code": payment_info["merchant_code"],
            "pay_item_id": payment_info["pay_item_id"],
            "transaction_ref": payment_info["transaction_ref"],
            "amount_kobo": payment_info["amount_kobo"],
            "hash": payment_info["hash"],
            "currency": payment_info["currency"],
            "customer_email": payment_info["customer_email"],
            "customer_name": payment_info["customer_name"],
            "mode": payment_info["mode"],
            "order_id": str(order.id),
            "payment_gateway": "interswitch",
        }


@router.post("/verify")
def verify_order_payment(
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
        raise HTTPException(400, "Payment already verified")

    order = db.query(Order).filter(Order.id == payment.order_id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    if payment.payment_gateway == "squad":
        try:
            result = squad_verify(payload.transaction_ref)
        except Exception as e:
            raise HTTPException(502, f"Could not reach Squad: {str(e)}")

        if result.get("transaction_status") == "Success":
            payment.status = "paid"
            payment.paid_at = datetime.utcnow()
            payment.escrow_status = "held"
            order.payment_status = "paid"
            order.status = "paid"
            order.escrow_status = "held"
            db.commit()
            return {
                "message": "Payment confirmed. Funds held in escrow until delivery.",
                "order_id": str(order.id),
                "amount": payment.amount,
                "escrow_status": order.escrow_status,
                "transaction_status": result.get("transaction_status"),
            }
        else:
            payment.status = "failed"
            order.payment_status = "failed"
            db.commit()
            raise HTTPException(
                400,
                f"Payment not successful. Status: {result.get('transaction_status')}"
            )

    else:
        amount_kobo = int(payment.amount * 100)
        try:
            result = isw_verify(payload.transaction_ref, amount_kobo)
        except Exception as e:
            raise HTTPException(502, f"Could not reach Interswitch: {str(e)}")

        if result.get("ResponseCode") != "00":
            payment.status = "failed"
            order.payment_status = "failed"
            db.commit()
            raise HTTPException(
                400,
                f"Payment not successful. Code: {result.get('ResponseCode')}"
            )

        payment.status = "paid"
        payment.paid_at = datetime.utcnow()
        payment.escrow_status = "held"
        order.payment_status = "paid"
        order.status = "paid"
        order.escrow_status = "held"

        db.commit()

        return {
            "message": "Payment confirmed. Funds held in escrow until delivery.",
            "order_id": str(order.id),
            "amount": payment.amount,
            "escrow_status": order.escrow_status,
        }


@router.post("/webhook")
async def squad_webhook(
    payload: SquadWebhookPayload,
    db: Session = Depends(get_db),
):
    transaction_ref = payload.TransactionRef
    event = payload.Event
    body = payload.Body

    payment = db.query(Payment).filter(
        Payment.payment_reference == transaction_ref
    ).first()

    if not payment:
        return {"status": "error", "message": "Payment not found"}

    if event == "charge_successful":
        order = db.query(Order).filter(Order.id == payment.order_id).first()

        payment.status = "paid"
        payment.paid_at = datetime.utcnow()
        payment.escrow_status = "held"

        if order:
            order.payment_status = "paid"
            order.status = "paid"
            order.escrow_status = "held"

        db.commit()
        return {"status": "success"}

    elif event == "charge_failed":
        payment.status = "failed"
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.payment_status = "failed"
        db.commit()
        return {"status": "success"}

    return {"status": "received"}


@router.post("/callback")
async def squad_callback(
    transaction_ref: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if status == "successful" or status == "Success":
        payment = db.query(Payment).filter(
            Payment.payment_reference == transaction_ref
        ).first()

        if payment and payment.status != "paid":
            order = db.query(Order).filter(Order.id == payment.order_id).first()

            payment.status = "paid"
            payment.paid_at = datetime.utcnow()
            payment.escrow_status = "held"

            if order:
                order.payment_status = "paid"
                order.status = "paid"
                order.escrow_status = "held"

            db.commit()

    return {"status": "ok"}
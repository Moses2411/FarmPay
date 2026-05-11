"""
routers/payment.py
Squad Co payment router for FarmPay.

Endpoints:
  POST /payments/initiate/{order_id}  — buyer triggers checkout, returns checkout_url
  POST /payments/verify               — frontend confirms after Squad modal completes
  POST /payments/webhook              — Squad server-to-server push notification
  GET  /payments/callback             — browser redirect after checkout
"""

import os
import hmac
import hashlib
import json
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Order, Payment, User, Notification
from db.schemas import PaymentVerifyRequest
from services.payment import initiate_payment, verify_payment
from authentication.OAuth2 import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY", "")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_success_status(status: str) -> bool:
    """
    Squad returns 'Success' from verify endpoint but 'success' in some other
    contexts. Compare case-insensitively so both work.
    """
    return str(status).strip().lower() == "success"


def _verify_squad_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Squad signs webhook body with HMAC-SHA512 using your secret key.
    Header: x-squad-encrypted-body  (uppercase hex string)
    """
    expected = hmac.new(
        SQUAD_SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest().upper()
    return hmac.compare_digest(expected, signature_header.strip().upper())


def _confirm_payment_in_db(payment: Payment, order: Order, db: Session) -> None:
    """
    Mark payment and order as paid, lock escrow.
    Idempotent — safe to call from both /verify and /webhook.
    """
    if payment.status == "paid":
        return  # already processed, skip

    payment.status = "paid"
    payment.paid_at = datetime.utcnow()
    payment.escrow_status = "held"
    payment.payment_gateway = "squad"

    order.payment_status = "paid"
    order.status = "paid"
    order.escrow_status = "held"

    notification = Notification(
        user_id=order.buyer_id,
        title="Payment Confirmed",
        message=(
            f"Your payment of N{payment.amount:,.2f} has been confirmed. "
            "Funds are held in escrow and will be released after delivery."
        ),
    )
    db.add(notification)
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Initiate payment
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/initiate/{order_id}")
def initiate_order_payment(
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

    existing_payment = db.query(Payment).filter(Payment.order_id == order.id).first()

    if existing_payment and existing_payment.status == "paid":
        raise HTTPException(400, "Payment already completed")

    try:
        payment_info = initiate_payment(
            amount_naira=order.total_amount,
            buyer_email=current_user.email,
            buyer_name=current_user.full_name,
        )
    except Exception as e:
        raise HTTPException(502, f"Could not reach Squad: {str(e)}")

    if existing_payment:
        existing_payment.payment_reference = payment_info["transaction_ref"]
        existing_payment.status = "pending"
        existing_payment.payment_gateway = "squad"
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
        "amount_kobo": payment_info["amount_kobo"],
        "customer_email": payment_info["customer_email"],
        "order_id": str(order.id),
        "message": "Open checkout_url to complete payment.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Frontend verify (called after Squad modal onSuccess)
# ─────────────────────────────────────────────────────────────────────────────

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

    # Already handled (by webhook or previous verify call)
    if payment.status == "paid":
        return {
            "message": "Payment already confirmed",
            "order_id": str(payment.order_id),
            "escrow_status": payment.escrow_status,
        }

    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    # Re-verify with Squad server-side — never trust frontend alone
    try:
        result = verify_payment(payload.transaction_ref)
    except Exception as e:
        raise HTTPException(502, f"Could not reach Squad: {str(e)}")

    transaction_status = result.get("transaction_status", "")

    if not _is_success_status(transaction_status):
        payment.status = "failed"
        order.payment_status = "failed"
        db.commit()
        raise HTTPException(
            400,
            f"Payment not completed. Squad status: '{transaction_status}'. "
            "Please complete payment on the checkout page, then try again."
        )

    _confirm_payment_in_db(payment, order, db)

    return {
        "message": "Payment confirmed. Funds held in escrow until delivery.",
        "order_id": str(order.id),
        "amount": payment.amount,
        "escrow_status": order.escrow_status,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Squad Webhook (server-to-server, most reliable path)
#
# Register on Squad Dashboard → Settings → Webhook:
#   Production:  https://your-domain.com/payments/webhook
#   Local dev:   https://xxxx.ngrok.io/payments/webhook  (use ngrok)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def squad_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()

    # 1. Verify Squad signature
    signature = request.headers.get("x-squad-encrypted-body", "")

    if SQUAD_SECRET_KEY and signature:
        if not _verify_squad_signature(raw_body, signature):
            print("[SQUAD WEBHOOK] Invalid signature — ignoring")
            return Response(status_code=200, content="invalid signature")
    else:
        print("[SQUAD WEBHOOK] No signature header — skipping verification")

    # 2. Parse body
    try:
        event = json.loads(raw_body)
    except Exception:
        return Response(status_code=200, content="bad json")

    event_type = event.get("Event", "")
    body = event.get("Body", event.get("data", {}))

    transaction_ref = (
        body.get("transaction_ref")
        or body.get("transaction_reference")
        or ""
    )
    transaction_status = body.get("transaction_status", "")

    print(f"[SQUAD WEBHOOK] event={event_type} | ref={transaction_ref} | status={transaction_status}")

    # 3. Only handle successful charge events
    if event_type != "charge_completed":
        return Response(status_code=200, content="event not handled")

    if not _is_success_status(transaction_status):
        print(f"[SQUAD WEBHOOK] Non-success status '{transaction_status}' — skipping")
        return Response(status_code=200, content="not a success event")

    if not transaction_ref:
        return Response(status_code=200, content="no ref")

    # 4. Find and update payment record
    payment = db.query(Payment).filter(
        Payment.payment_reference == transaction_ref
    ).first()

    if not payment:
        print(f"[SQUAD WEBHOOK] No payment record for ref '{transaction_ref}'")
        return Response(status_code=200, content="no record")

    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if not order:
        return Response(status_code=200, content="no order")

    # 5. Confirm — idempotent, safe if already paid
    _confirm_payment_in_db(payment, order, db)

    print(f"[SQUAD WEBHOOK] Order {order.id} marked paid via webhook")
    return Response(status_code=200, content="ok")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Browser callback after Squad checkout modal closes
# No auth needed — this is a browser redirect.
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/callback")
def squad_callback(
    transaction_ref: str = None,
    db: Session = Depends(get_db),
):
    if not transaction_ref:
        return {"message": "No transaction reference provided"}

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
        result = verify_payment(transaction_ref)
    except Exception as e:
        return {"message": f"Verification error: {str(e)}"}

    transaction_status = result.get("transaction_status", "")
    order = db.query(Order).filter(Order.id == payment.order_id).first()

    if _is_success_status(transaction_status) and order:
        _confirm_payment_in_db(payment, order, db)
        return {
            "message": "Payment confirmed",
            "order_id": str(payment.order_id),
            "amount": payment.amount,
            "status": "paid",
        }

    return {
        "message": "Payment not yet confirmed",
        "transaction_ref": transaction_ref,
        "squad_status": transaction_status,
        "hint": "Complete payment on the checkout page, then POST to /payments/verify",
    }
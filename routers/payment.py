import os
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Order, Payment, FarmerProfile, User, Dispute
from db.schemas import PaymentVerifyRequest, OTPVerifyRequest, DisputeCreate
from services.payment import initiate_payment, verify_payment
from services.payout import release_funds_to_farmer
from authentication.OAuth2 import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])


# ── STEP 1 ────────────────────────────────────────────────
# Buyer calls this after order is created
# Returns config for frontend to call webpayCheckout()
# ─────────────────────────────────────────────────────────
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

    existing_payment = db.query(Payment).filter(
        Payment.order_id == order.id
    ).first()

    if existing_payment and existing_payment.status == "paid":
        raise HTTPException(400, "Payment already completed")

    # Build checkout config — no Interswitch API call here
    payment_info = initiate_payment(
        amount_naira=order.total_amount,
        buyer_email=current_user.email,
        buyer_name=current_user.full_name,
    )

    # Save or update pending payment record
    if existing_payment:
        existing_payment.payment_reference = payment_info["transaction_ref"]
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

    # Return everything the frontend needs for webpayCheckout()
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
    }


# ── STEP 2 ────────────────────────────────────────────────
# Called by frontend after onComplete fires with resp "00"
# Backend verifies with Interswitch then locks escrow
# ─────────────────────────────────────────────────────────
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

    amount_kobo = int(payment.amount * 100)

    try:
        result = verify_payment(payload.transaction_ref, amount_kobo)
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

    # Confirmed — lock funds in escrow
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
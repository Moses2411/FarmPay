"""
routers/payment.py
Full payment lifecycle:
  1. initiate  → Squad hosted checkout → money lands in YOUR Squad wallet
  2. webhook   → Squad confirms payment → mark escrow "held"
  3. verify    → buyer polls after checkout → server-side confirm
  4. callback  → browser redirect after checkout
  5. release   → OTP confirmed → Transfer API → money moves to farmer's bank

Escrow model:
  Money physically sits in YOUR Squad merchant wallet after the buyer pays.
  It only moves to the farmer when release_escrow_to_farmer() calls payout/transfer.
  Your DB escrow_status column tracks the STATE of that real money.
"""

import logging
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from authentication.OAuth2 import get_current_user
from db.database import get_db
from db.model import FarmerProfile, Notification, Order, OrderItem, Payment, User
from db.schemas import EscrowReleaseResponse, PaymentVerifyRequest
from services.payout import release_funds_to_farmer
from services.squad_payment import (
    initiate_payment as squad_initiate,
    verify_payment as squad_verify,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY", "")

# ── Bank code lookup ──────────────────────────────────────────────────────────
# Extend this dict with all banks your farmers use.
# Source: https://docs.squadco.com or CBN NIP bank codes
BANK_CODE_MAP = {
    "access bank": "044",
    "gtbank": "058",
    "guaranty trust bank": "058",
    "gt bank": "058",
    "first bank": "011",
    "uba": "033",
    "united bank for africa": "033",
    "zenith bank": "057",
    "zenith": "057",
    "polaris bank": "076",
    "polaris": "076",
    "fidelity bank": "070",
    "fidelity": "070",
    "stanbic ibtc": "068",
    "stanbic": "068",
    "union bank": "032",
    "ecobank": "050",
    "sterling bank": "232",
    "sterling": "232",
    "wema bank": "035",
    "wema": "035",
    "kuda": "090267",
    "kuda bank": "090267",
    "opay": "999992",
    "palmpay": "999991",
}


def get_bank_code(bank_name: str) -> Optional[str]:
    """
    Resolve bank name to NIP code.
    Returns None if not found — caller must handle this.
    """
    return BANK_CODE_MAP.get(bank_name.strip().lower())


# ── Internal escrow helpers ───────────────────────────────────────────────────

def _confirm_payment(payment: Payment, order: Order, db: Session) -> None:
    """
    Mark payment and order as paid. Idempotent — safe to call multiple times.
    Money is now in YOUR Squad merchant wallet (escrow).
    """
    if payment.status == "paid":
        return

    payment.status = "paid"
    payment.paid_at = datetime.utcnow()
    payment.escrow_status = "held"

    order.payment_status = "paid"
    order.status = "paid"
    order.escrow_status = "held"

    db.add(Notification(
        user_id=order.buyer_id,
        title="Payment Confirmed",
        message=f"Your payment of ₦{float(payment.amount):,.2f} is confirmed and held in escrow.",
    ))
    db.commit()
    logger.info(f"[PAYMENT] Confirmed: order={order.id} ref={payment.payment_reference}")


def _release_escrow_to_farmer(order_id: UUID, db: Session) -> dict:
    """
    Core escrow release function.
    Called by:
      - /orders/verify-otp   (buyer confirms delivery via OTP)
      - /admin/dispute/{id}/resolve  (admin rules in favour of farmer)

    Steps:
      1. Load order + payment + farmer profile
      2. Validate state
      3. Call Squad Transfer API (payout.py)
      4. Update DB records
      5. Send notifications
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise Exception(f"Order {order_id} not found")

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise Exception(f"No payment record for order {order_id}")

    if payment.escrow_status == "released":
        logger.info(f"[ESCROW] Already released for order {order_id}")
        return {
            "message": "Already released",
            "payout_reference": payment.payout_reference,
            "payout_status": payment.payout_status,
        }

    if payment.status != "paid":
        raise Exception(f"Cannot release unpaid order {order_id}")

    # Find the farmer via order items
    first_item = db.query(OrderItem).filter(OrderItem.order_id == order_id).first()
    if not first_item:
        raise Exception(f"No order items found for order {order_id}")

    farmer_profile = db.query(FarmerProfile).filter(
        FarmerProfile.user_id == first_item.product.farmer_id
    ).first()
    if not farmer_profile:
        raise Exception("Farmer profile not found")

    # Resolve bank code
    bank_code = farmer_profile.settlement_bank_code
    if not bank_code:
        bank_code = get_bank_code(farmer_profile.bank_name)
    if not bank_code:
        raise Exception(
            f"Cannot resolve bank code for '{farmer_profile.bank_name}'. "
            "Ask farmer to update their bank details."
        )

    account_number = farmer_profile.settlement_account_number or farmer_profile.account_number
    amount_to_release = float(payment.amount)
    str_order_id = str(order_id)

    # Mark payout as pending before calling Squad
    payment.payout_status = "pending"
    payment.payout_initiated_at = datetime.utcnow()
    db.commit()

    # Call Squad Transfer API
    try:
        result = release_funds_to_farmer(
            farmer_account_number=account_number,
            farmer_bank_code=bank_code,
            farmer_name=farmer_profile.business_name or "Farmer",
            amount_naira=amount_to_release,
            order_id=str_order_id,
        )
    except Exception as e:
        payment.payout_status = "failed"
        db.commit()
        raise Exception(f"Payout failed: {str(e)}")

    # Update DB on success
    payout_reference = result.get("transaction_reference", "")
    payment.escrow_status = "released"
    payment.released_at = datetime.utcnow()
    payment.payout_reference = payout_reference
    payment.payout_status = "success"

    order.escrow_status = "released"
    order.status = "completed"

    # Deduct from farmer's tracked escrow balance
    current_balance = float(farmer_profile.escrow_balance or 0)
    farmer_profile.escrow_balance = max(0, current_balance - amount_to_release)
    farmer_profile.total_sales = float(farmer_profile.total_sales or 0) + amount_to_release

    # Notify farmer
    db.add(Notification(
        user_id=farmer_profile.user_id,
        title="Payment Released",
        message=(
            f"₦{amount_to_release:,.2f} has been transferred to your bank account "
            f"({account_number}). Order {str_order_id[:8]} complete."
        ),
    ))

    db.commit()
    logger.info(
        f"[ESCROW] Released ₦{amount_to_release:,.2f} to farmer "
        f"{farmer_profile.business_name} | ref: {payout_reference}"
    )

    return {
        "message": "Escrow released",
        "payout_reference": payout_reference,
        "payout_status": "success",
        "amount_released": amount_to_release,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/initiate/{order_id}")
def initiate_payment_endpoint(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 1: Create a Squad hosted checkout session.
    Buyer is redirected to checkout_url to pay.
    Money lands in YOUR Squad wallet on success.
    """
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

    # Check for existing paid payment record
    existing_paid = db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.status == "paid",
    ).first()
    if existing_paid:
        raise HTTPException(400, "Payment already completed for this order")

    # Re-use pending record if it exists
    existing_pending = db.query(Payment).filter(Payment.order_id == order.id).first()

    try:
        payment_info = squad_initiate(
            amount_kobo=order.total_amount_kobo,
            buyer_email=current_user.email,
            buyer_name=current_user.full_name,
        )
    except Exception as e:
        raise HTTPException(502, f"Could not reach Squad: {str(e)}")

    if existing_pending:
        existing_pending.payment_reference = payment_info["transaction_ref"]
        existing_pending.payment_gateway = "squad"
        existing_pending.status = "pending"
    else:
        db.add(Payment(
            order_id=order.id,
            payment_reference=payment_info["transaction_ref"],
            payment_gateway="squad",
            amount=float(order.total_amount),
            amount_kobo=order.total_amount_kobo,
            status="pending",
            escrow_status="held",
        ))

    db.commit()

    return {
        "checkout_url": payment_info["checkout_url"],
        "transaction_ref": payment_info["transaction_ref"],
        "amount": float(order.total_amount),
        "amount_kobo": order.total_amount_kobo,
        "transaction_amount": payment_info["transaction_amount"],
        "authorized_channels": payment_info["authorized_channels"],
        "currency": payment_info["currency"],
        "merchant_id": payment_info["merchant_id"],
        "order_id": str(order.id),
    }


@router.post("/verify")
def verify_payment_endpoint(
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 2: Buyer calls this after returning from Squad checkout.
    Always verify server-side — never trust client status.
    """
    payment = db.query(Payment).filter(
        Payment.payment_reference == payload.transaction_ref
    ).first()

    if not payment:
        raise HTTPException(404, "Transaction reference not found")

    if payment.status == "paid":
        return {
            "message": "Payment already confirmed. Funds held in escrow.",
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

    if str(result.get("transaction_status", "")).strip().lower() == "success":
        _confirm_payment(payment, order, db)
        return {
            "message": "Payment confirmed. Funds held in escrow until delivery.",
            "order_id": str(order.id),
            "amount": float(payment.amount),
            "escrow_status": payment.escrow_status,
        }

    payment.status = "failed"
    order.payment_status = "failed"
    db.commit()

    raise HTTPException(
        400,
        f"Payment not successful. Status: {result.get('transaction_status')}",
    )


@router.post("/webhook/payment")
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Squad webhook — called when hosted checkout payment completes.
    Also handles Dynamic VA events (mismatch, expired, completed).
    Squad requires HTTP 200 always — even for events we don't handle.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-squad-encrypted-body", "")

    if not verify_webhook_signature(raw_body, signature, SQUAD_SECRET_KEY):
        logger.warning("[WEBHOOK] Invalid signature — rejecting")
        # Still return 200 so Squad doesn't retry indefinitely
        return Response(status_code=200, content="invalid signature")

    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=200, content="bad json")

    event_type = payload.get("Event", "")
    body = payload.get("Body", payload.get("data", {}))

    logger.info(f"[WEBHOOK] Event: {event_type}")

    # ── Dynamic VA events ─────────────────────────────────────────────────
    if event_type in ("payment.mismatch", "payment.expired"):
        # Squad auto-refunds these — just log and ack
        logger.info(f"[WEBHOOK] {event_type} — Squad handles auto-refund")
        return Response(status_code=200, content="ok")

    # ── Hosted checkout payment ───────────────────────────────────────────
    if event_type == "charge.completed":
        transaction_ref = body.get("transaction_ref", "")
        amount_kobo = body.get("amount", 0)

        payment = db.query(Payment).filter(
            Payment.payment_reference == transaction_ref
        ).first()

        if not payment:
            logger.warning(f"[WEBHOOK] No payment found for ref: {transaction_ref}")
            return Response(status_code=200, content="no match")

        if payment.status == "paid":
            return Response(status_code=200, content="already processed")

        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            _confirm_payment(payment, order, db)
            logger.info(f"[WEBHOOK] Confirmed order {order.id} via webhook")

        return Response(status_code=200, content="ok")

    # ── VA payment.completed ──────────────────────────────────────────────
    if event_type == "payment.completed":
        account_number = body.get("account_number", "")
        amount_kobo = int(body.get("principal_amount", body.get("amount", 0)))
        transaction_ref = body.get("transaction_ref", body.get("transaction_reference", ""))

        farmer_profile = db.query(FarmerProfile).filter(
            FarmerProfile.virtual_account_number == account_number
        ).first()

        if not farmer_profile:
            logger.warning(f"[WEBHOOK] No farmer for VA: {account_number}")
            return Response(status_code=200, content="no farmer")

        # Match order by kobo amount + farmer + pending status
        # We match on kobo (integer) — no float equality risk
        pending_orders = (
            db.query(Order)
            .join(OrderItem)
            .join(Order.items)
            .filter(
                Order.payment_status == "pending",
                Order.total_amount_kobo == amount_kobo,
            )
            .order_by(Order.created_at.desc())
            .all()
        )

        # Find an order whose items belong to this farmer
        matched_order = None
        for o in pending_orders:
            for item in o.items:
                if str(item.product.farmer_id) == str(farmer_profile.user_id):
                    matched_order = o
                    break
            if matched_order:
                break

        if matched_order:
            payment = db.query(Payment).filter(Payment.order_id == matched_order.id).first()
            if not payment:
                payment = Payment(
                    order_id=matched_order.id,
                    payment_reference=transaction_ref,
                    payment_gateway="squad_va",
                    amount=amount_kobo / 100,
                    amount_kobo=amount_kobo,
                    status="paid",
                    escrow_status="held",
                    paid_at=datetime.utcnow(),
                )
                db.add(payment)
            else:
                payment.status = "paid"
                payment.paid_at = datetime.utcnow()
                payment.payment_reference = transaction_ref
                payment.amount_kobo = amount_kobo

            matched_order.payment_status = "paid"
            matched_order.status = "paid"
            matched_order.escrow_status = "held"

            # Track in farmer's escrow balance
            farmer_profile.escrow_balance = float(farmer_profile.escrow_balance or 0) + (amount_kobo / 100)

            db.add(Notification(
                user_id=matched_order.buyer_id,
                title="Payment Confirmed",
                message=f"Your payment of ₦{amount_kobo / 100:,.2f} is confirmed and held in escrow.",
            ))
            db.add(Notification(
                user_id=farmer_profile.user_id,
                title="Payment Received",
                message=f"₦{amount_kobo / 100:,.2f} received and held in escrow pending delivery.",
            ))

            db.commit()
            logger.info(f"[WEBHOOK] VA payment matched to order {matched_order.id}")
        else:
            # Unmatched payment — add to farmer balance for reconciliation
            farmer_profile.escrow_balance = float(farmer_profile.escrow_balance or 0) + (amount_kobo / 100)
            db.commit()
            logger.warning(
                f"[WEBHOOK] Unmatched VA payment: ₦{amount_kobo / 100} for {account_number} "
                f"— added to escrow balance for manual reconciliation"
            )

        return Response(status_code=200, content="ok")

    return Response(status_code=200, content="event not handled")


@router.get("/callback")
def squad_callback(
    transaction_ref: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Browser redirect target after Squad checkout.
    Verifies and confirms payment. Frontend polls this or /payments/verify.
    """
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
            "escrow_status": payment.escrow_status,
        }

    try:
        result = squad_verify(transaction_ref)
        transaction_status = result.get("transaction_status", "")
    except Exception:
        transaction_status = ""

    if str(transaction_status).strip().lower() == "success":
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            _confirm_payment(payment, order, db)
        return {
            "message": "Payment confirmed",
            "order_id": str(payment.order_id),
            "status": "paid",
            "escrow_status": payment.escrow_status,
        }

    return {
        "message": "Payment not yet confirmed",
        "transaction_ref": transaction_ref,
        "hint": "Complete payment on checkout page, then call POST /payments/verify",
    }
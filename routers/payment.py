"""
routers/payment.py
Squad hosted checkout payment - Money lands in your Squad wallet, held in escrow until release
Based on official Squad documentation
"""

import os
import json
import logging
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Order, Payment, User, Notification, FarmerProfile, OrderItem, Product
from db.schemas import PaymentVerifyRequest, PaymentInitiateResponse
from services.squad_payment import (
    initiate_payment,
    verify_payment,
    verify_webhook_signature,
    get_wallet_balance,
)
from authentication.OAuth2 import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


def _confirm_payment(payment: Payment, order: Order, db: Session):
    """
    Mark payment as confirmed - money is in Squad wallet (escrow)
    This does NOT move money to farmer yet.
    """
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
        message=f"Your payment of ₦{payment.amount:,.2f} has been confirmed. Funds are held in escrow until delivery.",
    )
    db.add(notification)
    db.commit()
    logger.info(f"Payment confirmed for order {order.id}, escrow held")


@router.post("/initiate/{order_id}", response_model=PaymentInitiateResponse)
def initiate_order_payment(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 1: Buyer calls this to get Squad hosted checkout URL
    Money will go into your Squad merchant wallet
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

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment and payment.status == "paid":
        raise HTTPException(400, "Payment already completed")

    try:
        payment_info = initiate_payment(
            amount_kobo=order.total_amount_kobo,
            buyer_email=current_user.email,
            buyer_name=current_user.full_name,
        )
    except Exception as e:
        raise HTTPException(502, f"Could not reach Squad: {str(e)}")

    if payment:
        payment.payment_reference = payment_info["transaction_ref"]
        payment.payment_gateway = "squad"
        payment.status = "pending"
    else:
        payment = Payment(
            order_id=order.id,
            payment_reference=payment_info["transaction_ref"],
            payment_gateway="squad",
            amount=order.total_amount,
            amount_kobo=order.total_amount_kobo,
            status="pending",
            escrow_status="held",
        )
        db.add(payment)

    db.commit()

    return PaymentInitiateResponse(
        checkout_url=payment_info["checkout_url"],
        transaction_ref=payment_info["transaction_ref"],
        amount=order.total_amount,
        order_id=str(order.id),
    )


@router.post("/verify")
def verify_order_payment(
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 2: Call this after customer completes checkout
    OR Squad will call your webhook
    """
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
        result = verify_payment(payload.transaction_ref)
    except Exception as e:
        raise HTTPException(502, f"Could not reach Squad: {str(e)}")

    if not result.get("valid"):
        payment.status = "failed"
        order.payment_status = "failed"
        db.commit()
        raise HTTPException(400, f"Payment verification failed: {result.get('error')}")

    if result.get("is_successful"):
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
        raise HTTPException(400, f"Payment not successful. Status: {result.get('transaction_status')}")


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Squad webhook for hosted checkout payments.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-squad-encrypted-body", "")

    # Verify webhook signature
    if not verify_webhook_signature(raw_body, signature):
        logger.warning("Invalid webhook signature - rejecting")
        return Response(status_code=401, content="Invalid signature")

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        return Response(status_code=200, content="bad json")

    event_type = payload.get("Event", "")
    logger.info(f"Webhook received - Event: {event_type}")

    if event_type != "charge_successful":
        logger.info(f"Ignoring event type: {event_type}")
        return Response(status_code=200, content="event not handled")

    body = payload.get("Body", {})
    transaction_ref = body.get("transaction_ref", payload.get("TransactionRef", ""))
    transaction_status = body.get("transaction_status", "")

    logger.info(f"Processing charge_successful for ref: {transaction_ref}, status: {transaction_status}")

    if str(transaction_status).strip().lower() != "success":
        logger.info(f"Transaction not successful: {transaction_status}")
        return Response(status_code=200, content="not success")

    payment = db.query(Payment).filter(
        Payment.payment_reference == transaction_ref
    ).first()

    if not payment:
        logger.warning(f"No payment record found for ref: {transaction_ref}")
        return Response(status_code=200, content="no payment found")

    if payment.status == "paid":
        logger.info(f"Payment already processed for ref: {transaction_ref}")
        return Response(status_code=200, content="already processed")

    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if order:
        _confirm_payment(payment, order, db)
        logger.info(f"Order {order.id} marked as paid via webhook")
    else:
        logger.error(f"Order not found for payment: {payment.order_id}")

    return Response(status_code=200, content="ok")


@router.post("/webhook/va-payment")
async def va_payment_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Squad webhook for Virtual Account payments.
    Also uses "charge_successful" event.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-squad-encrypted-body", "")

    if not verify_webhook_signature(raw_body, signature):
        logger.warning("Invalid VA webhook signature - rejecting")
        return Response(status_code=401, content="Invalid signature")

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse VA webhook JSON: {e}")
        return Response(status_code=200, content="bad json")

    event_type = payload.get("Event", "")
    logger.info(f"VA Webhook received - Event: {event_type}")

    if event_type != "charge_successful":
        return Response(status_code=200, content="event not handled")

    body = payload.get("Body", {})
    account_number = body.get("account_number", "")
    amount_kobo = body.get("amount", 0)
    amount_ngn = amount_kobo / 100
    transaction_ref = body.get("transaction_ref", "")
    customer_email = body.get("email", "")

    logger.info(f"VA Payment: VA {account_number} received ₦{amount_ngn:,.2f}")

    # Find farmer by virtual account number
    farmer_profile = db.query(FarmerProfile).filter(
        FarmerProfile.virtual_account_number == account_number
    ).first()

    if not farmer_profile:
        logger.warning(f"No farmer found for VA: {account_number}")
        return Response(status_code=200, content="no farmer found")

    # Find buyer by email
    buyer = db.query(User).filter(User.email == customer_email).first()

    if not buyer:
        logger.warning(f"No buyer found for email: {customer_email}")
        farmer_profile.escrow_balance += amount_ngn
        db.commit()
        return Response(status_code=200, content="no buyer found")

    # Find pending order - FIXED: removed double join
    order = db.query(Order).filter(
        Order.buyer_id == buyer.id,
        Order.total_amount_kobo == amount_kobo,
        Order.payment_status == "pending"
    ).order_by(Order.created_at.desc()).first()

    if order:
        # Create or update payment record
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        if not payment:
            payment = Payment(
                order_id=order.id,
                payment_reference=transaction_ref,
                payment_gateway="squad_va",
                amount=amount_ngn,
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

        order.payment_status = "paid"
        order.status = "paid"
        order.escrow_status = "held"

        farmer_profile.escrow_balance += amount_ngn

        db.commit()
        logger.info(f"Order {order.id} paid via VA. ₦{amount_ngn} in escrow")

        # Create notification for buyer
        buyer_notification = Notification(
            user_id=buyer.id,
            title="Payment Successful",
            message=f"Your payment of ₦{amount_ngn:,.2f} for order {str(order.id)[:8]} has been confirmed. Funds are held in escrow."
        )
        db.add(buyer_notification)

        farmer_notification = Notification(
            user_id=farmer_profile.user_id,
            title="Payment Received",
            message=f"Payment of ₦{amount_ngn:,.2f} for order {str(order.id)[:8]} has been received and held in escrow pending delivery confirmation."
        )
        db.add(farmer_notification)
        db.commit()
    else:
        # No matching order - add to escrow balance
        farmer_profile.escrow_balance += amount_ngn
        db.commit()
        logger.info(f"Added ₦{amount_ngn} to escrow balance for {farmer_profile.business_name} (no matching order)")

    return Response(status_code=200, content="ok")


@router.get("/callback")
def payment_callback(
    transaction_ref: str = None,
    db: Session = Depends(get_db),
):
    """Browser redirect after checkout - frontend should call /verify"""
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
            "escrow_status": "held",
        }

    # Try to verify the payment
    try:
        result = verify_payment(transaction_ref)
        if result.get("is_successful"):
            order = db.query(Order).filter(Order.id == payment.order_id).first()
            if order:
                _confirm_payment(payment, order, db)
            return {
                "message": "Payment confirmed",
                "order_id": str(payment.order_id),
                "status": "paid",
                "escrow_status": "held",
            }
    except Exception:
        pass

    return {
        "message": "Payment pending. Please check status via /payments/verify",
        "order_id": str(payment.order_id),
        "transaction_ref": transaction_ref,
    }


@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Squad wallet balance (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")

    try:
        balance = get_wallet_balance()
        return {
            "balance_naira": balance["balance_naira"],
            "balance_kobo": balance["balance_kobo"],
            "currency": balance["currency"],
        }
    except Exception as e:
        raise HTTPException(502, f"Failed to get balance: {str(e)}")
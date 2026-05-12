from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from db.database import get_db
from db.model import Order, User, Payment
from authentication.OAuth2 import get_current_user
from uuid import UUID

router = APIRouter(prefix="/rider", tags=["Rider"])


@router.post("/confirm-delivery/{order_id}")
def confirm_delivery(
    order_id: str,
    otp: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "dispatch_rider":
        raise HTTPException(status_code=403, detail="Only riders allowed")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.dispatch_rider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to this delivery")

    if order.is_otp_verified:
        raise HTTPException(status_code=400, detail="Delivery already confirmed")

    if order.otp_code != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    order.is_otp_verified = True
    order.delivery_status = "confirmed"
    order.confirmed_at = datetime.utcnow()

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()

    if payment and payment.escrow_status == "held":
        try:
            payout_response = release_funds_to_farmer(
                farmer_account_number="0000000000",
                farmer_bank_code="000",
                farmer_name="Farmer",
                amount_naira=payment.amount,
                order_id=str(order.id)
            )

            payment.escrow_status = "released"
            payment.released_at = datetime.utcnow()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Payout failed: {str(e)}")

    db.commit()

    return {
        "message": "Delivery confirmed successfully",
        "order_id": str(order.id),
        "delivery_status": order.delivery_status,
        "escrow_status": payment.escrow_status if payment else None
    }


@router.get("/orders")
def get_rider_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "dispatch_rider":
        raise HTTPException(403, "Only dispatch riders allowed")

    orders = db.query(Order).filter(
        Order.dispatch_rider_id == current_user.id
    ).all()

    return [
        {
            "id": str(order.id),
            "buyer_id": str(order.buyer_id),
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_status": order.payment_status,
            "delivery_status": order.delivery_status,
            "escrow_status": order.escrow_status,
            "delivery_location": order.delivery_location,
            "delivery_fee": order.delivery_fee,
            "otp_code": order.otp_code,
            "is_otp_verified": order.is_otp_verified,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
        for order in orders
    ]

@router.patch("/order/{order_id}/picked-up")
def mark_picked_up(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "dispatch_rider":
        raise HTTPException(403, "Only dispatch riders can update this")

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    if str(order.dispatch_rider_id) != str(current_user.id):
        raise HTTPException(403, "This order is not assigned to you")

    if order.payment_status != "paid":
        raise HTTPException(400, "Order has not been paid yet")

    order.delivery_status = "in_transit"
    order.status = "in_transit"
    db.commit()

    return {
        "message": "Order marked as picked up and in transit.",
        "order_id": str(order_id),
    }

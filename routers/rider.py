from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from db.database import get_db
from db.model import FarmerProfile, Order, OrderItem, Payment, Product, User
from authentication.OAuth2 import get_current_user
from authentication.hashing import Hash
from services.payout import release_funds_to_farmer

router = APIRouter(prefix="/rider", tags=["Rider"])


def _verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    return Hash.verify(hashed_otp, plain_otp)


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

    if not order.otp_hash:
        raise HTTPException(status_code=500, detail="No OTP on record for this order")

    if not _verify_otp(otp.strip().upper(), order.otp_hash):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    order.is_otp_verified = True
    order.delivery_status = "confirmed"
    order.confirmed_at = datetime.utcnow()
    order.status = "completed"

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()

    if payment and payment.escrow_status == "held":
        first_item = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
        if first_item:
            product = db.query(Product).filter(Product.id == first_item.product_id).first()
            if product:
                farmer_profile = db.query(FarmerProfile).filter(
                    FarmerProfile.user_id == product.farmer_id
                ).first()

                if farmer_profile and farmer_profile.account_number:
                    try:
                        bank_code = farmer_profile.settlement_bank_code or farmer_profile.bank_code or "058"
                        account_number = farmer_profile.settlement_account_number or farmer_profile.account_number
                        release_funds_to_farmer(
                            farmer_account_number=account_number,
                            farmer_bank_code=bank_code,
                            farmer_name=farmer_profile.business_name or "Farmer",
                            amount_naira=float(payment.amount),
                            order_id=str(order.id)
                        )
                        payment.escrow_status = "released"
                        payment.released_at = datetime.utcnow()
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Payout failed: {str(e)}")

    db.commit()

    current_user.is_available = True
    db.commit()

    return {
        "message": "Delivery confirmed successfully",
        "order_id": str(order.id),
        "delivery_status": order.delivery_status,
        "escrow_status": payment.escrow_status if payment else None
    }


@router.get("/rider/orders")
def get_rider_orders(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "dispatch_rider":
        raise HTTPException(403, "Only dispatch riders allowed")

    orders = db.query(Order).filter(
        Order.dispatch_rider_id == current_user.id
    ).all()

    return orders

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


@router.post("/status")
def update_rider_status(
    is_available: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "dispatch_rider":
        raise HTTPException(403, "Only dispatch riders can update status")

    current_user.is_available = is_available
    db.commit()

    return {
        "message": f"Rider status set to {'available' if is_available else 'busy'}",
        "is_available": current_user.is_available,
    }

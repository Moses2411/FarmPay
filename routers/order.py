"""
routers/orders.py
Order creation and status. OTP is hashed with bcrypt before storage.
"""

import secrets
import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from authentication.OAuth2 import get_current_user
from authentication.hashing import Hash
from db.database import get_db
from db.model import FarmerProfile, Notification, Order, OrderItem, Payment, Product, User
from db.schemas import OrderCreate, OrderStatusResponse, FarmerOrder, FarmerOrderItem
from services.mapbox_service import calculate_delivery_fee, geocode_address

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders"])

DELIVERY_FEE_NAIRA = 2000  # Flat rate — replace with Mapbox calc when ready


def _generate_otp() -> str:
    """Generate a 6-character hex OTP (uppercase)."""
    return secrets.token_hex(3).upper()


def _hash_otp(plain_otp: str) -> str:
    """Hash OTP with bcrypt for safe DB storage."""
    return Hash.hash_password(plain_otp)


def _verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verify submitted OTP against stored hash."""
    return Hash.verify(hashed_otp, plain_otp)


@router.post("/create")
def create_order(
    request: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an order and return payment instructions.
    OTP is returned once here — hashed in DB, never returned again.
    """
    if current_user.role not in ["buyer", "farmer"]:
        raise HTTPException(403, "Only buyers can create orders")

    total_amount_naira = 0
    order_items = []
    farmer_address = None
    farmer_profile = None

    for item in request.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.is_approved == True,
        ).first()

        if not product:
            raise HTTPException(404, f"Product {item.product_id} not found or not approved")

        if item.quantity > product.available_quantity:
            raise HTTPException(400, f"Insufficient quantity for {product.name}")

        current_farmer_profile = db.query(FarmerProfile).filter(
            FarmerProfile.user_id == product.farmer_id
        ).first()

        if not current_farmer_profile:
            raise HTTPException(400, f"Farmer profile not found for product {product.name}")

        if farmer_profile is None:
            farmer_profile = current_farmer_profile

        if farmer_address and farmer_address != current_farmer_profile.location:
            raise HTTPException(400, "All items in one order must be from the same farm location")

        farmer_address = current_farmer_profile.location
        total_amount_naira += float(product.price) * item.quantity
        order_items.append({"product": product, "quantity": item.quantity})

    final_amount_naira = total_amount_naira + DELIVERY_FEE_NAIRA
    final_amount_kobo = int(round(final_amount_naira * 100))

    # Generate OTP — return plaintext once, store hash
    plain_otp = _generate_otp()
    otp_hash = _hash_otp(plain_otp)

    order = Order(
        buyer_id=current_user.id,
        total_amount=final_amount_naira,
        total_amount_kobo=final_amount_kobo,
        status="pending",
        payment_status="pending",
        otp_hash=otp_hash,
        otp_expires_at=datetime.utcnow() + timedelta(hours=48),
        delivery_status="pending",
        escrow_status="held",
        delivery_location=request.delivery_address,
        delivery_fee=DELIVERY_FEE_NAIRA,
        delivery_fee_kobo=DELIVERY_FEE_NAIRA * 100,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    for item in order_items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item["product"].id,
            quantity=item["quantity"],
            price=item["product"].price,
            price_kobo=int(item["product"].price * 100),
        ))
        item["product"].available_quantity -= item["quantity"]

    db.commit()

    # Payment instructions via farmer's Static VA (optional, for direct bank transfer UX)
    payment_instructions = None
    if farmer_profile and farmer_profile.virtual_account_number:
        payment_instructions = {
            "bank_name": farmer_profile.virtual_account_bank_name or "GTBank",
            "account_number": farmer_profile.virtual_account_number,
            "account_name": (
                farmer_profile.virtual_account_business_name or farmer_profile.business_name
            ),
            "amount": final_amount_naira,
            "reference": f"ORDER_{str(order.id)[:8]}",
            "note": "Use the hosted checkout for guaranteed escrow protection.",
        }

    return {
        "message": "Order created. Proceed to payment.",
        "order_id": str(order.id),
        "product_total": total_amount_naira,
        "delivery_fee": DELIVERY_FEE_NAIRA,
        "final_amount": final_amount_naira,
        # OTP shown once here — buyer must save it for delivery confirmation
        "otp": plain_otp,
        "otp_note": "Give this OTP to the dispatch rider only when you receive your order.",
        "payment_instructions": payment_instructions,
    }


def _release_escrow_to_farmer(order_id: UUID, db: Session) -> dict:
    """
    Internal helper to release escrow funds to farmer.
    Called after OTP verification or admin resolution.
    """
    from services.payout import release_funds_to_farmer
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    
    # Get first product to find farmer
    first_item = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
    if not first_item:
        raise HTTPException(404, "No order items found")
    
    product = db.query(Product).filter(Product.id == first_item.product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    
    farmer_profile = db.query(FarmerProfile).filter(
        FarmerProfile.user_id == product.farmer_id
    ).first()
    
    if not farmer_profile:
        raise HTTPException(404, "Farmer profile not found")
    
    if not farmer_profile.account_number:
        raise HTTPException(400, "Farmer has no bank account configured")
    
    amount_naira = order.total_amount_kobo / 100
    
    result = release_funds_to_farmer(
        farmer_account_number=farmer_profile.account_number,
        farmer_bank_code=farmer_profile.bank_code or "058",
        farmer_name=farmer_profile.business_name or "Farmer",
        amount_naira=amount_naira,
        order_id=str(order.id),
    )
    
    # Update order and payment status
    order.escrow_status = "released"
    order.status = "completed"
    
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.escrow_status = "released"
        payment.released_at = datetime.utcnow()
    
    farmer_profile.total_sales = float(farmer_profile.total_sales or 0) + amount_naira
    db.commit()
    
    return {
        "success": True,
        "amount_released": amount_naira,
        "transaction_reference": result.get("transaction_reference"),
    }


@router.post("/verify-otp")
def verify_otp(
    order_id: UUID,
    otp_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Buyer submits OTP to confirm delivery receipt.
    This triggers escrow release to the farmer.
    Only the buyer who owns the order can call this.
    """

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    if order.buyer_id != current_user.id:
        raise HTTPException(403, "Not your order")

    if order.delivery_status not in ["in_transit", "delivered", "assigned"]:
        raise HTTPException(400, "Order has not been dispatched yet")

    if order.is_otp_verified:
        raise HTTPException(400, "OTP already verified — delivery already confirmed")

    if not order.otp_hash:
        raise HTTPException(500, "No OTP on record for this order")

    if datetime.utcnow() > order.otp_expires_at:
        raise HTTPException(400, "OTP has expired")

    if not _verify_otp(otp_code.strip().upper(), order.otp_hash):
        raise HTTPException(400, "Incorrect OTP")

    # Mark delivery confirmed
    order.is_otp_verified = True
    order.delivery_status = "confirmed"
    order.confirmed_at = datetime.utcnow()
    order.status = "completed"
    db.commit()

    # Release escrow to farmer via Squad Transfer API
    try:
        release_result = _release_escrow_to_farmer(order_id=order.id, db=db)
        return {
            "message": "Delivery confirmed. Funds released to farmer.",
            "order_id": str(order.id),
            "escrow_status": order.escrow_status,
            "payout": release_result,
        }
    except Exception as e:
        logger.error(f"[ESCROW] OTP verified but payout failed for order {order.id}: {e}")
        # Don't fail the OTP confirm — flag for manual review
        return {
            "message": "Delivery confirmed. Payout is being processed.",
            "order_id": str(order.id),
            "warning": "Payout is queued — contact support if not received within 24h.",
        }


@router.get("/my-orders", response_model=list[OrderStatusResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = db.query(Order).filter(Order.buyer_id == current_user.id).all()
    return orders


@router.get("/farmer-orders", response_model=list[FarmerOrder])
def get_farmer_orders(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "farmer":
        raise HTTPException(403, "Only farmers can view their orders")
    
    orders = db.query(Order).join(OrderItem).join(Product).filter(
        Product.farmer_id == current_user.id
    ).distinct().all()
    
    result = []
    for order in orders:
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        buyer = db.query(User).filter(User.id == order.buyer_id).first()

        result.append({
            "order_id": order.id,
            "buyer_name": buyer.full_name if buyer else "Unknown",
            "buyer_phone": buyer.phone_number if buyer else "Unknown",
            "delivery_address": order.delivery_location,
            "delivery_fee": float(order.delivery_fee),
            "total_amount": float(order.total_amount),
            "status": order.status,
            "payment_status": order.payment_status,
            "delivery_status": order.delivery_status,
            "created_at": order.created_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else "Unknown",
                    "quantity": item.quantity,
                    "price": float(item.price),
                }
                for item in order_items
            ],
        })

    return result


@router.get("/{order_id}", response_model=OrderStatusResponse)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    is_buyer = order.buyer_id == current_user.id
    is_rider = order.dispatch_rider_id == current_user.id
    is_admin = current_user.role == "admin"

    if not (is_buyer or is_rider or is_admin):
        raise HTTPException(403, "Access denied")

    return order
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from uuid import UUID
from db.database import get_db
from db.model import Order, OrderItem, Product, User, FarmerProfile, Notification
from db.schemas import OrderCreate, OrderStatusResponse
from authentication.OAuth2 import get_current_user
from services.mapbox_service import calculate_delivery_fee, geocode_address

router = APIRouter(prefix="/orders", tags=["Orders"])


def generate_otp():
    return secrets.token_hex(3).upper()  # 6 hex characters


@router.post("/create")
def create_order(
    request: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in  ["buyer", "farmer"]:
        raise HTTPException(403, "Only buyers and farmers can create orders")

    total_amount = 0
    order_items = []
    farmer_location = None

    for item in order_items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.is_approved == True,
        ).first()

        if not product:
            raise HTTPException(404, f"Product {item.product_id} not found or not approved")

        if item.quantity > product.available_quantity:
            raise HTTPException(400, f"Insufficient quantity for {product.name}")

        farmer_profile = db.query(FarmerProfile).filter(
            FarmerProfile.user_id == product.farmer_id
        ).first()

        if not farmer_profile:
            raise HTTPException(400, "Farmer profile not found")

        if farmer_location and farmer_location != farmer_profile.location:
            raise HTTPException(400, "All items must be from the same location")

        farmer_location = farmer_profile.location
        total_amount += product.price * item.quantity
        order_items.append({"product": product, "quantity": item.quantity})

    buyer_address = request.buyer_address or request.delivery_location.value

    origin_coords = geocode_address(farmer_location)
    dest_coords = geocode_address(buyer_address)

    if origin_coords[0] and dest_coords[0]:
        origin_str = f"{origin_coords[0]},{origin_coords[1]}"
        dest_str = f"{dest_coords[0]},{dest_coords[1]}"
        fee_info = calculate_delivery_fee(origin_str, dest_str)
        delivery_fee = fee_info["delivery_fee"]
        distance_km = fee_info["distance_km"]
    else:
        if request.delivery_location.value == farmer_location:
            delivery_fee = 1000
        else:
            delivery_fee = 5000
        distance_km = None

    final_amount = total_amount + delivery_fee
    otp_code = generate_otp()

    order = Order(
        buyer_id=current_user.id,
        total_amount=final_amount,
        status="pending",
        payment_status="pending",
        otp_code=otp_code,
        otp_expires_at=datetime.utcnow() + timedelta(hours=48),
        delivery_status="pending",
        escrow_status="held",
        delivery_location=request.delivery_location,
        delivery_fee=delivery_fee,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    for item in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product"].id,
            quantity=item["quantity"],
            price=item["product"].price,
        )
        db.add(order_item)
        item["product"].available_quantity -= item["quantity"]


    return {
        "message": "Order created. Proceed to payment.",
        "order_id": str(order.id),
        "product_total": total_amount,
        "delivery_fee": delivery_fee,
        "distance_km": distance_km,
        "final_amount": final_amount,
        "otp": otp_code
    }


@router.get("/my-orders", response_model=list[OrderStatusResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = db.query(Order).filter(Order.buyer_id == current_user.id).all()
    return orders

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
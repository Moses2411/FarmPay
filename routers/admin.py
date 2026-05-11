from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from authentication.OAuth2 import get_current_user
from db.database import get_db
from db.model import User, UserRole, Order, Dispute, Payment, FarmerProfile, Product
from authentication.hashing import Hash
from db.schemas import DispatchRiderCreate, DisputeResolve, DisputeResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_current_admin(user=Depends(get_current_user)):
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


@router.post("/create-dispatch-rider")
def create_dispatch_rider(
    request: DispatchRiderCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(400, "Email already exists")

    new_rider = User(
        full_name=request.full_name,
        email=request.email,
        phone_number=request.phone_number,
        password=Hash.hash_password(request.password),
        role=UserRole.dispatch_rider,
        is_verified=True,
    )
    db.add(new_rider)
    db.commit()
    db.refresh(new_rider)  # Ensure we have the generated ID

    # Return rider details along with success message (maintains backward compatibility)
    return {
        "message": "Dispatch rider created successfully",
        "rider": {
            "id": str(new_rider.id),
            "full_name": new_rider.full_name,
            "email": new_rider.email,
            "phone_number": new_rider.phone_number,
            "is_verified": new_rider.is_verified,
            "created_at": new_rider.created_at.isoformat() if new_rider.created_at else None,
        }
    }


@router.put("/assign-rider/{order_id}/{rider_id}")
def assign_rider(
    order_id: UUID,
    rider_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    rider = db.query(User).filter(
        User.id == rider_id,
        User.role == UserRole.dispatch_rider,
    ).first()

    if not order:
        raise HTTPException(404, "Order not found")

    if not rider:
        raise HTTPException(404, "Dispatch rider not found")

    if order.payment_status != "paid":
        raise HTTPException(400, "Can only assign rider to paid orders")

    order.dispatch_rider_id = rider_id
    order.delivery_status = "assigned"
    order.assigned_at = datetime.utcnow()

    db.commit()

    # Return rider details along with existing response (maintains backward compatibility)
    return {
        "message": f"Rider {rider.full_name} assigned to order successfully",
        "order_id": str(order_id),
        "rider_id": str(rider_id),
        "rider": {
            "id": str(rider.id),
            "full_name": rider.full_name,
            "email": rider.email,
            "phone_number": rider.phone_number,
        }
    }


@router.get("/orders")
def get_all_orders(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return orders


@router.get("/disputes")
def get_all_disputes(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    disputes = db.query(Dispute).order_by(Dispute.created_at.desc()).all()
    return disputes


@router.put("/dispute/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: UUID,
    payload: DisputeResolve,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()

    if not dispute:
        raise HTTPException(404, "Dispute not found")

    if dispute.status != "pending":
        raise HTTPException(400, "Dispute already resolved")

    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()

    if payload.action == "refund_buyer":
        order.escrow_status = "refunded"
        order.status = "disputed"
        if payment:
            payment.escrow_status = "refunded"
            payment.refunded_at = datetime.utcnow()
        dispute.status = "verified"
        message = "Dispute resolved. Buyer will be refunded."

    elif payload.action == "release_farmer":
        order.escrow_status = "released"
        order.status = "completed"
        if payment:
            payment.escrow_status = "released"
            payment.released_at = datetime.utcnow()
        dispute.status = "rejected"
        message = "Dispute rejected. Payment released to farmer."

    else:
        raise HTTPException(
            400, "action must be 'refund_buyer' or 'release_farmer'"
        )

    dispute.resolved_at = datetime.utcnow()
    dispute.admin_id = admin.id
    db.commit()

    return {"message": message, "order_id": str(order.id)}


@router.post('/verify_user/{user_id}')  # Fixed: added missing slash
def verify_user(user_id: UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # FIXED: Changed from == to = (assignment, not comparison)
    user.is_verified = True
    db.commit()
    
    return {
        "message": "User verified successfully",
        "user_id": str(user.id),
        "email": user.email,
        "full_name": user.full_name
    }


@router.get("/", response_model=list[DisputeResponse])
def get_all_disputes_v2(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)):
    
    disputes = db.query(Dispute).all()
    return disputes


@router.patch("/approve/{dispute_id}")
def approve_dispute(
    dispute_id: str, 
    db: Session = Depends(get_db), 
    admin: User = Depends(get_current_admin)
):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()

    dispute.status = "verified"
    order.delivery_status = "disputed"

    if payment:
        payment.escrow_status = "refunded"
        payment.refunded_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Dispute approved, buyer refunded",
        "dispute_id": str(dispute.id),
        "order_id": str(order.id)
    }


@router.get("/all_users")
def get_all_users(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    users = db.query(User).filter(User.role == "buyer").count()
    return {"role": "buyer", "count": users}  # Changed to return dict for consistency


@router.get("/all_farmers")
def get_all_farmers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    farmers = db.query(User).filter(User.role == "farmer").count()
    return {"role": "farmer", "count": farmers}  # Changed to return dict for consistency


@router.get("/all_orders")
def get_all_orders_count(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    orders = db.query(Order).count()
    return {"total_orders": orders}  # Changed to return dict for consistency


@router.get("/all_payments")
def get_all_payments(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    payments = db.query(Payment).count()
    return {"total_payments": payments}  # Changed to return dict for consistency


@router.get("/all_farmer_profile")
def get_all_sellers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    farmer_profile = db.query(FarmerProfile).count()
    return {"total_farmer_profiles": farmer_profile}  # Changed to return dict for consistency


@router.get("/all_products")
def get_all_products(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    products = db.query(Product).count()
    return {"total_products": products}  # Changed to return dict for consistency


# NEW ENDPOINT: Get all dispatch riders (doesn't break anything existing)
@router.get("/dispatch-riders")
def get_all_dispatch_riders(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Get all dispatch riders with their details and order statistics"""
    riders = db.query(User).filter(User.role == "dispatch_rider").order_by(User.created_at.desc()).all()
    
    result = []
    for rider in riders:
        # Count orders assigned to this rider
        total_assigned = db.query(Order).filter(Order.dispatch_rider_id == rider.id).count()
        completed_deliveries = db.query(Order).filter(
            Order.dispatch_rider_id == rider.id,
            Order.delivery_status == "confirmed"
        ).count()
        pending_deliveries = db.query(Order).filter(
            Order.dispatch_rider_id == rider.id,
            Order.delivery_status.in_(["assigned", "in_transit"])
        ).count()
        
        result.append({
            "id": str(rider.id),
            "full_name": rider.full_name,
            "email": rider.email,
            "phone_number": rider.phone_number,
            "is_verified": rider.is_verified,
            "created_at": rider.created_at.isoformat() if rider.created_at else None,
            "statistics": {
                "total_assigned_orders": total_assigned,
                "completed_deliveries": completed_deliveries,
                "pending_deliveries": pending_deliveries,
            }
        })
    
    return result
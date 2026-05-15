from fastapi import Depends, HTTPException, status, APIRouter, Query
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from typing import Optional
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
    db.refresh(new_rider)

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


@router.get("/dispatch-riders")
def list_available_riders(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    assigned_rider_ids = db.query(Order.dispatch_rider_id).filter(
        Order.dispatch_rider_id.isnot(None),
        Order.delivery_status.in_(["assigned", "in_transit"]),
    ).distinct().all()
    assigned_rider_ids = [r[0] for r in assigned_rider_ids]

    if assigned_rider_ids:
        available_riders = db.query(User).filter(
            User.role == UserRole.dispatch_rider,
            User.id.notin_(assigned_rider_ids),
            User.is_verified == True,
        ).all()
    else:
        available_riders = db.query(User).filter(
            User.role == UserRole.dispatch_rider,
            User.is_verified == True,
        ).all()

    return [
        {
            "id": str(rider.id),
            "full_name": rider.full_name,
            "email": rider.email,
            "phone_number": rider.phone_number,
        }
        for rider in available_riders
    ]


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


@router.post('/verify_user/{user_id}')
def verify_user(user_id: UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
    return users


@router.get("/all_farmers")
def get_all_farmers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    farmers = db.query(User).filter(User.role == "farmer").count()
    return farmers


@router.get("/all_orders")
def get_all_orders_count(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    orders = db.query(Order).count()
    return orders


@router.get("/all_payments")
def get_all_payments_count(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    payments = db.query(Payment).count()
    return payments


@router.get("/all_farmer_profile")
def get_all_farmer_profiles_count(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    farmer_profile = db.query(FarmerProfile).count()
    return farmer_profile


@router.get("/all_products")
def get_all_products_count(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    products = db.query(Product).count()
    return products

@router.get("/users/details")
def get_users_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    role: Optional[str] = None,
):
    skip = (page - 1) * per_page
    
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(per_page).all()
    
    return {
        "users": [
            {
                "id": str(u.id),
                "full_name": u.full_name,
                "email": u.email,
                "phone_number": u.phone_number,
                "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
                "is_verified": u.is_verified,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
    }

@router.get("/products/details")
def get_products_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    approved: Optional[bool] = None,
):
    skip = (page - 1) * per_page
    
    query = db.query(Product)
    if approved is not None:
        query = query.filter(Product.is_approved == approved)
    
    total = query.count()
    products = query.order_by(Product.created_at.desc()).offset(skip).limit(per_page).all()
    
    # Get farmer names efficiently
    farmer_ids = list(set([p.farmer_id for p in products]))
    farmers = db.query(User).filter(User.id.in_(farmer_ids)).all()
    farmer_map = {str(f.id): f for f in farmers}
    
    return {
        "products": [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "available_quantity": p.available_quantity,
                "unit": p.unit,
                "scan_status": p.scan_status,
                "is_approved": p.is_approved,
                "farmer": {
                    "id": str(p.farmer_id),
                    "full_name": farmer_map.get(str(p.farmer_id)).full_name if p.farmer_id in farmer_map else None,
                    "email": farmer_map.get(str(p.farmer_id)).email if p.farmer_id in farmer_map else None,
                },
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
    }


@router.get("/orders/details")
def get_orders_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
):
    """Get full order details with pagination and filtering"""
    skip = (page - 1) * per_page
    
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(per_page).all()
    
    return {
        "orders": [
            {
                "id": str(o.id),
                "buyer_id": str(o.buyer_id),
                "total_amount": o.total_amount,
                "status": o.status,
                "payment_status": o.payment_status,
                "delivery_status": o.delivery_status,
                "escrow_status": o.escrow_status,
                "delivery_location": o.delivery_location,
                "delivery_fee": o.delivery_fee,
                "dispatch_rider_id": str(o.dispatch_rider_id) if o.dispatch_rider_id else None,
                "is_otp_verified": o.is_otp_verified,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "confirmed_at": o.confirmed_at.isoformat() if o.confirmed_at else None,
            }
            for o in orders
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
    }


@router.get("/payments/details")
def get_payments_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
):
    """Get full payment details with pagination"""
    skip = (page - 1) * per_page
    
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status)
    
    total = query.count()
    payments = query.order_by(Payment.paid_at.desc()).offset(skip).limit(per_page).all()
    
    return {
        "payments": [
            {
                "id": str(p.id),
                "order_id": str(p.order_id),
                "payment_reference": p.payment_reference,
                "payment_gateway": p.payment_gateway,
                "amount": p.amount,
                "status": p.status,
                "escrow_status": p.escrow_status,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "released_at": p.released_at.isoformat() if p.released_at else None,
                "refunded_at": p.refunded_at.isoformat() if p.refunded_at else None,
            }
            for p in payments
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
    }


@router.get("/farmer-profiles/details")
def get_farmer_profiles_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
):
    skip = (page - 1) * per_page
    total = db.query(FarmerProfile).count()
    profiles = db.query(FarmerProfile).order_by(FarmerProfile.created_at.desc()).offset(skip).limit(per_page).all()
    
    user_ids = [p.user_id for p in profiles]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {str(u.id): u for u in users}
    
    return {
        "farmer_profiles": [
            {
                "id": str(p.id),
                "user_id": str(p.user_id),
                "full_name": user_map.get(str(p.user_id)).full_name if p.user_id in user_map else None,
                "email": user_map.get(str(p.user_id)).email if p.user_id in user_map else None,
                "business_name": p.business_name,
                "location": p.location,
                "nin": p.nin,
                "bank_name": p.bank_name,
                "account_number": p.account_number,
                "total_sales": p.total_sales,
                "rating": p.rating,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in profiles
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
    }


@router.get("/dispatch-riders/details")
def get_dispatch_riders_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
):
    """Get full dispatch rider details with statistics"""
    skip = (page - 1) * per_page
    
    query = db.query(User).filter(User.role == UserRole.dispatch_rider)
    total = query.count()
    riders = query.order_by(User.created_at.desc()).offset(skip).limit(per_page).all()
    
    result = []
    for rider in riders:
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
    
    return {
        "dispatch_riders": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
    }


@router.get("/disputes/details")
def get_disputes_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
):
    """Get full dispute details with pagination"""
    skip = (page - 1) * per_page
    
    query = db.query(Dispute)
    if status:
        query = query.filter(Dispute.status == status)
    
    total = query.count()
    disputes = query.order_by(Dispute.created_at.desc()).offset(skip).limit(per_page).all()
    
    return {
        "disputes": [
            {
                "id": str(d.id),
                "order_id": str(d.order_id),
                "buyer_id": str(d.buyer_id),
                "reason": d.reason,
                "status": d.status,
                "admin_id": str(d.admin_id) if d.admin_id else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "resolved_at": d.resolved_at.isoformat() if d.resolved_at else None,
            }
            for d in disputes
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
    }
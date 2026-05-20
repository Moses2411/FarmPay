import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from authentication.OAuth2 import get_current_user
from authentication.hashing import Hash
from db.database import get_db
from db.model import (
    Dispute, DisputeImage, FarmerProfile, Notification, Order, OrderItem,
    Payment, Product, ProductImage, ScanResult, User, UserRole
)
from db.schemas import DispatchRiderCreate, DisputeResolve, DisputeResponse, OrderAssign

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Auth guard ────────────────────────────────────────────────────────────────

def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


# ── Dispatch riders ───────────────────────────────────────────────────────────

@router.post("/create-dispatch-rider")
def create_dispatch_rider(
    request: DispatchRiderCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(400, "Email already exists")

    rider = User(
        full_name=request.full_name,
        email=request.email,
        phone_number=request.phone_number,
        password=Hash.hash_password(request.password),
        role=UserRole.dispatch_rider,
        is_verified=True,
    )
    db.add(rider)
    db.commit()
    db.refresh(rider)

    return {
        "message": "Dispatch rider created successfully",
        "rider": {
            "id": str(rider.id),
            "full_name": rider.full_name,
            "email": rider.email,
            "phone_number": rider.phone_number,
            "is_verified": rider.is_verified,
            "created_at": rider.created_at.isoformat() if rider.created_at else None,
        },
    }


@router.get("/dispatch-riders")
def list_available_riders(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    busy_ids = [
        r[0]
        for r in db.query(Order.dispatch_rider_id)
        .filter(
            Order.dispatch_rider_id.isnot(None),
            Order.delivery_status.in_(["assigned", "in_transit"]),
        )
        .distinct()
        .all()
    ]

    query = db.query(User).filter(
        User.role == UserRole.dispatch_rider,
        User.is_verified == True,
    )
    if busy_ids:
        query = query.filter(User.id.notin_(busy_ids))

    return [
        {
            "id": str(r.id),
            "full_name": r.full_name,
            "email": r.email,
            "phone_number": r.phone_number,
        }
        for r in query.all()
    ]


@router.put("/assign-rider/{order_id}/{rider_id}")
def assign_rider(
    order_id: UUID,
    rider_id: UUID,
    rider_status: str = "available",
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    if order.payment_status != "paid":
        raise HTTPException(400, "Can only assign rider to paid orders")

    if order.dispatch_rider_id:
        raise HTTPException(400, "Order already has a rider assigned")

    rider = db.query(User).filter(
        User.id == rider_id,
        User.role == UserRole.dispatch_rider,
    ).first()
    if not rider:
        raise HTTPException(404, "Dispatch rider not found")

    order.dispatch_rider_id = rider_id
    order.delivery_status = "assigned"
    order.assigned_at = datetime.utcnow()

    if rider_status == "busy":
        rider.is_available = False
    elif rider_status == "available":
        rider.is_available = True

    db.commit()

    return {
        "message": f"Rider {rider.full_name} assigned to order {str(order_id)[:8]}",
        "rider_status": "busy" if not rider.is_available else "available",
        "order_id": str(order_id),
        "rider": {
            "id": str(rider.id),
            "full_name": rider.full_name,
            "email": rider.email,
            "phone_number": rider.phone_number,
        },
    }


# ── Disputes ──────────────────────────────────────────────────────────────────

@router.get("/disputes")
def get_all_disputes(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    dispute_status: Optional[str] = None,
):
    """Paginated list of disputes with optional status filter."""
    skip = (page - 1) * per_page
    query = db.query(Dispute)
    if dispute_status:
        query = query.filter(Dispute.status == dispute_status)

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
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
    }


@router.put("/dispute/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: UUID,
    payload: DisputeResolve,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Resolve a dispute.
    - "refund_buyer"   → funds stay in Squad wallet, update records as refunded.
                         In production: call Squad refund API here if needed.
    - "release_farmer" → calls Transfer API to move money to farmer's bank.
    - "auto"           → automatically compares dispute scan with original farmer scan:
                         - If NEW disease/insect detected → refund buyer
                         - Otherwise → release to farmer
    Both actions update DB state and send notifications.
    """
    from routers.payment import _release_escrow_to_farmer  # avoid circular import

    if payload.action not in ("refund_buyer", "release_farmer", "auto"):
        raise HTTPException(400, "action must be 'refund_buyer', 'release_farmer', or 'auto'")

    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "Dispute not found")

    if dispute.status != "pending":
        raise HTTPException(400, "Dispute already resolved")

    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()

    dispute.resolved_at = datetime.utcnow()
    dispute.admin_id = admin.id

    final_action = payload.action

    if payload.action == "auto":
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        original_diseases = set()
        for item in order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product_images = db.query(ProductImage).filter(
                    ProductImage.product_id == product.id
                ).all()
                for img in product_images:
                    scan = db.query(ScanResult).filter(ScanResult.image_id == img.id).first()
                    if scan and scan.disease_name:
                        original_diseases.add(scan.disease_name.lower())

        dispute_images = db.query(DisputeImage).filter(DisputeImage.dispute_id == dispute.id).all()
        new_issues_found = False
        for dimg in dispute_images:
            if dimg.disease_detected and dimg.disease_name:
                disease_lower = dimg.disease_name.lower()
                if disease_lower not in original_diseases:
                    new_issues_found = True
                    break

        final_action = "refund_buyer" if new_issues_found else "release_farmer"
        logger.info(f"[DISPUTE] Auto-resolve: original_diseases={original_diseases}, new_issues={new_issues_found} -> {final_action}")

    if final_action == "refund_buyer":
        order.escrow_status = "refunded"
        order.status = "disputed"
        if payment:
            payment.escrow_status = "refunded"
            payment.refunded_at = datetime.utcnow()
        dispute.status = "verified"

        db.add(Notification(
            user_id=order.buyer_id,
            title="Dispute Resolved — Refund Approved",
            message="Your dispute was upheld. A refund will be processed to your original payment method.",
        ))

        db.commit()
        return {
            "message": "Dispute resolved. Buyer refund approved.",
            "order_id": str(order.id),
            "decision": "auto" if payload.action == "auto" else "manual",
            "reason": "New disease/insect detected not present at farmer upload" if payload.action == "auto" else None,
        }

    dispute.status = "rejected"
    db.commit()

    try:
        release_result = _release_escrow_to_farmer(order_id=order.id, db=db)
        return {
            "message": "Dispute rejected. Payment released to farmer.",
            "order_id": str(order.id),
            "payout": release_result,
            "decision": "auto" if payload.action == "auto" else "manual",
            "reason": "No new issues detected compared to original scan" if payload.action == "auto" else None,
        }
    except Exception as e:
        logger.error(f"[ADMIN] Payout failed during dispute resolution: {e}")
        raise HTTPException(500, f"Dispute resolved but payout failed: {str(e)}")


# ── User management ───────────────────────────────────────────────────────────

@router.post("/verify_user/{user_id}")
def verify_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_verified = True
    db.commit()
    return {"message": "User verified", "user_id": str(user.id), "email": user.email}


# ── Dashboard counts ──────────────────────────────────────────────────────────

@router.get("/dashboard/counts")
def get_dashboard_counts(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Single endpoint for all admin dashboard counts."""
    return {
        "buyers": db.query(User).filter(User.role == "buyer").count(),
        "farmers": db.query(User).filter(User.role == "farmer").count(),
        "dispatch_riders": db.query(User).filter(User.role == UserRole.dispatch_rider).count(),
        "orders": db.query(Order).count(),
        "payments": db.query(Payment).count(),
        "farmer_profiles": db.query(FarmerProfile).count(),
        "products": db.query(Product).count(),
        "pending_disputes": db.query(Dispute).filter(Dispute.status == "pending").count(),
    }


# ── Detail list endpoints (paginated) ────────────────────────────────────────

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
                "role": u.role.value if hasattr(u.role, "value") else str(u.role),
                "is_verified": u.is_verified,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
    }


@router.get("/orders/details")
def get_orders_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    order_status: Optional[str] = None,
    payment_status: Optional[str] = None,
):
    skip = (page - 1) * per_page
    query = db.query(Order)
    if order_status:
        query = query.filter(Order.status == order_status)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(per_page).all()

    return {
        "orders": [
            {
                "id": str(o.id),
                "buyer_id": str(o.buyer_id),
                "total_amount": float(o.total_amount) if o.total_amount else None,
                "status": o.status,
                "payment_status": o.payment_status,
                "delivery_status": o.delivery_status,
                "escrow_status": o.escrow_status,
                "delivery_location": o.delivery_location,
                "delivery_fee": float(o.delivery_fee) if o.delivery_fee else 0,
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
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
    }


@router.get("/payments/details")
def get_payments_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
    payment_status: Optional[str] = None,
):
    skip = (page - 1) * per_page
    query = db.query(Payment)
    if payment_status:
        query = query.filter(Payment.status == payment_status)

    total = query.count()
    payments = query.order_by(Payment.paid_at.desc()).offset(skip).limit(per_page).all()

    return {
        "payments": [
            {
                "id": str(p.id),
                "order_id": str(p.order_id),
                "payment_reference": p.payment_reference,
                "payment_gateway": p.payment_gateway,
                "amount": float(p.amount) if p.amount else None,
                "status": p.status,
                "escrow_status": p.escrow_status,
                "payout_status": p.payout_status,
                "payout_reference": p.payout_reference,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "released_at": p.released_at.isoformat() if p.released_at else None,
                "refunded_at": p.refunded_at.isoformat() if p.refunded_at else None,
            }
            for p in payments
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
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
    profiles = (
        db.query(FarmerProfile)
        .order_by(FarmerProfile.created_at.desc())
        .offset(skip)
        .limit(per_page)
        .all()
    )

    user_map = {
        str(u.id): u
        for u in db.query(User).filter(
            User.id.in_([p.user_id for p in profiles])
        ).all()
    }

    return {
        "farmer_profiles": [
            {
                "id": str(p.id),
                "user_id": str(p.user_id),
                "full_name": user_map.get(str(p.user_id), User()).full_name,
                "email": user_map.get(str(p.user_id), User()).email,
                "business_name": p.business_name,
                "location": p.location,
                "bank_name": p.bank_name,
                "account_number": p.account_number,
                "total_sales": float(p.total_sales) if p.total_sales else 0,
                "escrow_balance": float(p.escrow_balance) if p.escrow_balance else 0,
                "rating": float(p.rating) if p.rating else 0,
                "bvn_verified": p.bvn_verified,
                "virtual_account_number": p.virtual_account_number,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in profiles
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
    }


@router.get("/dispatch-riders/details")
def get_dispatch_riders_details(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = 1,
    per_page: int = 20,
):
    skip = (page - 1) * per_page
    query = db.query(User).filter(User.role == UserRole.dispatch_rider)
    total = query.count()
    riders = query.order_by(User.created_at.desc()).offset(skip).limit(per_page).all()

    result = []
    for rider in riders:
        total_assigned = db.query(Order).filter(Order.dispatch_rider_id == rider.id).count()
        completed = db.query(Order).filter(
            Order.dispatch_rider_id == rider.id,
            Order.delivery_status == "confirmed",
        ).count()
        pending = db.query(Order).filter(
            Order.dispatch_rider_id == rider.id,
            Order.delivery_status.in_(["assigned", "in_transit"]),
        ).count()

        result.append({
            "id": str(rider.id),
            "full_name": rider.full_name,
            "email": rider.email,
            "phone_number": rider.phone_number,
            "is_verified": rider.is_verified,
            "created_at": rider.created_at.isoformat() if rider.created_at else None,
            "statistics": {
                "total_assigned": total_assigned,
                "completed_deliveries": completed,
                "pending_deliveries": pending,
            },
        })

    return {
        "dispatch_riders": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
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

    farmer_map = {
        str(f.id): f
        for f in db.query(User).filter(
            User.id.in_([p.farmer_id for p in products])
        ).all()
    }

    return {
        "products": [
            {
                "id": str(p.id),
                "name": p.name,
                "price": float(p.price) if p.price else 0,
                "available_quantity": p.available_quantity,
                "unit": p.unit,
                "scan_status": p.scan_status,
                "is_approved": p.is_approved,
                "farmer": {
                    "id": str(p.farmer_id),
                    "full_name": farmer_map.get(str(p.farmer_id), User()).full_name,
                    "email": farmer_map.get(str(p.farmer_id), User()).email,
                },
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 1,
    }
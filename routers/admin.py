from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from datetime import datetime
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

    return {"message": "Dispatch rider created successfully"}


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

@router.post('/verify_user{user_id}')
def verify_user(user_id: UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code = 404, detail = "user not found")

    user.is_verified = True
    db.commit()
    return {"user verified"}


@router.get("/", response_model=list[DisputeResponse])
def get_all_disputes(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)):

    disputes = db.query(Dispute).all()
    return disputes

@router.patch("/approve/{dispute_id}")
def approve_dispute(dispute_id: str, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)
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

    return {"message": "Dispute approved, buyer refunded"}


@router.get("/all_users")
def get_all_users(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    users = db.query(User).filter(User.role == "buyer").count()
    return users

@router.get("/all_farmers")
def get_all_farmers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    farmers = db.query(User).filter(User.role == "farmer").count()
    return farmers
    
@router.get("/all_orders")
def get_all_orders(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    orders = db.query(Order).count()
    return orders

@router.get("/all_payments")
def get_all_payments(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    payments = db.query(Payment).count()
    return payments

@router.get("/all_farmer_profile")
def get_all_sellers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    farmer_profile = db.query(FarmerProfile).count()
    return farmer_profile

@router.get("/all_products")
def get_all_products(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    products = db.query(Product).count()
    return products

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Review, Order, OrderItem, Product, User
from authentication.OAuth2 import get_current_user
from db.schemas import CreateReviewRequest, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=ReviewResponse)
def create_review(
    request: CreateReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Only buyers can review")

    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    order_item = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            OrderItem.product_id == request.product_id,
            Order.buyer_id == current_user.id,
            Order.delivery_status == "confirmed"
        )
        .first()
    )

    if not order_item:
        raise HTTPException(
            status_code=400,
            detail="You can only review products you have received"
        )

    existing = db.query(Review).filter(
        Review.product_id == request.product_id,
        Review.buyer_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this product")

    review = Review(
        product_id=request.product_id,
        buyer_id=current_user.id,
        rating=request.rating,
        comment=request.comment
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review

@router.get("/product/{product_id}", response_model=list[ReviewResponse])
def get_product_reviews(product_id: str, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter( Review.product_id == product_id).all()
    return reviews
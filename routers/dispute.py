from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import shutil, os, uuid

from db.database import get_db
from db.schemas import CreateDisputeResponse
from db.model import Dispute, DisputeImage, Order, User, Payment
from authentication.OAuth2 import get_current_user
from services.disease_detector import detect_disease

router = APIRouter(prefix="/disputes", tags=["Disputes"])

UPLOAD_DIR = "uploads/disputes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/create", response_model=CreateDisputeResponse)
def create_dispute(
    order_id: str = Form(...),
    reason: str = Form(...),
    images: List[UploadFile] = File(...),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Only buyers can create disputes")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")

    if order.delivery_status != "confirmed":
        raise HTTPException(status_code=400, detail="Order not yet delivered")

    existing = db.query(Dispute).filter(Dispute.order_id == order.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dispute already exists")

    dispute = Dispute(
        order_id=order.id,
        buyer_id=current_user.id,
        reason=reason,
        status="pending"
    )

    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    for image in images:
        file_name = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
        file_path = os.path.join(UPLOAD_DIR, file_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        result = detect_disease(file_path)

        dispute_image = DisputeImage(
            dispute_id=dispute.id,
            image_url=file_path,
            disease_detected=result.get("disease_detected"),
            disease_name=result.get("disease_name")
        )

        db.add(dispute_image)

    order.delivery_status = "disputed"

    db.commit()

    return {
        "message": "Dispute submitted successfully",
        "dispute_id": dispute.id
    }
"""
routers/disputes.py
Buyer raises a dispute with image evidence after delivery.
Admin resolves via /admin/dispute/{id}/resolve.
"""

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List

from authentication.OAuth2 import get_current_user
from db.database import get_db
from db.model import Dispute, DisputeImage, Order, User
from db.schemas import CreateDisputeResponse
from services.disease_detector import analyze_image

router = APIRouter(prefix="/disputes", tags=["Disputes"])

UPLOAD_DIR = "uploads/disputes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/create", response_model=CreateDisputeResponse)
def create_dispute(
    order_id: str = Form(...),
    reason: str = Form(...),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "buyer":
        raise HTTPException(403, "Only buyers can raise disputes")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    if order.buyer_id != current_user.id:
        raise HTTPException(403, "Not your order")

    if order.delivery_status not in ["in_transit", "delivered", "assigned"]:
        raise HTTPException(400, "Order has not been dispatched yet")

    if db.query(Dispute).filter(Dispute.order_id == order.id).first():
        raise HTTPException(400, "A dispute already exists for this order")

    dispute = Dispute(
        order_id=order.id,
        buyer_id=current_user.id,
        reason=reason,
        status="pending",
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    for image in images:
        ext = image.filename.split(".")[-1] if image.filename else "jpg"
        file_name = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        result = analyze_image(file_path)

        db.add(DisputeImage(
            dispute_id=dispute.id,
            image_url=file_path,
            disease_detected=not result.get("is_healthy", True),
            disease_name=result.get("name"),
        ))

    order.delivery_status = "disputed"
    db.commit()

    return {"message": "Dispute submitted successfully", "dispute_id": dispute.id}
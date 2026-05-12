from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import uuid
from uuid import UUID

from db.database import get_db
from db.model import Product, ProductImage, ScanResult, User, FarmerProfile
from db.schemas import ProductResponse, ProductImageSchema, ProductImageScanResult
from authentication.OAuth2 import get_current_user
from services.disease_detector import analyze_image, get_supported

router = APIRouter(prefix="/products", tags=["Products"])

UPLOAD_DIR = "/var/data/uploads" if os.path.exists("/var/data") else "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def _save_image(image: UploadFile, upload_dir: str):
    if not image.filename:
        raise HTTPException(400, "Invalid filename")

    file_ext = image.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type not allowed. Use: {ALLOWED_EXTENSIONS}")

    image.file.seek(0, 2)
    size = image.file.tell()
    image.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Max 5MB")

    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(upload_dir, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return file_path, file_name


@router.post("/upload")
def upload_product(
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    available_quantity: int = Form(...),
    unit: str = Form(...),
    crop_type: str = Form("auto"),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "farmer":
        raise HTTPException(403, "Only farmers can upload products")

    valid = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
    if not valid:
        raise HTTPException(403, "You dont yet have a market place profile")

    product = Product(
        farmer_id=current_user.id,
        name=name,
        description=description,
        price=price,
        available_quantity=available_quantity,
        unit=unit,
        scan_status="pending",
        is_approved=False,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    try:
        file_path, file_name = _save_image(image, UPLOAD_DIR)
    except HTTPException:
        db.delete(product)
        db.commit()
        raise

    product_image = ProductImage(
        product_id=product.id,
        image_url=f"/uploads/{file_name}",
    )
    db.add(product_image)
    db.commit()
    db.refresh(product_image)

    result = analyze_image(file_path, crop_type)

    target_crop = name.lower().strip()
    detected_crop = result.get("detected_crop", "").lower().strip()
    provided_crop = crop_type.lower().strip() if crop_type and crop_type != "auto" else None

    if not (provided_crop and provided_crop != "auto"):
        if detected_crop and detected_crop != "unknown" and detected_crop != target_crop:
            os.remove(file_path)
            db.delete(product_image)
            db.delete(product)
            db.commit()
            raise HTTPException(
                400,
                f"Image mismatch: uploaded '{target_crop}' but detected '{detected_crop}'",
            )

    scan = ScanResult(
        image_id=product_image.id,
        disease_detected=not result["is_healthy"],
        disease_name=result["name"],
        status="scanned",
    )
    db.add(scan)

    product.scan_status = "scanned"
    product.is_approved = True
    db.commit()
    db.refresh(product)

    return {
        "message": "Product uploaded successfully",
        "scan_status": product.scan_status,
        "is_approved": product.is_approved,
        "product_id": str(product.id),
        "image_url": product_image.image_url,
        "crop_type": result.get("crop_type"),
        "issue_type": result.get("issue_type"),
        "name": result.get("name"),
        "treatment": result.get("treatment"),
    }


@router.get("/all", response_model=List[ProductResponse])
def get_verified_products(db: Session = Depends(get_db)):
    return db.query(Product).filter(
        Product.scan_status == "scanned",
        Product.is_approved == True,
    ).all()


@router.get("/specific/{product_id}")
def get_single_product(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_approved == True,
    ).first()
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    if product.farmer_id != current_user.id:
        raise HTTPException(403, "Not authorized")
    if product.order_items:
        raise HTTPException(400, "Ordered item cannot be deleted")

    for img in product.images:
        img_path = os.path.join(UPLOAD_DIR, os.path.basename(img.image_url))
        if os.path.exists(img_path):
            os.remove(img_path)

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


@router.get("/my-products", response_model=List[ProductResponse])
def get_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Product).filter(Product.farmer_id == current_user.id).all()
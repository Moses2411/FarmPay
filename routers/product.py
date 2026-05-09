from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import uuid
from uuid import UUID
from core.config import settings

from db.database import get_db
from db.model import Product, ProductImage, ScanResult, User, FarmerProfile
from db.schemas import ProductResponse
from authentication.OAuth2 import get_current_user
from services.disease_detector import detect_disease

router = APIRouter(prefix="/products", tags=["Products"])

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
def upload_product(
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    available_quantity: int = Form(...),
    unit: str = Form(...),
    image: UploadFile = File(..., description="Upload product image"),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only farmers can upload
    if current_user.role != "farmer":
        raise HTTPException(status_code=403, detail="Only farmers can upload products")

    valid = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
    if not valid:
        raise HTTPException(status_code = 403, detail = "You dont yet have a market place profile")

    # Create product first (pending)
    product = Product(
        farmer_id=current_user.id,
        name=name,
        description=description,
        price=price,
        available_quantity=available_quantity,
        unit=unit,
        scan_status="pending",
        is_approved=False
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    # Process single image
    file_ext = image.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Save image locally
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Save image record
    product_image = ProductImage(
        product_id=product.id,
        image_url=file_path
    )
    db.add(product_image)
    db.commit()
    db.refresh(product_image)

    # Run disease detection
    result = detect_disease(file_path)

    # Save scan result
    scan = ScanResult(
        image_id=product_image.id,
        disease_detected=result["disease_detected"],
        disease_name=result["disease_name"],
        status=result["status"]
    )
    db.add(scan)
    db.commit()

    # Final decision based on single image
    if result["disease_detected"]:
        product.scan_status = "rejected"
        product.is_approved = False
    else:
        product.scan_status = "approved"
        product.is_approved = True

    db.commit()
    db.refresh(product)

    return {
        "message": "Product uploaded successfully",
        "scan_status": product.scan_status,
        "is_approved": product.is_approved,
        "product_id": str(product.id)
    }

@router.get('/all', response_model= List[ProductResponse])
def get_verified_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_approved == True, Product.scan_status == "approved").all()
    return products

@router.get('/specific{product_id}')
def get_single_product(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.is_approved == "true").first()
    if not product:
        raise HTTPException(status_code = 404, detail = 'Product not found')
    return product

@router.delete("/{product_id}")
def delete_product(product_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(404, "Product not found")

    if product.farmer_id != current_user.id:
        raise HTTPException(403, "Not authorized to delete this product")
    
    if product.order_items:
        raise HTTPException(status_code = 400, detail = "odered item cannot be deleted")

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}

@router.get("/my-products", response_model = List[ProductResponse] )
def get_my_products(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    products = db.query(Product).filter(Product.farmer_id == current_user.id).all()
    return products
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    farmer = "farmer"
    buyer = "buyer"
    admin = "admin"
    dispatch_rider = "dispatch_rider"


# ── User ──────────────────────────────────────────────────


# ── User ──────────────────────────────────────────────────

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: UserRole
    phone_number: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Farmer profile ────────────────────────────────────────

class FarmerProfileBase(BaseModel):
    business_name: str
    location: str
    nin: int
    bank_name: str
    account_number: str


class FarmerProfileResponse(FarmerProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    total_sales: float
    rating: float

    class Config:
        from_attributes = True


class FarmerProfileSchema(BaseModel):
    id: UUID
    business_name: Optional[str] = None
    location: str

    class Config:
        from_attributes = True


# ── Product ───────────────────────────────────────────────

class ProductImageScanResult(BaseModel):
    disease_detected: bool
    disease_name: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class ProductImageSchema(BaseModel):
    image_url: str
    scan_result: Optional[ProductImageScanResult] = None

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    price: float
    available_quantity: int
    unit: str
    scan_status: str
    is_approved: bool
    created_at: datetime
    farmer_profile: Optional[FarmerProfileSchema] = None
    images: List[ProductImageSchema] = []

    class Config:
        from_attributes = True


# ── Order ─────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    delivery_address: str
    buyer_address: Optional[str] = None

class OrderResponse(BaseModel):
    id: UUID
    total_amount: float
    delivery_status: str
    escrow_status: str
    payment_status: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderStatusResponse(BaseModel):
    id: UUID
    status: str
    payment_status: str
    delivery_status: str
    escrow_status: str
    total_amount: float
    delivery_fee: float
    delivery_location: str
    dispatch_rider_id: Optional[UUID] = None
    is_otp_verified: bool
    otp_code: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Payment ───────────────────────────────────────────────

class PaymentVerifyRequest(BaseModel):
    transaction_ref: str


class PaymentResponse(BaseModel):
    order_id: UUID
    payment_reference: str
    amount: float
    status: str
    escrow_status: str

    class Config:
        from_attributes = True


# ── OTP ───────────────────────────────────────────────────

class OTPVerifyRequest(BaseModel):
    order_id: UUID
    otp_code: str


# ── Dispute ───────────────────────────────────────────────

class DisputeCreate(BaseModel):
    order_id: UUID
    reason: str


class DisputeResolve(BaseModel):
    action: str  # "refund_buyer" or "release_farmer"

class CreateDisputeResponse(BaseModel):
    message: str
    dispute_id: UUID

    class Config:
        from_attributes = True


class DisputeImageResponse(BaseModel):
    image_url: str
    disease_detected: Optional[bool]
    disease_name: Optional[str]

    class Config:
        from_attributes = True


class DisputeResponse(BaseModel):
    id: UUID
    order_id: UUID
    reason: Optional[str]
    status: str
    images: List[DisputeImageResponse]

    class Config:
        from_attributes = True


# ── Admin ─────────────────────────────────────────────────

class DispatchRiderCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: str

# ── Review ─────────────────────────────────────────────────

class CreateReviewRequest(BaseModel):
    product_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: UUID
    product_id: UUID
    rating: int
    comment: Optional[str]

    class Config:
        from_attributes = True


# ── Squad Payment ───────────────────────────────────────────

class SquadInitiateRequest(BaseModel):
    order_id: UUID
    payment_gateway: str = "squad"


class SquadInitiateResponse(BaseModel):
    transaction_ref: str
    checkout_url: str
    transaction_amount: int
    authorized_channels: List[str]
    currency: str
    merchant_id: str
    order_id: str

    class Config:
        from_attributes = True


class SquadWebhookPayload(BaseModel):
    Event: str
    TransactionRef: str
    Body: dict
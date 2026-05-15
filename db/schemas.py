from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum


def kobo_to_naira(kobo: int) -> float:
    """Convert kobo to naira (e.g., 10000 -> 100.00)"""
    return round(kobo / 100, 2)


def naira_to_kobo(naira: float) -> int:
    """Convert naira to kobo (e.g., 100.00 -> 10000)"""
    return int(naira * 100)


class UserRole(str, Enum):
    farmer = "farmer"
    buyer = "buyer"
    admin = "admin"
    dispatch_rider = "dispatch_rider"


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


class FarmerProfileBase(BaseModel):
    business_name: str
    location: str
    nin: int
    bvn: str = Field(..., min_length=11, max_length=11, description="11-digit BVN")
    bank_name: str
    account_number: str


class FarmerProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_name: Optional[str] = None
    location: str
    nin: int
    bank_name: str
    account_number: str
    created_at: datetime
    total_sales: float
    rating: float
    virtual_account_number: Optional[str] = None
    virtual_account_bank_name: Optional[str] = None
    escrow_balance: float = 0.0

    class Config:
        from_attributes = True


class FarmerProfileSchema(BaseModel):
    id: UUID
    business_name: Optional[str] = None
    location: str

    class Config:
        from_attributes = True


class ProductImageScanResult(BaseModel):
    disease_detected: bool
    disease_name: Optional[str] = None
    status: str
    confidence: float = 0.0

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
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FarmerOrderItem(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int
    price: float


class FarmerOrder(BaseModel):
    order_id: UUID
    buyer_name: str
    buyer_phone: str
    delivery_address: str
    delivery_fee: float
    total_amount: float
    status: str
    payment_status: str
    delivery_status: str
    created_at: datetime
    items: List[FarmerOrderItem] = []

    class Config:
        from_attributes = True


class PaymentVerifyRequest(BaseModel):
    transaction_ref: str


class PaymentInitiateResponse(BaseModel):
    checkout_url: str
    transaction_ref: str
    amount: float
    order_id: str


class PaymentVerifyResponse(BaseModel):
    message: str
    order_id: str
    amount: float
    escrow_status: str


class PaymentResponse(BaseModel):
    order_id: UUID
    payment_reference: str
    amount: float
    status: str
    escrow_status: str

    class Config:
        from_attributes = True

class OTPVerifyRequest(BaseModel):
    order_id: UUID
    otp_code: str


class OTPVerifyResponse(BaseModel):
    message: str
    order_id: str
    delivery_status: str
    escrow_status: str


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
    images: List[DisputeImageResponse] = []
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DispatchRiderCreate(BaseModel):
    full_name: str
    email: str
    password: str
    phone_number: str


class DispatchRiderResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone_number: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EscrowSummary(BaseModel):
    """Escrow summary for admin dashboard"""
    total_held_naira: float = 0.0
    total_released_naira: float = 0.0
    total_refunded_naira: float = 0.0
    held_orders_count: int = 0
    released_orders_count: int = 0
    refunded_orders_count: int = 0


class EscrowReleaseResponse(BaseModel):
    """Response for manual escrow release"""
    message: str
    order_id: UUID
    amount_released: float
    payout_reference: str
    payout_status: str


class CreateReviewRequest(BaseModel):
    product_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: UUID
    product_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
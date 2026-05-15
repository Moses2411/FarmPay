import enum
import uuid
from sqlalchemy import (
    Column, DateTime, ForeignKey, String, Text,
    Integer, Boolean, Enum, Numeric,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base


class UserRole(str, enum.Enum):
    farmer = "farmer"
    buyer = "buyer"
    admin = "admin"
    dispatch_rider = "dispatch_rider"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False)
    products = relationship("Product", back_populates="farmer")
    orders = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    reviews = relationship("Review", back_populates="buyer")
    deliveries = relationship(
        "Order", back_populates="dispatch_rider", foreign_keys="Order.dispatch_rider_id"
    )
    notifications = relationship("Notification", back_populates="user")


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    business_name = Column(String)
    location = Column(String, nullable=False)
    nin = Column(String, nullable=False)
    bvn = Column(String, nullable=True)
    bank_name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    total_sales = Column(Numeric(12, 2), default=0)
    rating = Column(Numeric(3, 2), default=0)

    # Virtual Account fields
    virtual_account_number = Column(String, nullable=True)
    virtual_account_business_name = Column(String, nullable=True)
    virtual_account_identifier = Column(String, nullable=True)
    virtual_account_bank_code = Column(String, nullable=True)
    virtual_account_bank_name = Column(String, nullable=True)
    virtual_account_created_at = Column(DateTime, nullable=True)
    virtual_account_is_active = Column(Boolean, default=True)

    # KYC
    bvn_verified = Column(Boolean, default=False)
    bvn_verified_at = Column(DateTime, nullable=True)

    # Tracks amount owed to farmer — backed by Squad merchant wallet
    escrow_balance = Column(Numeric(12, 2), default=0)

    # Farmer's real bank account for Transfer API payouts
    settlement_account_number = Column(String, nullable=True)
    settlement_bank_code = Column(String, nullable=True)

    user = relationship("User", back_populates="farmer_profile")


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Numeric(12, 2), nullable=False)
    available_quantity = Column(Integer, nullable=False)
    unit = Column(String, nullable=False)
    scan_status = Column(String, default="pending")
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer = relationship("User", back_populates="products")
    images = relationship("ProductImage", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    image_url = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="images")
    scan_result = relationship("ScanResult", back_populates="image", uselist=False)


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("product_images.id"))
    disease_detected = Column(Boolean)
    disease_name = Column(String)
    status = Column(String)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())

    image = relationship("ProductImage", back_populates="scan_result")


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    total_amount = Column(Numeric(12, 2))
    total_amount_kobo = Column(Integer)  # Integer kobo — source of truth for matching
    status = Column(String, default="pending") # pending | paid | in_transit | delivered | confirmed | disputed | completed
    payment_status = Column(String, default="pending") # pending | paid | refunded
    delivery_status = Column(String, default="pending")# pending | assigned | in_transit | delivered | confirmed | disputed
    escrow_status = Column(String, default="held")# held | released | refunded
    

    # OTP — stored as bcrypt hash, never plaintext in DB
    otp_hash = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    is_otp_verified = Column(Boolean, default=False)

    dispatch_rider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivery_location = Column(String, nullable=False)
    delivery_fee = Column(Numeric(12, 2), default=0)
    delivery_fee_kobo = Column(Integer, default=0)

    buyer = relationship("User", back_populates="orders", foreign_keys=[buyer_id])
    dispatch_rider = relationship(
        "User", back_populates="deliveries", foreign_keys=[dispatch_rider_id]
    )
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)
    dispute = relationship("Dispute", back_populates="order", uselist=False)


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason = Column(Text)
    status = Column(String, default="pending")
    # pending | verified | rejected

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    order = relationship("Order", back_populates="dispute")
    images = relationship("DisputeImage", back_populates="dispute")


class DisputeImage(Base):
    __tablename__ = "dispute_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispute_id = Column(UUID(as_uuid=True), ForeignKey("disputes.id"))
    image_url = Column(String)
    disease_detected = Column(Boolean)
    disease_name = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    dispute = relationship("Dispute", back_populates="images")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Numeric(12, 2))
    price_kobo = Column(Integer)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True)
    payment_reference = Column(String, unique=True)
    payment_gateway = Column(String)
    amount = Column(Numeric(12, 2))
    amount_kobo = Column(Integer)
    status = Column(String)
    # pending | paid | failed | refunded
    escrow_status = Column(String, default="held")
    # held | released | refunded

    paid_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    # Squad Transfer API payout tracking
    payout_reference = Column(String, nullable=True)
    payout_status = Column(String, nullable=True)  # pending | success | failed
    payout_initiated_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="payment")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="reviews")
    buyer = relationship("User", back_populates="reviews")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
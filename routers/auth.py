"""
routers/auth.py
Authentication — register, login, farmer profile creation + VA setup.
BVN is never returned in any response.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from authentication.OAuth2 import create_access_token, get_current_user
from authentication.hashing import Hash
from db.database import get_db
from db.model import FarmerProfile, User, UserRole
from db.schemas import (
    FarmerProfileBase,
    FarmerProfileResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from services.virtual_account import SquadVirtualAccountService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Full NIP bank code mapping — extend as needed
BANK_CODE_MAP = {
    "access bank": "044",
    "gtbank": "058",
    "guaranty trust bank": "058",
    "gt bank": "058",
    "first bank": "011",
    "uba": "033",
    "united bank for africa": "033",
    "zenith bank": "057",
    "zenith": "057",
    "polaris bank": "076",
    "polaris": "076",
    "fidelity bank": "070",
    "fidelity": "070",
    "stanbic ibtc": "068",
    "stanbic": "068",
    "union bank": "032",
    "ecobank": "050",
    "sterling bank": "232",
    "sterling": "232",
    "wema bank": "035",
    "kuda": "090267",
    "kuda bank": "090267",
    "opay": "999992",
    "palmpay": "999991",
}


def get_bank_code(bank_name: str) -> str:
    """Resolve bank name to NIP code. Returns '044' (Access) as fallback."""
    code = BANK_CODE_MAP.get(bank_name.strip().lower())
    if not code:
        # Log unknown bank names so they can be added to the map
        print(f"[WARN] Unknown bank name: '{bank_name}' — defaulting to Access Bank code")
        return "044"
    return code


@router.post("/register", response_model=UserResponse)
def register(request: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    new_user = User(
        full_name=request.full_name,
        email=request.email,
        phone_number=request.phone_number,
        password=Hash.hash_password(request.password),
        role=request.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(request: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not Hash.verify(user.password, request.password):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token({"sub": str(user.id)})

    # Build profile summary — BVN intentionally excluded
    profile = {}
    if user.role == UserRole.farmer and user.farmer_profile:
        fp = user.farmer_profile
        profile = {
            "business_name": fp.business_name,
            "location": fp.location,
            "bank_name": fp.bank_name,
            "account_number": fp.account_number,
            "virtual_account_number": fp.virtual_account_number,
            "virtual_account_bank_name": fp.virtual_account_bank_name,
            "escrow_balance": float(fp.escrow_balance) if fp.escrow_balance else 0.0,
            "total_sales": float(fp.total_sales) if fp.total_sales else 0.0,
            "bvn_verified": fp.bvn_verified,
            "created_at": str(fp.created_at),
        }

    return {
        "access_token": token,
        "token_type": "bearer",
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "phone_number": user.phone_number,
        "id": str(user.id),
        "is_verified": user.is_verified,
        "profile": profile,
        "created_at": user.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@router.post("/farmer_profile", response_model=FarmerProfileResponse)
def create_farmer_profile(
    request: FarmerProfileBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.farmer:
        raise HTTPException(403, "Only farmers can create a profile")

    if db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first():
        raise HTTPException(400, "Profile already exists")

    if request.location not in ["kaduna_south", "kaduna_north", "kaduna_central"]:
        raise HTTPException(400, "Invalid location")

    if len(request.bvn) != 11:
        raise HTTPException(400, "BVN must be exactly 11 digits")

    bank_code = get_bank_code(request.bank_name)

    new_profile = FarmerProfile(
        business_name=request.business_name,
        location=request.location,
        user_id=current_user.id,
        nin=request.nin,
        bvn=request.bvn,
        bank_name=request.bank_name,
        account_number=request.account_number,
        settlement_account_number=request.account_number,
        settlement_bank_code=bank_code,
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    # Create Squad Static Virtual Account for this farmer
    va_service = SquadVirtualAccountService(db)
    try:
        va_data = va_service.create_farmer_virtual_account(
            farmer_id=str(current_user.id),
            business_name=request.business_name,
            mobile_number=current_user.phone_number,
            bvn=request.bvn,
            beneficiary_account=request.account_number,
        )

        if va_data.get("success"):
            new_profile.virtual_account_number = va_data["account_number"]
            new_profile.virtual_account_business_name = request.business_name
            new_profile.virtual_account_identifier = va_data["customer_identifier"]
            new_profile.virtual_account_bank_code = va_data.get("bank_code")
            new_profile.virtual_account_bank_name = va_data.get("bank_name", "GTBank")
            new_profile.virtual_account_created_at = datetime.utcnow()
            new_profile.virtual_account_is_active = True
            new_profile.bvn_verified = True
            new_profile.bvn_verified_at = datetime.utcnow()

            db.commit()
            print(f"✅ VA {va_data['account_number']} created for {request.business_name}")

    except Exception as e:
        # VA creation failure is non-fatal — profile still saved
        print(f"⚠️ VA creation failed for {request.business_name}: {str(e)}")

    return new_profile


@router.get("/profile", response_model=FarmerProfileResponse)
def get_farmer_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.farmer:
        raise HTTPException(403, "Only farmers can access this endpoint")

    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")

    return profile
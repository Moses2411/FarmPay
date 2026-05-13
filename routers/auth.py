from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from db.model import User, FarmerProfile, UserRole, OrderItem, Review, Product, Order
from db.schemas import UserCreate, UserLogin, UserResponse, FarmerProfileBase, FarmerProfileResponse
from authentication.hashing import Hash
from authentication.OAuth2 import create_access_token, get_current_user
from sqlalchemy import func


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
def register(request: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == request.email).first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    new_user = User(
        full_name=request.full_name,
        email=request.email,
        phone_number = request.phone_number,
        password=Hash.hash_password(request.password),
        role=request.role
    )

    if new_user.role not in ["farmer", "buyer", "admin", "dispatch_rider"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    db.add(new_user)
    db.commit()

    return new_user


@router.post("/login")
def login(request: UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.email == request.email).first()

    if not db_user:
        raise HTTPException(401, "Invalid credentials")

    if not Hash.verify(db_user.password, request.password):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token({"sub": str(db_user.id)})

    # Build profile based on role
    profile = {}

    if db_user.role == UserRole.farmer and db_user.farmer_profile:
        profile = {
            "business_name": db_user.farmer_profile.business_name,
            "location": db_user.farmer_profile.location,
            "created_at": str(db_user.farmer_profile.created_at),
            "nin": db_user.farmer_profile.nin,
            "bank_name": db_user.farmer_profile.bank_name,
            "account_number": db_user.farmer_profile.account_number
        }

    return {
        "access_token": token,
        "full_name": db_user.full_name,
        "email": db_user.email,
        "role": db_user.role,
        "phone_number": db_user.phone_number,
        "id": str(db_user.id),
        "is_verified": db_user.is_verified,
        "profile": profile,
        "created_at": db_user.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
    }

@router.post("/farmer_profile")
def profile(request: FarmerProfileBase, db:Session = Depends(get_db), loggedIn: User = Depends(get_current_user)):

    user = db.query(User).filter(User.id == loggedIn.id).first()
    if user.role != "farmer":
        raise HTTPException(status_code = 403, detail = "Only farmers can create a profile")

    existing = db.query(FarmerProfile).filter(FarmerProfile.user_id == loggedIn.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")

    new_profile = FarmerProfile(
        business_name = request.business_name,
        location = request.location,
        user_id = loggedIn.id,
        nin = request.nin,
        bank_name = request.bank_name,
        account_number = request.account_number,
    )

    db.add(new_profile)
    db.commit()

    return {
        "business_name": request.business_name,
        "location": request.location,
        "user_id": loggedIn.id,
        "nin": request.nin,
        "bank_name": request.bank_name,
        "account_number": request.account_number,
    }


@router.get("/profile", response_model=FarmerProfileResponse)
def get_farmer_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != "farmer":
        raise HTTPException(status_code=403, detail="Only farmers allowed")

    profile = db.query(FarmerProfile).filter(
        FarmerProfile.user_id == current_user.id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


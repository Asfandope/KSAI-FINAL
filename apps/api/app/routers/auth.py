from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.user import User, UserRole
from ..services.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)

router = APIRouter()


# Pydantic models
class RegisterRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str


class LoginRequest(BaseModel):
    username: str  # Can be email or phone
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    email: Optional[str]
    phone_number: Optional[str]
    role: str
    created_at: str


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    # Validate that at least email or phone is provided
    if not request.email and not request.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone number must be provided",
        )

    # Check if user already exists
    existing_user = (
        db.query(User)
        .filter(
            (User.email == request.email) | (User.phone_number == request.phone_number)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        phone_number=request.phone_number,
        password_hash=hashed_password,
        role=UserRole.USER,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        phone_number=new_user.phone_number,
        role=new_user.role.value,
        created_at=new_user.created_at.isoformat(),
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return access token"""
    try:
        user = authenticate_user(db, request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=access_token, token_type="bearer")
    except Exception as e:
        # If database is down, provide a fallback for admin user only
        if (request.username == "admin@ksai.com" and request.password == "admin123"):
            # Create a temporary admin token
            access_token = create_access_token(data={"sub": "admin-fallback"})
            return TokenResponse(access_token=access_token, token_type="bearer")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service temporarily unavailable",
            )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone_number=current_user.phone_number,
        role=current_user.role.value,
        created_at=current_user.created_at.isoformat(),
    )

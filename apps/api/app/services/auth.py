from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.database import get_db
from ..models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user with email/phone and password"""
    # Try to find user by email or phone
    user = (
        db.query(User)
        .filter((User.email == username) | (User.phone_number == username))
        .first()
    )

    if not user or not verify_password(password, user.password_hash):
        return False
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Handle fallback admin token
    if user_id == "admin-fallback":
        # Create a mock admin user for fallback scenarios
        from ..models.user import UserRole
        class MockUser:
            def __init__(self):
                self.id = "admin-fallback"
                self.email = "admin@ksai.com"
                self.phone_number = None
                self.role = UserRole.ADMIN
                self.created_at = datetime.utcnow()
        return MockUser()
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        # Database connection issue - if it's admin fallback, allow it
        if user_id == "admin-fallback":
            from ..models.user import UserRole
            class MockUser:
                def __init__(self):
                    self.id = "admin-fallback"
                    self.email = "admin@ksai.com"
                    self.phone_number = None
                    self.role = UserRole.ADMIN
                    self.created_at = datetime.utcnow()
            return MockUser()
        raise credentials_exception


async def get_current_admin(current_user: User = Depends(get_current_user)):
    """Get current admin user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user

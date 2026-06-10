"""OAuth2 authentication endpoints."""

from datetime import timedelta
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
import logging
import sys
from pathlib import Path

# Add security-service to path for password breach checking
security_service_path = Path(__file__).parent.parent.parent / "security-service"
if security_service_path.exists():
    sys.path.insert(0, str(security_service_path))

from app.config import settings
from app.models import User, Base
from app.auth.jwt_handler import create_access_token, verify_token
from app.database import get_db

logger = logging.getLogger(__name__)

# Try to import password breach service (optional - fails gracefully if not available)
try:
    from security_service.intelligence.password_breach import PasswordBreachService

    password_breach_service = PasswordBreachService()
    PASSWORD_BREACH_CHECK_ENABLED = password_breach_service.enabled
except ImportError:
    logger.warning("Password breach service not available - password checking disabled")
    password_breach_service = None
    PASSWORD_BREACH_CHECK_ENABLED = False

# Try to import email breach service (optional - fails gracefully if not available)
try:
    from security_service.intelligence.email_breach import EmailBreachService

    EMAIL_BREACH_CHECK_ENABLED = True
except ImportError:
    logger.warning("Email breach service not available - email checking disabled")
    EMAIL_BREACH_CHECK_ENABLED = False

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


OAUTH2_TOKEN_TYPE = "bearer"  # nosec B105 - OAuth2 token type label, not a credential


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = OAUTH2_TOKEN_TYPE


class UserCreate(BaseModel):
    """User creation model."""

    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    """User response model."""

    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Token:
    """OAuth2 token endpoint."""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "email": user.email, "is_admin": user.is_admin},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": OAUTH2_TOKEN_TYPE}


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate, db: Session = Depends(get_db)
) -> UserResponse:
    """Register a new user."""
    # Check if user exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Check password against breach database
    if PASSWORD_BREACH_CHECK_ENABLED and password_breach_service:
        try:
            is_valid, error_message = await password_breach_service.validate_password(
                user_data.password
            )
            if not is_valid:
                logger.warning(
                    f"Registration blocked: breached password for email {user_data.email}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                    or "Password has been found in a data breach. Please choose a different password.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password breach check failed: {e}")
            # Fail open - don't block registration if service is unavailable
            pass

    # Check email against breach database (warn but don't block)
    email_breaches = []
    if EMAIL_BREACH_CHECK_ENABLED:
        try:
            from security_service.intelligence.email_breach import EmailBreachService

            email_breach_service = EmailBreachService(db)
            email_breaches = await email_breach_service.check_email(
                user_data.email,
                truncate_response=True,  # Faster check, just breach names
            )
            if email_breaches:
                logger.warning(
                    f"Registration: email {user_data.email} found in {len(email_breaches)} breach(es)"
                )
                # Note: We warn but don't block - user may still want to register
                # In production, you might want to block or require additional verification
        except Exception as e:
            logger.error(f"Email breach check failed: {e}")
            # Fail open - don't block registration if service is unavailable
            pass

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # If email was breached, update breach records with user_id
    if email_breaches and EMAIL_BREACH_CHECK_ENABLED:
        try:
            from security_service.intelligence.email_breach import EmailBreachService

            email_breach_service = EmailBreachService(db)
            # Re-check to associate user_id with breaches
            await email_breach_service.check_email(
                user_data.email,
                user_id=db_user.id,
                force_refresh=False,  # Use cached data
            )
        except Exception as e:
            logger.error(f"Failed to update breach records with user_id: {e}")

    return db_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user information."""
    return current_user


@router.post("/init-db")
async def init_database(
    request: Request, current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Initialize database tables (development only - requires explicit enable)."""
    # Layer 1: Check explicit enable flag
    if not settings.enable_debug_endpoints:
        logger.warning(f"Blocked /init-db access from {request.client.host}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    # Layer 2: Require admin authentication
    if settings.debug_endpoint_require_admin and not current_user.is_admin:
        logger.warning(
            f"Blocked /init-db access - non-admin user: {current_user.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    # Layer 3: IP whitelist check
    if settings.debug_endpoint_allowed_ips:
        client_ip = request.client.host
        if client_ip not in settings.debug_endpoint_allowed_ips:
            logger.warning(f"Blocked /init-db access from unauthorized IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    # Log successful access
    logger.info(
        f"Database initialization triggered by admin user: {current_user.username} from {request.client.host}"
    )

    from app.database import init_db

    init_db()
    return {"message": "Database initialized"}

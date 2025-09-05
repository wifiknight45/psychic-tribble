import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis.asyncio as redis
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.settings import settings

# Logging setup (Best practice: Monitor auth actions)
logger = logging.getLogger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Redis connection for token revocation and login rate limiting
redis_client: Optional[redis.Redis] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    jti: Optional[str] = None

class UserInDB(BaseModel):
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False

#### PASSWORD HASHING ####
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare hashed password using bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash password securely with bcrypt."""
    return pwd_context.hash(password)

#### USER LOADER (EXAMPLE) ####
def get_user_by_username(db: Session, username: str) -> Optional[UserInDB]:
    """Query user from DB. Replace with ORM query."""
    user = db.query(UserInDB).filter_by(username=username).first()
    return user

#### JWT CREATION & VALIDATION ####
def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None, jti: Optional[str] = None
) -> str:
    """Generate JWT access token with expiration and unique JTI."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    if not jti:
        # Generate unique identifier for token (for revocation / auditing)
        from uuid import uuid4
        jti = str(uuid4())
    to_encode.update({"jti": jti})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode JWT token and validate signature and expiration."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis.from_url(
            settings.redis_url, decode_responses=True
        )
    return redis_client

#### TOKEN REVOCATION AND BLACKLISTING ####
async def is_token_revoked(jti: str, redis_client: redis.Redis) -> bool:
    """Check if a token is blacklisted (revoked) in Redis."""
    return await redis_client.exists(f"revoked_{jti}") == 1

async def revoke_token(jti: str, expires_in: int, redis_client: redis.Redis) -> None:
    """Blacklist token in Redis with TTL (token expires after this period)."""
    await redis_client.setex(f"revoked_{jti}", expires_in, "revoked")
    logger.info(f"Token revoked (JTI={jti})")

#### AUTHENTICATION/LOGIN WITH RATE LIMITING ####
async def rate_limit_login(username: str, redis_client: redis.Redis):
    """Enforce login rate limit per username. Raise if exceeded."""
    key = f"login_attempts_{username}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, settings.login_rate_limit_period)
    if count > settings.login_rate_limit_max:
        logger.warning(f"Login rate limit exceeded for {username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts, please try again later."
        )

async def authenticate_user(db: Session, username: str, password: str, redis_client: redis.Redis) -> Optional[UserInDB]:
    """Authenticate user—verify password, enforce rate limits, and return user if valid."""
    await rate_limit_login(username, redis_client)
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        logger.info(f"Authentication failed for username: {username}")
        return None
    if not user.is_active:
        logger.info(f"Inactive user login attempt: {username}")
        return None
    return user

#### FASTAPI DEPENDENCY FOR CURRENT USER ####
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client)
) -> UserInDB:
    """Dependency: Authenticated current user with token revocation check."""
    payload = decode_token(token)
    username: str = payload.get("sub")
    jti: str = payload.get("jti")
    if username is None or jti is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload invalid")
    # Check for revoked tokens (logout/forced logout)
    if await is_token_revoked(jti, redis_client):
        logger.info(f"Revoked token rejected for user {username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#### REFRESH TOKEN SUPPORT ####
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None, jti: Optional[str] = None) -> str:
    """Create refresh JWT token."""
    exp = expires_delta or timedelta(days=settings.refresh_token_expire_days)
    return create_access_token(data, expires_delta=exp, jti=jti)

async def revoke_refresh_token(jti: str, expires_in: int, redis_client: redis.Redis) -> None:
    """Blacklist a refresh token (same as access token)."""
    await revoke_token(jti, expires_in, redis_client)
    logger.info(f"Refresh token revoked (JTI={jti})")

#### LOGGING DECORATOR FOR CRITICAL AUTH ACTIONS ####
def log_auth_event(event: str, username: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
    logger.info(f"AUDIT_AUTH | {event} | username={username} | context={context}")

#### INIT REDIS (STARTUP) ####
async def init_redis_connection():
    global redis_client
    redis_client = redis.Redis.from_url(
        settings.redis_url, decode_responses=True
    )
    

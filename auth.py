# auth.py

import time
import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import List, Optional, Callable, Any, Dict

import pyotp
import hvac
from fastapi import (
    Depends,
    HTTPException,
    status,
    Security,
    Request,
    Response
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes
)
from fastapi.concurrency import run_in_threadpool
from jose import jwt, JWTError
from passlib.context import CryptContext

from sqlalchemy.ext.asyncio import AsyncSession

# Constants and secrets injection
from .settings import settings    # Assume this is a pydantic settings object
from .db import get_async_session  # Dependency, returns Async SQLAlchemy session
from .redis import redis_async     # aioredis client instance
from .vault import get_vault_client  # Dependency, returns an hvac.Client instance

# --- Constants ---
JWT_ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
REDIS_NAMESPACE = "pt_auth:"

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Logging Setup (structured JSON) ---
class JSONLogger:
    def __init__(self, name: str = "pt_auth"):
        self.logger = logging.getLogger(name)
        if not any(isinstance(h.formatter, JSONLogFormatter) for h in self.logger.handlers):
            handler = logging.StreamHandler()
            handler.setFormatter(JSONLogFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def emit(
        self,
        *,
        event_type: str,
        user_id: Optional[str] = None,
        jti: Optional[str] = None,
        ip: Optional[str] = None,
        status: str = "info",
        message: Optional[str] = None,
        extra: Optional[dict] = None
    ):
        record = {
            "event_type": event_type,
            "user_id": user_id,
            "jti": jti,
            "ip": ip,
            "status": status,
            "message": message,
            "timestamp": int(time.time()),
        }
        if extra:
            record.update(extra)
        self.logger.info(json.dumps(record))

class JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, str):
            try:
                message = json.loads(record.msg)
            except Exception:
                message = {"message": record.msg}
        else:
            message = record.msg
        message["level"] = record.levelname
        return json.dumps(message)

logger = JSONLogger()

# --- Models and Schemas ---
# Minimal user and token schemas (could be expanded as needed)
from pydantic import BaseModel

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []
    jti: Optional[str] = None
    iat: Optional[int] = None

class User(BaseModel):
    username: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    totp_enabled: bool = False

# --- JWT Helpers ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    now = int(time.time())
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.fromtimestamp(now, tz=timezone.utc) + expires_delta
    else:
        expire = datetime.fromtimestamp(now, tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = generate_jti()
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": now,
        "jti": jti,
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    now = int(time.time())
    if expires_delta is None:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.fromtimestamp(now, tz=timezone.utc) + expires_delta
    jti = generate_jti()
    to_encode = data.copy()
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": now,
        "jti": jti,
        "type": "refresh",
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        iat = payload.get("iat")
        if not isinstance(iat, int):
            raise HTTPException(status_code=401, detail="Malformed token issued at")
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def generate_jti() -> str:
    # 128-bit random hex string
    return pyotp.random_base32(length=32)

# --- Redis-backed Token Revocation ---
async def revoke_token(jti: str, exp: int):
    key = f"{REDIS_NAMESPACE}revoked:{jti}"
    ttl = exp - int(time.time())
    if ttl > 0:
        await redis_async.set(key, "true", ex=ttl)
    logger.emit(event_type="token_revoked", jti=jti, status="revoked")

async def is_token_revoked(jti: str) -> bool:
    key = f"{REDIS_NAMESPACE}revoked:{jti}"
    return await redis_async.exists(key) > 0

# --- Exponential Lockout / Rate Limiting ---
BASE_LOCKOUT_SECONDS = 30
EXPONENTIAL_FACTOR = 2
MAX_LOCKOUT_ATTEMPTS = 5

async def increment_failed_login(username: str) -> int:
    key = f"{REDIS_NAMESPACE}fail:{username}"
    attempts = await redis_async.incr(key)
    await redis_async.expire(key, 3600)
    return attempts

async def reset_failed_logins(username: str):
    key = f"{REDIS_NAMESPACE}fail:{username}"
    await redis_async.delete(key)

def calculate_lockout_duration(attempts: int) -> int:
    return BASE_LOCKOUT_SECONDS * (EXPONENTIAL_FACTOR ** (attempts - 1))

async def is_lockout_active(username: str) -> Optional[int]:
    key = f"{REDIS_NAMESPACE}fail:{username}"
    attempts = await redis_async.get(key)
    if attempts is None:
        return None
    attempts = int(attempts)
    if attempts < MAX_LOCKOUT_ATTEMPTS:
        return None
    lockout_duration = calculate_lockout_duration(attempts)
    blocked_key = f"{REDIS_NAMESPACE}blocked:{username}"
    # Ensure blocked_key expires at the correct interval
    if not await redis_async.exists(blocked_key):
        await redis_async.set(blocked_key, "true", ex=lockout_duration)
    ttl = await redis_async.ttl(blocked_key)
    return max(ttl, 0)

# --- Password Hashing/Verification ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# --- OAuth2 Setup with Scopes ---
OAUTH2_SCOPES = {
    "read": "Read only access",
    "write": "Write access",
    "admin": "Administrative operations",
    "mfa_sensitive": "Scope requiring MFA"
}

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes=OAUTH2_SCOPES
)

# --- Scope Enforcement Decorator ---
def enforce_scopes(required_scopes: List[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token: str = await oauth2_scheme(request)
            payload = decode_jwt_token(token)
            token_scopes = payload.get("scopes", [])
            if not all(scope in token_scopes for scope in required_scopes):
                logger.emit(event_type="scope_denied", user_id=payload.get("sub"), status="denied", message="Insufficient scope")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
            # Enforce MFA for sensitive scopes
            if "mfa_sensitive" in required_scopes:
                await enforce_mfa(request, payload)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# --- MFA (TOTP) Implementation and Secure Secret Storage ---
async def get_user_mfa_secret(username: str, vault_client: hvac.Client) -> Optional[str]:
    secret_path = f"secret/data/{REDIS_NAMESPACE}mfa_secret:{username}"
    try:
        secret = vault_client.secrets.kv.v2.read_secret_version(path=secret_path)
        return secret['data']['data']['secret']
    except hvac.exceptions.InvalidPath:
        return None

async def set_user_mfa_secret(username: str, secret: str, vault_client: hvac.Client):
    secret_path = f"secret/data/{REDIS_NAMESPACE}mfa_secret:{username}"
    vault_client.secrets.kv.v2.create_or_update_secret(
        path=secret_path,
        secret={"secret": secret}
    )

async def require_mfa_code(username: str, code: str, vault_client: hvac.Client):
    secret = await get_user_mfa_secret(username, vault_client)
    if not secret:
        raise HTTPException(status_code=401, detail="MFA not enrolled")
    totp = pyotp.TOTP(secret)
    if not totp.verify(code):
        logger.emit(event_type="mfa_failed", user_id=username, status="failed")
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    logger.emit(event_type="mfa_success", user_id=username, status="success")

async def enforce_mfa(request: Request, payload: dict):
    mfa_code = request.headers.get("x-mfa-code") or request.query_params.get("mfa_code")
    if not mfa_code:
        raise HTTPException(status_code=401, detail="MFA code required")
    username = payload["sub"]
    vault_client = await get_vault_client()
    await require_mfa_code(username, mfa_code, vault_client)

# --- User Management Functions ---
async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    # Replace with real ORM query
    user_row = await run_in_threadpool(lambda: ...)  # Your query here
    if user_row:
        return User(**user_row)
    return None

# --- Token Issuance and Rotation ---
async def issue_tokens(user: User) -> dict:
    data = {"sub": user.username, "scopes": ["read"]}  # Assign scopes dynamically as needed
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    # Store refresh jti as valid, revoke on use (rotation)
    decoded_refresh = decode_jwt_token(refresh_token)
    await redis_async.set(f"{REDIS_NAMESPACE}refresh:{decoded_refresh['jti']}", "valid", ex=REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

async def rotate_refresh_token(old_token: str, new_token: str):
    # Revoke old, record new
    old_payload = decode_jwt_token(old_token)
    new_payload = decode_jwt_token(new_token)
    await revoke_token(old_payload["jti"], old_payload["exp"])
    await redis_async.set(f"{REDIS_NAMESPACE}refresh:{new_payload['jti']}", "valid", ex=new_payload["exp"] - int(time.time()))

async def validate_refresh_token(token: str) -> dict:
    payload = decode_jwt_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")
    # Check if revoked
    if await is_token_revoked(payload["jti"]):
        raise HTTPException(status_code=401, detail="Refresh token revoked")
    valid = await redis_async.get(f"{REDIS_NAMESPACE}refresh:{payload['jti']}")
    if valid != b"valid":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return payload

# --- Login Route Example ---
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
    vault_client: hvac.Client = Depends(get_vault_client),
):
    ip = request.client.host
    lockout_ttl = await is_lockout_active(form_data.username)
    if lockout_ttl:
        logger.emit(event_type="login_lockout", user_id=form_data.username, ip=ip, status="locked", message=f"Lockout TTL: {lockout_ttl}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked, try again in {lockout_ttl} seconds."
        )
    user = await get_user_by_username(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        attempts = await increment_failed_login(form_data.username)
        logger.emit(event_type="login_failed", user_id=form_data.username, ip=ip, status="failed", message=f"Failed attempt {attempts}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    await reset_failed_logins(form_data.username)
    # MFA required?
    if user.totp_enabled:
        code = request.headers.get("x-mfa-code") or form_data.scopes.get("mfa_code", None)
        if not code:
            raise HTTPException(status_code=401, detail="MFA code required")
        await require_mfa_code(user.username, code, vault_client)
    tokens = await issue_tokens(user)
    logger.emit(event_type="login_success", user_id=user.username, ip=ip, status="success", jti=decode_jwt_token(tokens["access_token"]).get("jti"))
    return tokens

# --- Refresh Endpoint Example ---
async def refresh_token_endpoint(
    request: Request,
    refresh_token: str,
    session: AsyncSession = Depends(get_async_session)
):
    ip = request.client.host
    try:
        old_payload = await validate_refresh_token(refresh_token)
    except HTTPException as e:
        logger.emit(event_type="refresh_failed", user_id=None, ip=ip, jti=None, status="failed", message=str(e.detail))
        raise
    user = await get_user_by_username(session, old_payload.get("sub"))
    if not user:
        logger.emit(event_type="refresh_failed", user_id=old_payload.get("sub"), ip=ip, status="failed", message="User not found")
        raise HTTPException(status_code=401, detail="User not found")
    new_tokens = await issue_tokens(user)
    await rotate_refresh_token(refresh_token, new_tokens["refresh_token"])
    logger.emit(event_type="refresh_success", user_id=user.username, ip=ip, jti=decode_jwt_token(new_tokens["refresh_token"]).get("jti"), status="success")
    return new_tokens

# --- MFA Setup Endpoint Example ---
async def setup_mfa(
    request: Request,
    current_user: User = Depends(...),  # Fill in with your current_user dependency
    vault_client: hvac.Client = Depends(get_vault_client)
):
    # Generate new TOTP secret
    secret = pyotp.random_base32()
    await set_user_mfa_secret(current_user.username, secret, vault_client)
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.username, issuer_name="Psychic-Tribble")
    # Optionally, provide QR code
    logger.emit(event_type="mfa_setup", user_id=current_user.username, status="created")
    return {"otpauth_uri": uri, "secret": secret}

# --- Example Protected View with Scope and MFA Enforcement ---
@enforce_scopes(["admin", "mfa_sensitive"])
async def admin_action(request: Request, *args, **kwargs):
    # Actual view logic here
    return {"result": "admin level action, MFA verified"}

# --- Utilities ---
async def get_client_ip(request: Request) -> str:
    # Support for proxies if present/configured
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host

# --- Exportable API setup for router ---
__all__ = [
    "login",
    "refresh_token_endpoint",
    "setup_mfa",
    "admin_action",
    "enforce_scopes",
]

    

# auth.py
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# In production, load from environment (.env or secrets manager)
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ---------------------------
# Password hashing with bcrypt
# ---------------------------

def get_password_hash(password: str) -> str:
    """
    Hashes the given plaintext password using bcrypt.
    Returns a UTF-8 string suitable for DB storage (TEXT).
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
    salt = bcrypt.gensalt()  # default cost works well; tune via rounds if needed
    hashed: bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a bcrypt hash.
    Accepts stored hashes as UTF-8 strings.
    """
    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        # If the stored hash is malformed
        return False

# ---------------------------
# JWT utilities
# ---------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Example dependency returning a username from the token's `sub` claim.
    Swap to fetch a full User object from DB as needed.
    """
    payload = decode_access_token(token)
    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return username

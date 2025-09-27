from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from src.psychic_tribble.core.database import get_db_session
from src.psychic_tribble.crud.user import get_user_by_email, get_user_by_id
from src.psychic_tribble.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

async def get_db() -> AsyncSession:
    async for s in get_db_session():
        yield s

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        user_id = payload.get("id")
        if not sub and not user_id:
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = None
    if user_id:
        user = await get_user_by_id(db, int(user_id))
    if not user and sub:
        user = await get_user_by_email(db, sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

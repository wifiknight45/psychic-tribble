from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from src.psychic_tribble.models.user import User
from src.psychic_tribble.schemas.user import UserCreate

# Inject via dependency or config
from psychic_tribble.config import get_settings

def get_password_context():
    settings = get_settings()
    return CryptContext(
        schemes=["bcrypt"], 
        deprecated="auto",
        bcrypt__rounds=settings.bcrypt_rounds  # Configurable
    )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_context = get_password_context()
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    pwd_context = get_password_context()
    return pwd_context.hash(password)

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed = get_password_hash(user_in.password)
    user = User(email=user_in.email, hashed_password=hashed)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

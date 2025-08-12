from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    name: str = Field(..., max_length=100, description="User's full name")

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True  # Supports ORM models

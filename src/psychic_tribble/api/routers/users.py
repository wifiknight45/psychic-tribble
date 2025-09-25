"""User API endpoints."""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

users_router = APIRouter()


# Pydantic models for request/response
class UserCreate(BaseModel):
    """User creation request schema."""
    name: str


class UserResponse(BaseModel):
    """User response schema."""
    user_id: int
    name: str


@users_router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """
    Create a new user.
    
    Args:
        user: User creation data
        
    Returns:
        Created user data
    """
    logger.info(f"Creating user with name={user.name}")
    
    # Placeholder implementation - would integrate with actual service
    new_user_id = 1  # This would come from the actual user service
    
    logger.info(f"User created with id={new_user_id}")
    
    return UserResponse(user_id=new_user_id, name=user.name)


@users_router.get("/", response_model=List[UserResponse])
async def list_users():
    """List all users."""
    logger.info("Listing all users")
    
    # Placeholder implementation
    return [
        UserResponse(user_id=1, name="Test User")
    ]


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID."""
    logger.info(f"Getting user with id={user_id}")
    
    # Placeholder implementation
    if user_id <= 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(user_id=user_id, name=f"User {user_id}")

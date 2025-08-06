from pydantic import BaseModel, Field, root_validator
from datetime import datetime
from typing import Optional

class EventCreate(BaseModel):
    title: str = Field(..., max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=1000, description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    location: Optional[str] = Field(None, max_length=200, description="Event location")

    @root_validator
    def check_time_range(cls, values):
        start_time, end_time = values.get("start_time"), values.get("end_time")
        if start_time and end_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return values

class EventResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]

    class Config:
        from_attributes = Truee

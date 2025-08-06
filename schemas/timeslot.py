from pydantic import BaseModel, Field, root_validator
from datetime import date, time
from typing import Optional

class TimeslotCreate(BaseModel):
    date: date = Field(..., description="Date of the timeslot")
    start_time: time = Field(..., description="Start time (HH:MM)")
    end_time: time = Field(..., description="End time (HH:MM)")
    description: Optional[str] = Field(None, max_length=500, description="Timeslot description")

    @root_validator
    def check_time_range(cls, values):
        start_time, end_time = values.get("start_time"), values.get("end_time")
        if start_time and end_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return values

class TimeslotResponse(BaseModel):
    id: int
    date: date
    start_time: time
    end_time: time
    description: Optional[str]

    class Config:
        from_attributes = True

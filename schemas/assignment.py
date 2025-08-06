from pydantic import BaseModel, Field

class AssignmentCreate(BaseModel):
    user_id: int = Field(..., description="ID of the user assigned")
    event_id: int = Field(..., description="ID of the event or timeslot assigned")

class AssignmentResponse(BaseModel):
    id: int
    user_id: int
    event_id: int

    class Config:
        from_attributes = True


from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ParticipantBase(BaseModel):
    name: str
    birth_date: datetime
    weight: float
    academy: str
    height: float
    category: str
    payment_proof: str = None
    email: str
    aztlan_id: str = None

    class Config:
        orm_mode = True

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantResponse(ParticipantBase):
    id: int
    payment_proof: Optional[str] = None
    created_at: Optional[datetime]  # Nuevo campo

    class Config:
        orm_mode = True
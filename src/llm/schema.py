from pydantic import BaseModel, Field
from enum import Enum

class Category(str, Enum):
    work = "work"
    errand = "errand"
    health = "health"
    chore = "chore"
    other = "other"

class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"

class TriageOutput(BaseModel):
    category: Category
    urgency: Urgency
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
class TriageInput(BaseModel):
    text: str
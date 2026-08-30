from pydantic import BaseModel, Field
from enum import Enum
import json
import re

def extract_json(text: str) -> dict:
    """Strip markdown code fences if present, then parse as JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(cleaned)

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
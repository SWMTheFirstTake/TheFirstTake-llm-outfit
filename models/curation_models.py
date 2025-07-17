from pydantic import BaseModel
from typing import List, Optional, Dict, TypeVar, Generic
from enum import Enum



class CurationStyle(str, Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    CITY_BOY = "city_boy"

class CurationRequest(BaseModel):
    user_input: str
    room_id: int
    styles: Optional[List[CurationStyle]] = [CurationStyle.FORMAL, CurationStyle.CASUAL, CurationStyle.CITY_BOY]

class CurationResponse(BaseModel):
    room_id: int
    results: List[Dict[str, str]]  # [{"style": "formal", "content": "result"}]
    prompt_history: Optional[str] = None

class PromptRequest(BaseModel):
    prompt: str
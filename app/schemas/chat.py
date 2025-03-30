from pydantic import BaseModel
from typing import List, Dict

class ChatRequest(BaseModel):
    texto: str
    historial: List[Dict[str, str]]

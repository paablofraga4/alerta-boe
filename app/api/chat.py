from fastapi import APIRouter
from app.schemas.chat import ChatRequest
from app.services.chat_documento import responder_sobre_documento

router = APIRouter()

@router.post("/chat-documento")
def chat_documento(payload: ChatRequest):
    respuesta = responder_sobre_documento(payload.texto, payload.historial)
    return {"respuesta": respuesta}

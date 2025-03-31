from fastapi import APIRouter
from app.schemas.chat import ChatRequest
from app.services.chat_documento import responder_sobre_documento
from app.services.personal_assistant import generar_respuesta_asistente
from pydantic import BaseModel

router = APIRouter()

# Ruta actual
@router.post("/chat-documento")
def chat_documento(payload: ChatRequest):
    respuesta = responder_sobre_documento(payload.texto, payload.historial)
    return {"respuesta": respuesta}

# Nueva ruta para asistente personal
class ConsultaAsistenteRequest(BaseModel):
    mensaje: str

@router.post("/asistente-personal")
def asistente_personal(req: ConsultaAsistenteRequest):
    return generar_respuesta_asistente(req.mensaje)

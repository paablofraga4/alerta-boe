import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

def preparar_contexto(texto: str) -> str:
    """Reduce el texto para contexto inicial, limitando longitud y formato."""
    return texto.strip()[:4000]  # limite de tokens de contexto

def construir_prompt(texto: str, historial: list[dict]) -> list[dict]:
    """Construye el prompt con sistema + contexto + historial del usuario."""
    prompt = [
        {
            "role": "system",
            "content": (
                "Eres un asistente jurídico experto. Ayudas a los ciudadanos a entender el contenido de un documento legal "
                "concreto del BOE. Responde siempre basándote SOLO en el contenido proporcionado. "
                "Sé claro, directo y evita tecnicismos innecesarios."
            ),
        },
        {
            "role": "user",
            "content": (
                "Este es el contenido del documento legal sobre el que te voy a preguntar:\n\n"
                f"{preparar_contexto(texto)}"
            ),
        },
    ]
    prompt.extend(historial)
    return prompt

def responder_sobre_documento(texto: str, historial_chat: list[dict]) -> str:
    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": construir_prompt(texto, historial_chat),
                "temperature": 0.3,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        time.sleep(1.5)
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("❌ Error en responder_sobre_documento:", e)
        return "⚠️ Hubo un problema al generar la respuesta."

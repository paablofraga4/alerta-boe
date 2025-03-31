import requests
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generar_mensaje_asistente(mensaje_usuario: str, publicaciones: list):
    lista_titulares = "\n".join([f"- {p.resumen_tiktok}" for p in publicaciones])

    prompt = [
        {"role": "system", "content": "Eres un asistente legal que ayuda a ciudadanos y autónomos a entender qué publicaciones del BOE les afectan."},
        {"role": "user", "content": (
            f"""El usuario ha dicho: "{mensaje_usuario}". 

Estas son las publicaciones que podrían interesarle (cada línea es un resumen breve):

{lista_titulares}

Con base en estos resúmenes, responde al usuario explicando por qué le interesan estas publicaciones. 
No repitas los textos tal cual, haz una síntesis clara, útil, con lenguaje sencillo. 
Puedes mencionar categorías (ayudas, empleo, fiscalidad, etc.)."""
        )}
    ]

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": prompt,
            "temperature": 0.5,
            "stream": False
        },
        timeout=90  # 👈 aumenta aquí también si quieres
    )
    data = response.json()
    print("Respuesta de la API:", data)
    return response.json()["choices"][0]["message"]["content"]


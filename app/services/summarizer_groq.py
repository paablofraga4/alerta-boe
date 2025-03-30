import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"
WAIT_SECONDS = 2.1  # evitar 429 por RPM

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def resumen_prompt(texto: str):
    return [
        {"role": "system", "content": "Eres un asistente legal experto en legislación española."},
        {"role": "user", "content": (
            "Resume este texto legal de forma clara y accesible. No utilices tecnicismos. "
            "Indica qué regula, a quién afecta, si hay fechas importantes y qué acciones "
            "deben tener en cuenta ciudadanos o pequeñas empresas. Sé directo, útil y conciso.\n\n"
            f"{texto[:3500]}"
        )}
    ]

def llamar_modelo(modelo: str, texto: str) -> str:
    if not texto.strip():
        return ""
    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": modelo,
                "messages": resumen_prompt(texto),
                "temperature": 0.4,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        time.sleep(WAIT_SECONDS)  # evitar sobrecarga
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            raise RuntimeError("Rate limit (429)")
        raise
    except Exception as e:
        print("❌ Error llamando a Groq:", e)
        return ""

def resumir_texto(texto: str) -> str:
    try:
        return llamar_modelo(PRIMARY_MODEL, texto)
    except RuntimeError as e:
        if str(e) == "Rate limit (429)":
            print("🔁 Rate limit alcanzado. Intentando con modelo fallback...")
            try:
                return llamar_modelo(FALLBACK_MODEL, texto)
            except Exception as fallback_error:
                print("❌ Fallback también falló:", fallback_error)
    except Exception as e:
        print("❌ Error general:", e)
    return ""
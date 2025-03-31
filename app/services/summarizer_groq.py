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


def resumen_tiktok_prompt(texto: str):
    return [
        {"role": "system", "content": "Eres un redactor de titulares legales para una app de alertas ciudadanas."},
        {"role": "user", "content": (
            "Resume este contenido legal en un solo párrafo breve (máx. 300 caracteres), directo y sin tecnicismos. "
            "Debe sonar como una alerta útil. Di siempre quién toma la acción (Ej: El Gobierno, Hacienda, etc). "
            "Evita frases impersonales como 'se aprueba', 'se nombra'. Usa sujeto claro.\n\n"
            f"{texto[:2000]}"
        )}
    ]


def llamar_modelo(modelo: str, texto: str, prompt_fn) -> str:
    if not texto.strip():
        return ""

    intentos = 3
    for intento in range(1, intentos + 1):
        try:
            print(f"⚙️  [{modelo}] Intento {intento}...", end=" ")
            response = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": modelo,
                    "messages": prompt_fn(texto),
                    "temperature": 0.4,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            time.sleep(WAIT_SECONDS)
            print("✅ OK")
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP {e.response.status_code}")
            if e.response.status_code == 429 and intento < intentos:
                time.sleep(3 + intento * 2)
                continue
            elif e.response.status_code == 429:
                raise RuntimeError("Rate limit (429)")
        except Exception as e:
            print(f"❌ Error ({e})")
            time.sleep(3 + intento * 2)
    return ""



def resumir_texto(texto: str) -> str:
    try:
        return llamar_modelo(PRIMARY_MODEL, texto, resumen_prompt)
    except RuntimeError as e:
        if str(e) == "Rate limit (429)":
            print("🔁 Rate limit alcanzado. Intentando con modelo fallback...")
            try:
                return llamar_modelo(FALLBACK_MODEL, texto, resumen_prompt)
            except Exception as fallback_error:
                print("❌ Fallback también falló:", fallback_error)
    except Exception as e:
        print("❌ Error general:", e)
    return ""


def resumir_texto_tiktok(texto: str) -> str:
    try:
        return llamar_modelo(PRIMARY_MODEL, texto, resumen_tiktok_prompt)
    except RuntimeError as e:
        if str(e) == "Rate limit (429)":
            print("🔁 Rate limit alcanzado (tiktok). Intentando con fallback...")
            try:
                return llamar_modelo(FALLBACK_MODEL, texto, resumen_tiktok_prompt)
            except Exception as fallback_error:
                print("❌ Fallback también falló (tiktok):", fallback_error)
    except Exception as e:
        print("❌ Error general (tiktok):", e)
    return ""

import requests
from bs4 import BeautifulSoup

OLLAMA_URL = "http://localhost:11434/api/generate"

def extraer_texto_desde_html(url: str) -> str:
    """
    Extrae el contenido principal del BOE en texto plano desde la URL HTML.
    """
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        contenido = soup.find("div", {"id": "contenido"})
        texto = contenido.get_text(separator="\n", strip=True)
        return texto
    except Exception as e:
        print("❌ Error al extraer HTML:", e)
        return ""

def resumir_texto(texto: str, modelo: str = "mistral") -> str:
    """
    Resume el texto legal usando el modelo local vía Ollama.
    """
    if not texto.strip():
        return ""

    prompt = (
        "Resume este texto legal de forma clara y accesible. No utilices tecnicismos. "
        "Destaca qué regula, a quién afecta, si hay fechas importantes y qué acciones "
        "deben tener en cuenta ciudadanos o pequeñas empresas. Sé directo, útil y conciso:\n\n"
        f"{texto[:4000]}"
    )
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": modelo,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al contactar con Ollama: {e}")
    except ValueError:
        print("❌ Error al parsear JSON de respuesta")
    return ""

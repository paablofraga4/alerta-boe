import requests

res = requests.post(
    "http://localhost:8000/api/chat-documento",
    json={
        "texto": "Ejemplo de texto del documento",
        "historial": [
            {"role": "user", "content": "¿De qué trata esto?"}
        ]
    }
)

print("Código de respuesta:", res.status_code)
print("Respuesta JSON:", res.json())
import requests

res = requests.post(
    "http://localhost:8000/api/chat-documento",
    json={
        "texto": "Ejemplo de texto del documento",
        "historial": [
            {"role": "user", "content": "¿De qué trata esto?"}
        ]
    }
)

print("Código de respuesta:", res.status_code)
print("Respuesta JSON:", res.json())

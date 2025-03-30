import requests

headers = {
    "Authorization": "Bearer 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",
    "Content-Type": "application/json"
}

json_data = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "system", "content": "Eres un asistente legal español."},
        {"role": "user", "content": "Resume esta ley: Ley de protección de datos personales y garantía de los derechos digitales."}
    ],
    "temperature": 0.3,
    "stream": False
}

response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=json_data)

print("STATUS:", response.status_code)
print("BODY:", response.text)

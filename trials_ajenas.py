import requests
import json

BOE_API_BASE = "https://www.boe.es/datosabiertos/api"

# ✅ 1. Obtener sumario del BOE

def obtener_sumario_boe(fecha):
    url = f"{BOE_API_BASE}/boe/sumario/{fecha}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error sumario BOE:", response.status_code)
        return None

# ✅ 2. Obtener listado general de legislación consolidada

def obtener_listado_legislacion():
    #se puede añadir limite
    url = f"{BOE_API_BASE}/legislacion-consolidada"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error obtener listado legislación:", response.status_code)
        return None

# ✅ 3. Obtener metadatos de una legislación por ID

def obtener_metadatos_legislacion(legislation_id):
    url = f"{BOE_API_BASE}/legislacion-consolidada/id/{legislation_id}/metadatos"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error metadatos legislación:", response.status_code)
        return None

# ✅ 4. Obtener índice estructurado de una legislación

def obtener_indice_legislacion(legislation_id):
    url = f"{BOE_API_BASE}/legislacion-consolidada/id/{legislation_id}/texto/indice"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error índice legislación:", response.status_code)
        return None

# ✅ 5. Obtener contenido de un bloque (artículo) concreto

def obtener_bloque_legislacion(legislation_id, bloque_id):
    url = f"https://boe.es/datosabiertos/api/legislacion-consolidada/id/{legislation_id}/texto/bloque/{bloque_id}"
    headers = {"Accept": "application/xml"}  # 👈 Petición en XML
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.text  # 👈 XML como string
    else:
        print("❌ Error bloque legislación:", response.status_code)
        return None

# 📦 Ejemplos de uso
if __name__ == "__main__":
    # sumario = obtener_sumario_boe("20250320")
    # print(json.dumps(sumario, indent=4))

    # listado = obtener_listado_legislacion()
    # print(json.dumps(listado, indent=4))

    # metadatos = obtener_metadatos_legislacion("BOE-A-2005-1154")
    # print(json.dumps(metadatos, indent=4))

    # indice = obtener_indice_legislacion("BOE-A-2005-1154")
    # print(json.dumps(indice, indent=4))

    bloque = obtener_bloque_legislacion("BOE-A-2005-1154", "pr")
    print(json.dumps(bloque, indent=4))
    pass

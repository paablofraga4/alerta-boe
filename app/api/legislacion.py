from fastapi import APIRouter, Query, HTTPException
import requests
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter()

BOE_API_BASE_LEGISLACION = "https://boe.es/datosabiertos/api/legislacion-consolidada"

# 🧱 Esquema Pydantic para normas resumidas
class NormaResumen(BaseModel):
    id: str
    titulo: str
    ambito: str
    departamento: str
    rango: str
    fecha_disposicion: Optional[str] = None
    fecha_publicacion: str
    fecha_vigencia: Optional[str] = None
    estado: str
    vigente: bool
    url_boe: str

# 🧱 Esquema para índice (bloques de artículos)
class BloqueIndice(BaseModel):
    id: str
    titulo: str
    fecha_actualizacion: Optional[str]
    url: str

# 📄 Endpoint para listar normas (listado general con filtros)
@router.get("/legislacion/listado", response_model=List[NormaResumen])
def listar_normas(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    texto: Optional[str] = Query(None, description="Texto libre en título o cuerpo"),
    ambito_codigo: Optional[str] = Query(None),
    desde: Optional[str] = Query(None, description="Desde fecha actualización AAAAMMDD"),
    hasta: Optional[str] = Query(None, description="Hasta fecha actualización AAAAMMDD")
):
    query_payload = {
        "query": {},
        "sort": [{"fecha_actualizacion": "desc"}]
    }

    if texto:
        # Permite usar frases entre comillas
        if '"' in texto:
            condiciones = f"titulo:({texto})"
        else:
            palabras = texto.split()
            condiciones = " AND ".join([f"titulo:{p}" for p in palabras])
        query_payload["query"]["query_string"] = {"query": condiciones}

    params = {
        "limit": limit,
        "offset": offset
    }
    if desde:
        params["from"] = desde
    if hasta:
        params["to"] = hasta

    headers = {"Accept": "application/json"}
    url = f"{BOE_API_BASE_LEGISLACION}"

    if query_payload["query"]:
        import json
        params["query"] = json.dumps(query_payload)

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error en la API del BOE")

    json_data = response.json()
    normas_raw = json_data.get("data", [])

    normas_limpias = []
    for n in normas_raw:
        normas_limpias.append(NormaResumen(
            id=n.get("identificador"),
            titulo=n.get("titulo"),
            ambito=n.get("ambito", {}).get("texto", ""),
            departamento=n.get("departamento", {}).get("texto", ""),
            rango=n.get("rango", {}).get("texto", ""),
            fecha_disposicion=n.get("fecha_disposicion"),
            fecha_publicacion=n.get("fecha_publicacion"),
            fecha_vigencia=n.get("fecha_vigencia"),
            estado=n.get("estado_consolidacion", {}).get("texto", ""),
            vigente=n.get("vigencia_agotada", "N") == "N",
            url_boe=n.get("url_html_consolidada"),
            resumen_tiktok=n.get("resumen_tiktok") or n.get("texto_resumen") or ""
        ))

    return normas_limpias



# 📄 Endpoint para obtener detalles de una norma por ID
@router.get("/legislacion/detalle/{legislation_id}", response_model=NormaResumen)
def obtener_detalle_legislacion(legislation_id: str):
    url = f"{BOE_API_BASE_LEGISLACION}/id/{legislation_id}/metadatos"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="No se encontraron metadatos")

    data = response.json().get("data", [])
    if not data:
        raise HTTPException(status_code=404, detail="Norma no encontrada")

    meta = data[0]
    
    # ✅ fallback si no viene como resumen_tiktok
    resumen = meta.get("resumen_tiktok") or meta.get("texto_resumen") or ""

    return NormaResumen(
        id=meta.get("identificador"),
        titulo=meta.get("titulo"),
        ambito=meta.get("ambito", {}).get("texto", ""),
        departamento=meta.get("departamento", {}).get("texto", ""),
        rango=meta.get("rango", {}).get("texto", ""),
        fecha_disposicion=meta.get("fecha_disposicion"),
        fecha_publicacion=meta.get("fecha_publicacion"),
        fecha_vigencia=meta.get("fecha_vigencia"),
        estado=meta.get("estado_consolidacion", {}).get("texto", ""),
        vigente=meta.get("vigencia_agotada", "N") == "N",
        url_boe=meta.get("url_html_consolidada"),
        resumen_tiktok=resumen  # ✅ incluido en el response
    )

# 📑 Endpoint para obtener el índice (bloques/artículos) de una norma
@router.get("/legislacion/indice/{legislation_id}", response_model=List[BloqueIndice])
def obtener_indice_legislacion(legislation_id: str):
    url = f"{BOE_API_BASE_LEGISLACION}/id/{legislation_id}/texto/indice"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Índice no encontrado")

    data = response.json().get("data", [])
    bloques = data[0].get("bloque", []) if data else []

    return [BloqueIndice(
        id=b["id"],
        titulo=b.get("titulo", ""),
        fecha_actualizacion=b.get("fecha_actualizacion"),
        url=b.get("url")
    ) for b in bloques]

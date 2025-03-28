from fastapi import APIRouter, Query
from app.services.suggest_engine import SuggestionEngine

router = APIRouter()
engine = SuggestionEngine()

@router.get("/suggest")
def sugerir_categoria(q: str = Query(..., min_length=2)):
    sugerencias = engine.sugerir(q)
    if not sugerencias:
        return {"message": f"No se encontraron coincidencias claras para '{q}'."}
    return {"query": q, "sugerencias": sugerencias}

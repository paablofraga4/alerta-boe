from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models import Publication

router = APIRouter()

@router.get("/fecha/{fecha}")
def publicaciones_por_fecha(fecha: str, db: Session = Depends(get_db)):
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(content={"error": "Formato de fecha inválido. Usa YYYY-MM-DD."}, status_code=400)

    publicaciones = db.query(Publication).filter(Publication.date == fecha_obj).all()

    publicaciones_serializadas = []
    for pub in publicaciones:
        publicaciones_serializadas.append({
            "id": pub.id,
            "date": str(pub.date),
            "title": pub.title,
            "body": pub.body,
            "category": list(pub.category) if isinstance(pub.category, (list, tuple)) else [str(pub.category)],
            "extra_tag": pub.extra_tag,  # ✅ NUEVO CAMPO INCLUIDO
            "scope": pub.scope.name if pub.scope else None,
            "departamento": pub.departamento,
            "seccion": pub.seccion,
            "epigrafe": pub.epigrafe,
            "url_html": pub.url_html,
            "url_pdf": pub.url_pdf,
            "pages": pub.pages,
        })

    return JSONResponse(content=publicaciones_serializadas)

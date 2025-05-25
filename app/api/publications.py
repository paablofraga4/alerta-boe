from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import Request

from app.db.session import get_db
from app.db.models import Publication
from app.services.boe_fetcher import fetch_boe_json  # 👈 Asegúrate que esté importado correctamente
from app.db.models import Favorito

router = APIRouter()

@router.get("/fecha/{fecha}")
def publicaciones_por_fecha(fecha: str, db: Session = Depends(get_db)):
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(content={"error": "Formato de fecha inválido. Usa YYYY-MM-DD."}, status_code=400)

    publicaciones = db.query(Publication).filter(Publication.date == fecha_obj).all()

    # ⚡ Si no hay publicaciones, las buscamos en el BOE y guardamos
    if not publicaciones:
        print(f"📡 No había publicaciones en DB para {fecha}, llamando a BOE…")
        fetch_boe_json(fecha.replace("-", ""))  # La función espera formato YYYYMMDD
        publicaciones = db.query(Publication).filter(Publication.date == fecha_obj).all()

    publicaciones_serializadas = []
    for pub in publicaciones:
        publicaciones_serializadas.append({
            "id": pub.id,
            "date": str(pub.date),
            "title": pub.title,
            "body": pub.body,
            "category": list(pub.category) if isinstance(pub.category, (list, tuple)) else [str(pub.category)],
            "extra_tag": pub.extra_tag,
            "scope": pub.scope.name if pub.scope else None,
            "departamento": pub.departamento,
            "seccion": pub.seccion,
            "epigrafe": pub.epigrafe,
            "url_html": pub.url_html,
            "url_pdf": pub.url_pdf,
            "pages": pub.pages,
            "resumen": pub.resumen,
            "resumen_tiktok": pub.resumen_tiktok
        })

    return JSONResponse(content=publicaciones_serializadas)


# POST para marcar una publicación como favorita
@router.post("/favorito/{publication_id}")
def marcar_favorito(publication_id: int, session_id: str, db: Session = Depends(get_db)):
    # Evitar duplicados
    ya_existe = db.query(Favorito).filter_by(session_id=session_id, publication_id=publication_id).first()
    if ya_existe:
        return {"message": "Ya estaba marcado como favorito."}

    fav = Favorito(session_id=session_id, publication_id=publication_id)
    db.add(fav)
    db.commit()
    return {"message": "✅ Publicación marcada como favorita."}

# GET para obtener publicaciones favoritas de un usuario (por sesión)
@router.get("/favoritos/{session_id}")
def obtener_favoritos(session_id: str, db: Session = Depends(get_db)):
    favoritos = db.query(Favorito).filter_by(session_id=session_id).all()
    publicaciones = [f.publication for f in favoritos]

    publicaciones_serializadas = []
    for pub in publicaciones:
        publicaciones_serializadas.append({
            "id": pub.id,
            "date": str(pub.date),
            "title": pub.title,
            "body": pub.body,
            "category": list(pub.category) if isinstance(pub.category, (list, tuple)) else [str(pub.category)],
            "extra_tag": pub.extra_tag,
            "scope": pub.scope.name if pub.scope else None,
            "departamento": pub.departamento,
            "seccion": pub.seccion,
            "epigrafe": pub.epigrafe,
            "url_html": pub.url_html,
            "url_pdf": pub.url_pdf,
            "pages": pub.pages,
            "resumen": pub.resumen,
            "resumen_tiktok": pub.resumen_tiktok
        })

    return JSONResponse(content=publicaciones_serializadas)

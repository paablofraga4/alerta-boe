from app.db.session import SessionLocal
from app.db.models import Publication
from app.services.semantic_search import buscar_similares_por_embedding
from app.services.llm_client import generar_mensaje_asistente
from sqlalchemy import desc

def generar_respuesta_asistente(mensaje_usuario: str, limite=10):
    session = SessionLocal()

    # Cargamos muchas publicaciones recientes para búsqueda semántica
    publicaciones_recientes = session.query(Publication).filter(
        Publication.resumen_tiktok.isnot(None),
        Publication.resumen_tiktok != ""
    ).order_by(desc(Publication.date)).limit(200).all()

    # 🔎 Buscamos las más parecidas por embedding
    publicaciones_similares = buscar_similares_por_embedding(mensaje_usuario, publicaciones_recientes, top_k=limite, modo="consultor_personal")


    # 🧠 Generamos respuesta solo con las top-N
    explicacion = generar_mensaje_asistente(mensaje_usuario, publicaciones_similares)

    session.close()

    # ✅ Empaquetamos las publicaciones para frontend
    return {
        "explicacion": explicacion,
        "publicaciones": [
            {
                "id": p.id,
                "title": p.title,
                "date": p.date.isoformat(),
                "resumen_tiktok": p.resumen_tiktok,
                "extra_tag": p.extra_tag,
                "category": p.category,
                "url_html": p.url_html,
                "departamento": p.departamento,
            } for p in publicaciones_similares
        ]
    }

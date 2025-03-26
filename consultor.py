
from app.services.semantic_search import buscar_similares
from app.db.session import SessionLocal
from app.db.models import Publication
from datetime import datetime
import textwrap

# Número de días hacia atrás para acotar la búsqueda
DIAS_RECIENTES = 60

def obtener_sentencias_recientes(db):
    desde = datetime.today().date() - timedelta(days=DIAS_RECIENTES)
    publicaciones = db.query(Publication).filter(
        Publication.date >= desde,
        Publication.category == "Sentencia"
    ).all()
    return publicaciones

def main():
    db = SessionLocal()
    print("🔎 CONSULTOR INTELIGENTE DE SENTENCIAS")
    consulta = input("Introduce tu consulta (ej: convenio del metal): ").strip()

    publicaciones = obtener_sentencias_recientes(db)

    if not publicaciones:
        print("No hay publicaciones recientes para analizar.")
        return

    textos = [p.title + " " + (p.summary or "") for p in publicaciones]
    similares = buscar_similares(consulta, textos)

    print(f"\n📄 Resultados más relevantes para: '{consulta}'\n")

    for score, idx in similares[:10]:
        pub = publicaciones[idx]
        print(f"📌 {pub.title} ({pub.date})")
        print(f"   Categoría: {pub.category} | Similitud: {score:.2f}")
        print(f"   Resumen: {textwrap.shorten(pub.summary or '', width=200)}\n")

if __name__ == "__main__":
    from datetime import timedelta  # Solo para evitar error de import en main
    main()

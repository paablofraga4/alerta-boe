from app.db.session import SessionLocal
from app.db.models import Publication
from datetime import datetime
import sys

def borrar_publicaciones_por_fecha(fecha: str):
    session = SessionLocal()
    try:
        fecha_obj = datetime.strptime(fecha, "%Y%m%d").date()
        publicaciones = session.query(Publication).filter(Publication.date == fecha_obj).all()
        for pub in publicaciones:
            session.delete(pub)
        session.commit()
        print(f"🗑️ Borradas {len(publicaciones)} publicaciones de la fecha {fecha}.")
    except Exception as e:
        print(f"❌ Error al borrar publicaciones: {e}")
        session.rollback()
    finally:
        session.close()

def borrar_todas_publicaciones():
    session = SessionLocal()
    try:
        total = session.query(Publication).delete()
        session.commit()
        print(f"🧨 Borradas TODAS las publicaciones ({total} registros).")
    except Exception as e:
        print(f"❌ Error al borrar todas las publicaciones: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso:")
        print("  python -m scripts.clear_publications YYYYMMDD    # Borrar por fecha")
        print("  python -m scripts.clear_publications --all       # Borrar TODO")
    elif sys.argv[1] == "--all":
        borrar_todas_publicaciones()
    else:
        borrar_publicaciones_por_fecha(sys.argv[1])

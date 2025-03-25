from app.db.models import Base
from app.db.session import engine

print("⚠️ ATENCIÓN: eliminando tabla 'publications'...")
Base.metadata.drop_all(bind=engine)
print("✅ Tabla eliminada.")

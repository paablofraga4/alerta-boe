from app.db.models import Base
from app.db.session import engine

print("⏳ Creando tablas en la base de datos...")
Base.metadata.create_all(bind=engine)
print("✅ ¡Tablas creadas con éxito!")

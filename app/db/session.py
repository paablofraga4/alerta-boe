from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 📦 Cargar la URL de la base de datos desde la configuración
DATABASE_URL = settings.DATABASE_URL

# ⚙️ Crear el engine
engine = create_engine(DATABASE_URL)

# 🧪 Crear el sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 📐 Base para los modelos
Base = declarative_base()

# ✅ Función de utilidad para inyectar la DB en endpoints de FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

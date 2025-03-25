import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    BOE_API_URL: str = os.getenv("BOE_API_URL", "https://www.boe.es/diario_boe/xml.php")

settings = Settings()

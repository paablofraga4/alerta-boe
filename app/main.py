from fastapi import FastAPI
from app.api.publications import router as publications_router

print("✅ ESTE ES EL main.py REAL")

app = FastAPI(
    title="AlertaBOE",
    description="API para consultar y clasificar publicaciones del BOE por fecha",
    version="1.0.0"
)

app.include_router(publications_router, prefix="/publicaciones", tags=["Publicaciones"])


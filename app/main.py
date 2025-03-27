from fastapi import FastAPI
from app.api.publications import router as publications_router

app = FastAPI(
    title="AlertaBOE",
    description="API para consultar y clasificar publicaciones del BOE por fecha",
    version="1.0.0"
)

# ✅ API en español
app.include_router(publications_router, prefix="/publicaciones", tags=["Publicaciones"])

# Debug de rutas registradas
for route in app.router.routes:
    print(f"🔍 Ruta activa: {route.path}")

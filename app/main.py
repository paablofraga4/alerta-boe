from fastapi import FastAPI
from app.api.publications import router as publications_router
from app.api.legislacion import router as legislacion_router
from app.api import suggest

app = FastAPI(
    title="AlertaBOE",
    description="API para consultar y clasificar publicaciones del BOE por fecha",
    version="1.0.0"
)

# 🔗 Registro de routers
app.include_router(publications_router, prefix="/publicaciones", tags=["Publicaciones"])
app.include_router(legislacion_router, prefix="/legislacion", tags=["Legislación"])  # 👈 NUEVO
app.include_router(suggest.router, prefix="/api")

# Debug opcional
for route in app.router.routes:
    print(f"🔍 Ruta activa: {route.path}")





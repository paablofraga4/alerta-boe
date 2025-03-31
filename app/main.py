from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 👈 Añadir esto

from app.api.publications import router as publications_router
from app.api.legislacion import router as legislacion_router
from app.api import suggest
from app.api import chat

app = FastAPI(
    title="AlertaBOE",
    description="API para consultar y clasificar publicaciones del BOE por fecha",
    version="1.0.0"
)

# 🛡️ Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod: cambiar por el dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔗 Registro de routers
app.include_router(publications_router, prefix="/publicaciones", tags=["Publicaciones"])
app.include_router(legislacion_router, prefix="/legislacion", tags=["Legislación"])
app.include_router(suggest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# Debug opcional
for route in app.router.routes:
    print(f"🔍 Ruta activa: {route.path}")

from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class LegislacionOut(BaseModel):
    legislation_id: str
    title: str
    rango: str
    departamento: str
    fecha_publicacion: date
    fecha_ultima_version: date
    estado_consolidacion: str
    materias: Optional[str]
    ambito: Optional[str]
    url_html: Optional[str]

    class Config:
        orm_mode = True


# 👉 Para /legislacion/listado y /detalle
class NormaResumen(BaseModel):
    id: str
    titulo: str
    ambito: str
    departamento: str
    rango: str
    fecha_disposicion: Optional[str] = None
    fecha_publicacion: str
    fecha_vigencia: Optional[str] = None
    estado: str
    vigente: bool
    url_boe: str
    url_eli: Optional[str] = None


# 👉 Para /legislacion/indice
class BloqueIndice(BaseModel):
    id: str
    titulo: str
    fecha_actualizacion: str
    url: str

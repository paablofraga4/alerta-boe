from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

class PublicationOut(BaseModel):
    id: int
    date: date
    title: str
    body: str
    category: str
    scope: str

    # Campos nuevos
    boe_id: Optional[str]
    departamento: Optional[str]
    seccion: Optional[str]
    epigrafe: Optional[str]
    url_html: Optional[str]
    url_pdf: Optional[str]
    pages: Optional[int]

    model_config = ConfigDict(from_attributes=True)  # 🔁 reemplaza orm_mode

from pydantic import BaseModel
from typing import Optional
from datetime import date

class PublicationOut(BaseModel):
    id: int
    date: date
    title: str
    body: Optional[str]
    category: Optional[str]
    scope: Optional[str]  # Solo el nombre del ámbito
    departamento: Optional[str]
    seccion: Optional[str]
    epigrafe: Optional[str]
    url_html: Optional[str]
    url_pdf: Optional[str]
    pages: Optional[int]

    class Config:
        orm_mode = True

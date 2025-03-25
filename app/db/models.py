from sqlalchemy import Column, Integer, String, Date
from app.db.session import Base

class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    title = Column(String)
    body = Column(String)
    category = Column(String)
    scope = Column(String)

    # 🆕 Campos nuevos
    boe_id = Column(String, unique=True, index=True)
    departamento = Column(String)
    seccion = Column(String)
    epigrafe = Column(String)
    url_html = Column(String)
    url_pdf = Column(String)
    pages = Column(Integer)

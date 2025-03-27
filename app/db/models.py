from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.session import Base

# 🧩 Tabla intermedia
publication_region_table = Table(
    "publication_regions",
    Base.metadata,
    Column("publication_id", Integer, ForeignKey("publications.id")),
    Column("region_id", Integer, ForeignKey("regions.id"))
)

class Scope(Base):
    __tablename__ = "scopes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    publications = relationship("Publication", back_populates="scope")

class Region(Base):
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True)

    publications = relationship("Publication", secondary=publication_region_table, back_populates="regions")

class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    title = Column(String)
    body = Column(String)
    category = Column(String)
    extra_tag = Column(String, nullable=True)  # ✅ NUEVO CAMPO

    scope_id = Column(Integer, ForeignKey("scopes.id"))
    scope = relationship("Scope", back_populates="publications")

    regions = relationship("Region", secondary=publication_region_table, back_populates="publications")

    boe_id = Column(String, unique=True, index=True)
    departamento = Column(String)
    seccion = Column(String)
    epigrafe = Column(String)
    url_html = Column(String)
    url_pdf = Column(String)
    pages = Column(Integer)

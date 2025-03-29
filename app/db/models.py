from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
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

    # ✅ CAMBIO: ahora es una lista de categorías
    category = Column(ARRAY(String))

    extra_tag = Column(String, nullable=True)

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

    # 🧠 OPCIONAL: embedding vectorial para búsqueda semántica
    # embedding = Column(Vector(384))

# 🆕 Legislación consolidada
class Legislacion(Base):
    __tablename__ = "legislaciones"

    id = Column(Integer, primary_key=True, index=True)
    legislation_id = Column(String, unique=True, index=True)  # ID oficial del BOE
    title = Column(String)
    rango = Column(String)
    departamento = Column(String)
    fecha_publicacion = Column(Date)
    fecha_ultima_version = Column(Date)
    estado_consolidacion = Column(String)
    materias = Column(String)  # CSV de materias
    ambito = Column(String)
    texto_completo = Column(String, nullable=True)
    indice = Column(String, nullable=True)
    resumen = Column(String, nullable=True)
    url_html = Column(String)

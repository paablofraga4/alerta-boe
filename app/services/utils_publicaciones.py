from sqlalchemy.orm import Session
from app.db.models import Publication

def extraer_categorias_unicas(db: Session) -> list[str]:
    """
    Devuelve todas las categorías únicas (aplanadas y sin duplicados) de la base de datos.
    """
    categorias_flat = []
    resultados = db.query(Publication.category).all()
    
    for row in resultados:
        lista = row[0]
        if isinstance(lista, list):
            categorias_flat.extend(lista)

    # Limpiar y quitar duplicados
    categorias_limpias = {c.strip() for c in categorias_flat if c and isinstance(c, str)}
    return sorted(categorias_limpias)

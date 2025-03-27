import re
import spacy
from sentence_transformers import SentenceTransformer, util

# Cargamos modelos
model = SentenceTransformer("all-MiniLM-L6-v2")
nlp = spacy.load("es_core_news_md")

# Regex para categorías base
CATEGORIAS_REGEX = [
    (r"\bsubvencione?s?\b|\bayudas?\b|\bfondos europeos\b", "Subvención"),
    (r"\bnombramiento?s?\b|\bdesignaci[oó]n\b|\bdestinos?\b|\bceses?\b|\bsituaciones?\b", "Empleo público"),
    (r"\boposiciones?\b|\bconcurso\b|\bbolsa de trabajo\b|\bprocedimiento de selecci[oó]n\b", "Empleo público"),
    (r"\bconvenios?\b|\bacuerdos internacionales?\b|\bcolaboraci[oó]n\b", "Convenio"),
    (r"\bsanciones?\b|\bmulta?s?\b|\bexpediente sancionador\b", "Sanción"),
    (r"\bsentencia\b|\btribunal\b|\bresoluci[oó]n judicial\b|\bjuzgado\b", "Sentencia"),
    (r"\bnormas?\b|\breglamentos?\b|\bleyes?\b|\bestatutos?\b|\breformas?\b", "Norma"),
    (r"\bplanes de estudios?\b|\benseñanza\b|\beducaci[oó]n\b|\bcursos\b|\bbecas?\b", "Educación"),
    (r"\bsalud\b|\bservicio(s)? de salud\b|\bespecialidades sanitarias\b", "Sanidad"),
    (r"\bmedio ambiente\b|\bimpacto ambiental\b|\bresiduos?\b|\benerg[ií]a renovable\b", "Medio ambiente"),
    (r"\bpresupuestos?\b|\bdeuda\b|\bimpuestos?\b|\bmercado de valores\b", "Economía"),
    (r"\binfraestructura(s)?\b|\btransporte\b|\bobras p[úu]blicas\b|\bcarreteras?\b", "Infraestructura"),
    (r"\bagricultura\b|\bganado\b|\bpesca\b|\bvit[ií]cola\b|\bPAC\b", "Agroalimentario"),
    (r"\btelecomunicaciones\b|\btelevisi[oó]n\b|\bTIC\b|\bdigital\b", "Tecnología"),
    (r"\bjusticia\b|\bprocedimientos judiciales?\b|\bletrados?\b", "Justicia"),
    (r"\bseguridad\b|\bdefensa\b|\bFuerzas Armadas\b", "Seguridad"),
    (r"\bbienes de inter[eé]s cultural\b|\bcultura\b|\bpatrimonio\b", "Cultura"),
    (r"\bigualdad\b|\bdiversidad\b|\binclusi[oó]n\b|\bdiscapacidad\b", "Asuntos sociales"),
    (r"\bempresas?\b|\baut[oó]nomos?\b|\bcomercio\b|\bemprendimiento\b", "Empresa y comercio"),
]

def clasificar_categoria_por_regex(texto: str) -> str:
    texto = texto.lower()
    for patron, categoria in CATEGORIAS_REGEX:
        if re.search(patron, texto):
            return categoria
    return "Otro"

# 🔍 NUEVO: Etiqueta contextual usando NLP gratuito con spaCy
def extra_tag_por_contexto(texto: str) -> str:
    texto = texto.lower()
    doc = nlp(texto)
    tokens = [t.text for t in doc]

    if "autónomo" in tokens or "autónomos" in tokens:
        return "Autónomos"
    if "empresa" in tokens or "pymes" in tokens or "comercio" in tokens:
        return "Empresas"
    if "educación" in tokens or "docente" in tokens or "profesor" in tokens:
        return "Educación"
    if "universidad" in tokens or "beca" in tokens:
        return "Universidad"
    if "salud" in tokens or "hospital" in tokens or "sanitario" in tokens:
        return "Sanidad"
    if "digital" in tokens or "tecnología" in tokens or "tic" in tokens:
        return "Digitalización"
    if any("tribunal" in t or "juzgado" in t for t in tokens):
        return "Justicia"
    
    return None

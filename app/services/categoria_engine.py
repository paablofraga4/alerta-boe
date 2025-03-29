import re
from typing import List
from sentence_transformers import SentenceTransformer, util
from app.services.utils_categoria_semantica import convertir_categorias_para_embeddings

# Modelo semántico
model = SentenceTransformer("all-MiniLM-L6-v2")

# Regex base (puedes extenderla si quieres mantenerla)
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

def clasificar_por_regex(texto: str) -> List[str]:
    texto = texto.lower()
    categorias = []
    for patron, categoria in CATEGORIAS_REGEX:
        if re.search(patron, texto) and categoria not in categorias:
            categorias.append(categoria)
    return categorias

# --- SEMÁNTICA ---
# Leemos frases desde tu archivo
CATEGORIAS_SEMANTICAS = convertir_categorias_para_embeddings("vectorstore/categorias_semanticas.json")

# Preprocesamos embeddings
categorias_embed = {
    nombre: model.encode(frase, convert_to_tensor=True)
    for nombre, frase in CATEGORIAS_SEMANTICAS.items()
}

def clasificar_por_semantica(texto: str, threshold=0.60) -> List[str]:
    texto_embed = model.encode(texto, convert_to_tensor=True)
    categorias_detectadas = []
    for nombre, emb_ref in categorias_embed.items():
        sim = util.cos_sim(texto_embed, emb_ref).item()
        if sim >= threshold:
            categorias_detectadas.append(nombre)
    return categorias_detectadas

# --- COMBINADOR ---
def clasificar_publicacion(texto: str) -> List[str]:
    regex_cats = clasificar_por_regex(texto)
    semantic_cats = clasificar_por_semantica(texto)
    return list(set(regex_cats + semantic_cats)) or ["Otro"]

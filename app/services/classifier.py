from sentence_transformers import SentenceTransformer, util
import re

# Cargamos modelo preentrenado
model = SentenceTransformer("all-MiniLM-L6-v2")

CATEGORIAS_REGEX = [
    # Subvenciones y ayudas
    (r"\bsubvencione?s?\b|\bayudas?\b|\bfondos europeos\b", "Subvención"),

    # Empleo público y personal
    (r"\bnombramiento?s?\b|\bdesignaci[oó]n\b|\bdestinos?\b|\bceses?\b|\bsituaciones?\b", "Empleo público"),
    (r"\boposiciones?\b|\bconcurso\b|\bbolsa de trabajo\b|\bprocedimiento de selecci[oó]n\b", "Empleo público"),

    # Convenios y acuerdos
    (r"\bconvenios?\b|\bacuerdos internacionales?\b|\bcolaboraci[oó]n\b", "Convenio"),

    # Sanciones
    (r"\bsanciones?\b|\bmulta?s?\b|\bexpediente sancionador\b", "Sanción"),

    # Sentencias y resoluciones judiciales
    (r"\bsentencia\b|\btribunal\b|\bresoluci[oó]n judicial\b|\bjuzgado\b", "Sentencia"),

    # Normas, leyes y reglamentos
    (r"\bnormas?\b|\breglamentos?\b|\bleyes?\b|\bestatutos?\b|\breformas?\b", "Norma"),

    # Educación y universidades
    (r"\bplanes de estudios?\b|\benseñanza\b|\beducaci[oó]n\b|\bcursos\b|\bbecas?\b", "Educación"),

    # Sanidad y salud
    (r"\bsalud\b|\bservicio(s)? de salud\b|\bespecialidades sanitarias\b", "Sanidad"),

    # Medio ambiente y sostenibilidad
    (r"\bmedio ambiente\b|\bimpacto ambiental\b|\bresiduos?\b|\benerg[ií]a renovable\b", "Medio ambiente"),

    # Economía, deuda, presupuestos
    (r"\bpresupuestos?\b|\bdeuda\b|\bimpuestos?\b|\bmercado de valores\b", "Economía"),

    # Infraestructuras y transporte
    (r"\binfraestructura(s)?\b|\btransporte\b|\bobras p[úu]blicas\b|\bcarreteras?\b", "Infraestructura"),

    # Agricultura y sector primario
    (r"\bagricultura\b|\bganado\b|\bpesca\b|\bvit[ií]cola\b|\bPAC\b", "Agroalimentario"),

    # Tecnología y digitalización
    (r"\btelecomunicaciones\b|\btelevisi[oó]n\b|\bTIC\b|\bdigital\b", "Tecnología"),

    # Justicia y legal
    (r"\bjusticia\b|\bprocedimientos judiciales?\b|\bletrados?\b", "Justicia"),

    # Seguridad y defensa
    (r"\bseguridad\b|\bdefensa\b|\bFuerzas Armadas\b", "Seguridad"),

    # Cultura y patrimonio
    (r"\bbienes de inter[eé]s cultural\b|\bcultura\b|\bpatrimonio\b", "Cultura"),

    # Igualdad, diversidad, inclusión
    (r"\bigualdad\b|\bdiversidad\b|\binclusi[oó]n\b|\bdiscapacidad\b", "Asuntos sociales"),

    # Comercio y empresas
    (r"\bempresas?\b|\baut[oó]nomos?\b|\bcomercio\b|\bemprendimiento\b", "Empresa y comercio"),
]


def clasificar_categoria_por_regex(texto: str) -> str:
    texto = texto.lower()
    for patron, categoria in CATEGORIAS_REGEX:
        if re.search(patron, texto):
            return categoria
    return "Otro"

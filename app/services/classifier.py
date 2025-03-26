from sentence_transformers import SentenceTransformer, util

# Cargamos modelo preentrenado
model = SentenceTransformer("all-MiniLM-L6-v2")

categorias = {
    "Subvención": (
        "Publicaciones relacionadas con ayudas económicas procedentes de entidades públicas. "
        "Incluyen convocatorias para subvenciones, programas de incentivos, ayudas a la digitalización, "
        "eficiencia energética, internacionalización o contratación. Muy relevantes para pequeñas empresas "
        "y autónomos que busquen financiación externa o apoyo institucional."
    ),

    "Convenio colectivo": (
        "Documentos que recogen acuerdos entre representantes sindicales y empleadores. "
        "Regulan condiciones laborales como salarios, jornadas, vacaciones, categorías profesionales o permisos. "
        "Pueden afectar a sectores completos o empresas concretas, y suelen tener efecto retroactivo."
    ),

    "Sentencia": (
        "Resoluciones judiciales emitidas por tribunales u órganos administrativos. "
        "Incluyen fallos, autos o recursos con efectos legales. Pueden afectar a procedimientos sancionadores, "
        "contratos públicos, situaciones fiscales o responsabilidades empresariales."
    ),

    "Norma": (
        "Leyes, decretos, reglamentos u órdenes ministeriales que crean o modifican obligaciones legales. "
        "Estas normas pueden tener impacto directo sobre trámites, impuestos, licencias, seguridad laboral, "
        "protección de datos u otros aspectos de cumplimiento normativo."
    ),

    "Empleo público": (
        "Convocatorias de plazas en administraciones públicas: oposiciones, concursos, bolsas de trabajo, etc. "
        "Incluye también resoluciones de nombramientos, listados de admitidos/excluidos y calendarios de pruebas. "
        "Útil para quienes buscan trabajo en el sector público o prestan servicios a él."
    ),

    "Nombramiento": (
        "Anuncios de designación, cese o renovación de cargos públicos: directores generales, jueces, vocales, "
        "inspectores, etc. Estos cambios pueden tener relevancia si afectan a órganos que regulan tu actividad "
        "o sector (ej. Agencia Tributaria, CNMC, ICEX…)."
    ),

    "Universidades": (
        "Información relativa a universidades públicas o privadas: convocatorias de plazas de profesorado, "
        "resoluciones de rectorado, normativas internas o becas específicas. Especialmente relevante si tu actividad "
        "está relacionada con formación, investigación o colaboraciones institucionales."
    ),

    "Sanción": (
        "Resoluciones sancionadoras o disciplinarias por parte de la administración. "
        "Incluye multas, expedientes, inhabilitaciones o cierres temporales. Pueden ser por incumplimientos laborales, "
        "ambientales, fiscales o de contratación pública. Muy importante para conocer riesgos o precedentes."
    ),

    "Otro": (
        "Contenido no categorizado o con bajo impacto directo. Puede tratarse de anuncios formales, rectificaciones, "
        "modificaciones menores o comunicaciones sin implicaciones legales o económicas claras."
    )
}




# Preprocesar las descripciones una sola vez
categoria_embeddings = {
    cat: model.encode(desc, convert_to_tensor=True) for cat, desc in categorias.items()
}

def classify_with_ai(text: str) -> str:
    if not text:
        return "otro"

    text_embedding = model.encode(text, convert_to_tensor=True)

    # Calculamos similitud coseno con cada categoría
    scores = {
        cat: float(util.cos_sim(text_embedding, emb))
        for cat, emb in categoria_embeddings.items()
    }

    mejor_categoria = max(scores, key=scores.get)
    return mejor_categoria



# def classify_text(text: str) -> str:
#     text = text.lower()

#     if any(word in text for word in ["subvención", "ayuda", "convocatoria", "financiación"]):
#         return "Subvención"
#     elif any(word in text for word in ["sanción", "infracción", "multa", "expediente"]):
#         return "Sanción"
#     elif any(word in text for word in ["ley", "real decreto", "normativa", "reglamento", "modificación"]):
#         return "Norma"
#     elif any(word in text for word in ["presupuesto", "impuesto", "tributo", "ejercicio económico"]):
#         return "Presupuesto"
#     elif any(word in text for word in ["oposición", "concurso", "plazas", "convocatoria de empleo"]):
#         return "Empleo público"
#     elif any(word in text for word in ["nombramiento", "cese", "designación", "resolución de nombramiento"]):
#         return "Nombramiento"
#     elif "universidad" in text or "catedrático" in text or "profesor titular" in text:
#         return "Universidades"
#     elif any(word in text for word in ["medio ambiente", "sostenibilidad", "ordenación del territorio"]):
#         return "Medio ambiente"
#     else:
#         return "Otro"

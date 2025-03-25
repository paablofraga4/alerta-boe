from sentence_transformers import SentenceTransformer, util

# Cargamos modelo preentrenado
model = SentenceTransformer("all-MiniLM-L6-v2")

# Definimos las categorías y sus descripciones (puedes afinar esto)
categorias = {
    "Subvención": "Publicaciones relacionadas con ayudas económicas, subvenciones, incentivos financieros o convocatorias públicas para empresas, autónomos o entidades.",
    
    "Convenio colectivo": "Documentos que recogen acuerdos laborales entre representantes de trabajadores y empleadores, incluyendo condiciones de trabajo, salarios y jornadas.",

    "Sentencia": "Resoluciones judiciales firmes emitidas por tribunales, incluyendo fallos, autos y decisiones que afectan a personas físicas o jurídicas.",

    "Norma": "Leyes, reglamentos, decretos u otras disposiciones de carácter normativo que modifican o establecen nuevas obligaciones legales.",

    "Empleo público": "Convocatorias de oposiciones, concursos públicos, bolsas de empleo o plazas ofertadas en administraciones públicas o instituciones oficiales.",

    "Nombramiento": "Anuncios oficiales de designación o cese de personas en cargos públicos, administrativos, judiciales o institucionales.",

    "Universidades": "Publicaciones relacionadas con el ámbito universitario, como plazas docentes, nombramientos académicos o resoluciones de rectorado.",

    "Sanción": "Disposiciones relacionadas con expedientes sancionadores, multas administrativas, infracciones o penalizaciones legales.",

    "Otro": "Contenido no encuadrado en ninguna de las categorías anteriores o que no contiene información relevante directa para el usuario."
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

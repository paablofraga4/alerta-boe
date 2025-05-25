from sentence_transformers import SentenceTransformer, util

# Cargar modelo local gratuito (rápido y potente)
model = SentenceTransformer("all-MiniLM-L6-v2")

def buscar_similares_por_embedding(query_text, publicaciones, top_k=5, modo="consultor_inteligente"):
    """
    Devuelve las publicaciones más similares a una búsqueda libre usando embeddings.

    Parámetros:
      - query_text: texto de la consulta.
      - publicaciones: lista de publicaciones, ya sea como diccionarios (para consultor_inteligente)
                       o como objetos (para consultor_personal).
      - top_k: número máximo de resultados a devolver.
      - modo: "consultor_inteligente" (usa pub.get("title", "")) o "consultor_personal" (usa pub.title).
    """
    if not publicaciones or not query_text:
        return []

    # Ajustar top_k al número de publicaciones disponibles
    top_k = min(top_k, len(publicaciones))
    if top_k == 0:
        return []

    # Embedding de la búsqueda
    query_embedding = model.encode(query_text, convert_to_tensor=True)

    # Extraer títulos según el modo
    if modo == "consultor":
        titulos_consultor_inteligente = [pub.get("title", "") for pub in publicaciones]
        titulos = titulos_consultor_inteligente
    elif modo == "asistente":
        titulos_consultor_personal = [pub.title or "" for pub in publicaciones]
        titulos = titulos_consultor_personal
    else:
        # Por defecto, intenta detectar el tipo del primer elemento
        if publicaciones and isinstance(publicaciones[0], dict):
            titulos = [pub.get("title", "") for pub in publicaciones]
        else:
            titulos = [pub.title or "" for pub in publicaciones]

    # Obtener embeddings de títulos
    embeddings_pub = model.encode(titulos, convert_to_tensor=True)

    # Calcular similitud y obtener los índices de los mejores resultados
    similitudes = util.cos_sim(query_embedding, embeddings_pub)[0]
    top_indices = similitudes.topk(top_k).indices.tolist()

    # Devolver publicaciones ordenadas según la similitud
    return [publicaciones[i] for i in top_indices]

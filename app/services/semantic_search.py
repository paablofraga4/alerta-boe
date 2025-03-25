from sentence_transformers import SentenceTransformer, util

# Cargar modelo local gratuito (rápido y potente)
model = SentenceTransformer("all-MiniLM-L6-v2")

def buscar_similares(query_text, publicaciones, top_k=5):
    """
    Devuelve las publicaciones más similares a una búsqueda libre usando embeddings.
    """
    if not publicaciones or not query_text:
        return []

    # Embedding de la búsqueda
    query_embedding = model.encode(query_text, convert_to_tensor=True)

    # Embeddings de títulos del BOE
    titulos = [pub.get("title", "") for pub in publicaciones]
    embeddings_pub = model.encode(titulos, convert_to_tensor=True)

    # Calcular similitud
    similitudes = util.cos_sim(query_embedding, embeddings_pub)[0]
    top_indices = similitudes.topk(top_k).indices.tolist()

    # Devolver publicaciones ordenadas por similitud
    resultados = [publicaciones[i] for i in top_indices]
    return resultados

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os

# Ruta al JSON original agrupado
ORIGEN_JSON = "vectorstore/categorias_semanticas.json"
FLATTENED_JSON = "vectorstore/flat_categorias.json"
INDEX_PATH = "vectorstore/faiss_index.index"

# Cargar estructura agrupada
with open(ORIGEN_JSON, "r", encoding="utf-8") as f:
    agrupado = json.load(f)

# Aplanar
flat_categorias = []
for grupo, items in agrupado.items():
    for item in items:
        flat_categorias.append({
            "grupo": grupo,
            "title": item["title"],
            "keywords": item["keywords"]
        })

# Crear embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
textos = [item["keywords"] for item in flat_categorias]
vectors = model.encode(textos, normalize_embeddings=True)

# Crear índice FAISS
index = faiss.IndexFlatIP(vectors.shape[1])
index.add(np.array(vectors))

# Guardar resultados
os.makedirs("vectorstore", exist_ok=True)
faiss.write_index(index, INDEX_PATH)
with open(FLATTENED_JSON, "w", encoding="utf-8") as f:
    json.dump(flat_categorias, f, ensure_ascii=False, indent=2)

print("✅ Índice y metadatos generados correctamente.")

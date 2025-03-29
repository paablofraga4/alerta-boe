import json

def convertir_categorias_para_embeddings(path: str) -> dict[str, str]:
    """
    Convierte el JSON jerárquico de categorías en frases representativas para embeddings.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultado = {}

    for grupo, items in data.items():
        for item in items:
            nombre = item.get("title")
            keywords = item.get("keywords", [])
            if not nombre or not keywords:
                continue
            frase = f"{nombre}: " + ", ".join(keywords)
            resultado[nombre] = frase

    return resultado

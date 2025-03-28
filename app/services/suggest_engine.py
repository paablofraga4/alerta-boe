import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer

# NLTK para entender mejor el lenguaje
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Descargamos los recursos de NLTK por si acaso
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")

class SuggestionEngine:
    def __init__(self, index_path="vectorstore/faiss_index.index", metadata_path="vectorstore/flat_categorias.json"):
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError("Faltan el índice o los metadatos.")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.read_index(index_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.categorias = json.load(f)

        # Configuración de NLTK
        self.stop_words = set(stopwords.words("spanish"))
        self.lemmatizer = WordNetLemmatizer()

    def limpiar_texto(self, texto):
        """Procesa el texto: quita palabras vacías y normaliza las palabras"""
        tokens = word_tokenize(texto.lower())
        return set(
            self.lemmatizer.lemmatize(t)
            for t in tokens
            if t.isalpha() and t not in self.stop_words
        )

    def sugerir(self, query: str, top_k=5, threshold=0.45):
        """Hace la búsqueda semántica, pero además filtra con análisis del lenguaje"""
        vec = self.model.encode([query], normalize_embeddings=True)
        D, I = self.index.search(np.array(vec), top_k)

        palabras_usuario = self.limpiar_texto(query)
        sugerencias = []

        for score, idx in zip(D[0], I[0]):
            if score > threshold:
                categoria = self.categorias[idx]
                palabras_categoria = self.limpiar_texto(categoria["keywords"])

                # Solo la aceptamos si comparten al menos una palabra
                if palabras_usuario & palabras_categoria:
                    sugerencias.append({
                        "title": categoria["title"],
                        "grupo": categoria["grupo"],
                        "score": round(float(score), 3)
                    })

        return sugerencias

"""
Embeddings alternativos para ambientes Streamlit
"""

import hashlib
from typing import List

from sentence_transformers import SentenceTransformer


class StreamlitSafeEmbeddings:
    """
    Embeddings seguros para Streamlit usando sentence-transformers
    Como fallback se GoogleGenerativeAI falha
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializar con modelo sentence-transformers

        Args:
            model_name: Nombre del modelo de sentence-transformers
        """
        self.model_name = model_name
        self._model = None
        self._cache = {}

    def _get_model(self):
        """Lazy loading del modelo"""
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"Error loading sentence-transformers model: {e}")
                # Fallback a embeddings dummy
                self._model = None
        return self._model

    def _get_cache_key(self, text: str) -> str:
        """Generar clave de cache para el texto"""
        return hashlib.md5(text.encode()).hexdigest()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed lista de documentos"""
        model = self._get_model()

        if model is None:
            # Fallback: embeddings dummy
            return [[0.0] * 384 for _ in texts]

        try:
            # Verificar cache primero
            embeddings = []
            texts_to_embed = []
            indices_to_embed = []

            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                if cache_key in self._cache:
                    embeddings.append(self._cache[cache_key])
                else:
                    embeddings.append(None)
                    texts_to_embed.append(text)
                    indices_to_embed.append(i)

            # Embedder textos no cacheados
            if texts_to_embed:
                new_embeddings = model.encode(texts_to_embed, convert_to_numpy=True)
                for idx, text_idx in enumerate(indices_to_embed):
                    embedding = new_embeddings[idx].tolist()
                    embeddings[text_idx] = embedding
                    # Guardar en cache
                    cache_key = self._get_cache_key(texts_to_embed[idx])
                    self._cache[cache_key] = embedding

            return embeddings

        except Exception as e:
            print(f"Error in embed_documents: {e}")
            return [[0.0] * 384 for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed consulta única"""
        return self.embed_documents([text])[0]

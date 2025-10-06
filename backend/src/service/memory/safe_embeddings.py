import os
from typing import List

from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer


class SafeEmbeddings(Embeddings):
    def __init__(
        self, model_name: str = "keepitreal/vietnamese-sbert", device: str = None
    ):
        self.model_name = model_name
        self.model = SentenceTransformer(
            os.environ.get("EMBEDDING_MODEL", r"keepitreal/vietnamese-sbert")
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(
            texts, convert_to_numpy=False, show_progress_bar=False
        ).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode(
            text, convert_to_numpy=False, show_progress_bar=False
        ).tolist()

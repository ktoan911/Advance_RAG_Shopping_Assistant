"""
Safe wrapper cho GoogleGenerativeAIEmbeddings để tránh event loop issues
"""

import asyncio
import threading
from typing import List

from langchain.embeddings.base import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .fallback_embeddings import StreamlitSafeEmbeddings


class SafeGoogleGenerativeAIEmbeddings(Embeddings):
    """
    Wrapper an toàn cho GoogleGenerativeAIEmbeddings
    Tự động xử lý event loop issues trong môi trường Streamlit
    Có fallback sang sentence-transformers nếu Google API fails
    Kế thừa từ LangChain Embeddings để tương thích
    """

    def __init__(self, model: str, google_api_key: str):
        super().__init__()
        self.model = model
        self.google_api_key = google_api_key
        self._embeddings = None
        self._fallback_embeddings = None
        self._lock = threading.Lock()
        self._use_fallback = False

    def _get_embeddings(self):
        """Lazy initialization của embeddings"""
        if self._embeddings is None and not self._use_fallback:
            with self._lock:
                if self._embeddings is None and not self._use_fallback:
                    try:
                        self._embeddings = GoogleGenerativeAIEmbeddings(
                            model=self.model, google_api_key=self.google_api_key
                        )
                    except Exception as e:
                        print(f"Failed to initialize Google embeddings: {e}")
                        self._use_fallback = True

        if self._use_fallback and self._fallback_embeddings is None:
            with self._lock:
                if self._fallback_embeddings is None:
                    self._fallback_embeddings = StreamlitSafeEmbeddings()

        return self._embeddings if not self._use_fallback else self._fallback_embeddings

    def _run_in_thread(self, func, *args, **kwargs):
        """Chạy function trong thread riêng với event loop mới"""
        result = {}
        exception = {}

        def target():
            try:
                # Tạo event loop mới cho thread này
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Chạy function
                result["value"] = func(*args, **kwargs)

                # Đóng loop
                loop.close()
            except Exception as e:
                exception["error"] = e

        thread = threading.Thread(target=target)
        thread.start()
        thread.join()

        if "error" in exception:
            raise exception["error"]

        return result["value"]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed list of documents"""
        try:
            embeddings = self._get_embeddings()

            if self._use_fallback:
                # Sử dụng fallback embeddings
                return embeddings.embed_documents(texts)
            else:
                # Sử dụng Google embeddings với thread safety
                return self._run_in_thread(embeddings.embed_documents, texts)

        except Exception as e:
            print(f"Error in embed_documents: {e}")
            # Switch to fallback
            self._use_fallback = True
            if self._fallback_embeddings is None:
                self._fallback_embeddings = StreamlitSafeEmbeddings()
            return self._fallback_embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed single query"""
        try:
            embeddings = self._get_embeddings()

            if self._use_fallback:
                # Sử dụng fallback embeddings
                return embeddings.embed_query(text)
            else:
                # Sử dụng Google embeddings với thread safety
                return self._run_in_thread(embeddings.embed_query, text)

        except Exception as e:
            print(f"Error in embed_query: {e}")
            # Switch to fallback
            self._use_fallback = True
            if self._fallback_embeddings is None:
                self._fallback_embeddings = StreamlitSafeEmbeddings()
            return self._fallback_embeddings.embed_query(text)

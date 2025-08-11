from __future__ import annotations

import os
import re
import sys

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.common.logger import get_logger
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from src.service.sematic_router import (
    ChitchatProdcutsSentimentRoute,
    SemanticRouter,
)

load_dotenv()
logger = get_logger(__name__)

# load the embedding model
embedding_model = SentenceTransformer(os.environ.get("EMBEDDING_MODEL", r'keepitreal/vietnamese-sbert'))

chitchat_prodcuts_sentiment_route = ChitchatProdcutsSentimentRoute()
senmatic_router = SemanticRouter(embedding_model)

embedding_routes = chitchat_prodcuts_sentiment_route.get_json_routesEmbedding(
    path=r"Embedding/routesEmbedding.json",
)


class TextProcessor:
    def process_history(self, history: list[dict]) -> str:
        result = ""
        for message in history:
            result += f"{message['role']}: {message['content']}\n"
        return result.strip()

    def process_query(self, text: str) -> str:
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip().lower()

    def _get_infomation(self, text, prompt):
        text = text.replace("\n", ".")
        if text:
            return f"{prompt} {text}.\n"
        else:
            return ""

    def transform_query(self, db_information: list) -> str:
        results = []
        for _, result in enumerate(db_information):
            title = result.get("title", "N/A")
            product_promotion = result.get("product_promotion", "N/A")
            product_specs = result.get("product_specs", "N/A")
            current_price = (
                result.get("current_price", "N/A")
                if result.get(
                    "current_price",
                    "N/A",
                )
                else "Liên hệ để trao đổi thêm"
            )
            color_options = ", ".join(result.get("color_options", "N/A"))
            search_result = ""

            search_result += self._get_infomation(title, "Tên sản phẩm:")
            search_result += self._get_infomation(
                product_promotion,
                "Ưu đãi:",
            )
            search_result += self._get_infomation(
                product_specs,
                "Chi tiết sản phẩm:",
            )
            search_result += self._get_infomation(current_price, "Giá tiền:")
            search_result += self._get_infomation(
                color_options,
                "Các màu điện thoại:",
            )
            results.append(search_result)
        return results

    # Function to get embedding of query sentence
    def get_embedding(self, text: str) -> list[float]:
        if not text.strip():
            logger.info("Attempted to get embedding for empty text.")
            return []

        embedding = embedding_model.encode(
            text.replace(
                "###",
                "",
            )
            .replace("\n", "")
            .replace("<br>", ""),
        )

        return embedding.tolist()

    def classification_query(self, queries):
        for query in queries:
            score, intent = senmatic_router.guide(
                query,
                embedding_routes,
            )
        if intent == "products":
            return True
        else:
            return False

    def extension_query(self, llm, history_query) -> str:
        summary_query = "###The chat history is {history_query}. ### Output: reconstruct string".format(
            history_query=history_query,
        )

        return llm.get_message(summary_query, stream=False)

from __future__ import annotations

import os

import src.service.LLM.PROMPT as p
from src.common.logger import get_logger
from src.common.text import TextProcessor
from dotenv import load_dotenv
from src.service.LLM.llm import LLM
from src.service.LLM.tool_infos import Tools
from src.service.RAG import RAG

load_dotenv()

logger = get_logger("ToolController")


class ToolController:
    def __init__(self, num_history: int = 10):
        self.search = RAG()
        self.text_processor = TextProcessor()
        self.llm = LLM(instructions=p.model_instructions())
        self.llm_instructions = LLM(instructions=p.model_summary_chat_history_prompt())
        self.history = []
        self.num_history = num_history
        t = Tools()
        self.tools = t.get_tools()

    def get_tools(self):
        return self.tools

    def execute_method_by_name(self, method_name: str, params: dict):
        if not hasattr(self, method_name):
            logger.info(
                f"Method '{method_name}' not found in {self.__class__.__name__}"
            )

        method = getattr(self, method_name)

        if not callable(method):
            logger.info(f"Attribute '{method_name}' is not callable")

        return method(**params)

    def summary_chat_history(self):
        return self.text_processor.extension_query(
            self.llm_instructions, self.history[-self.num_history :]
        )

    def get_general_message(self, query):
        query = str(query).strip()
        try:
            is_needRAG = self.text_processor.classification_query([query])
            self.history.append({"role": "user", "content": query})

            if is_needRAG:
                query = self.summary_chat_history()
                bonus_info = self.search.get_graph_search_result(query)
                full_query = query + "\n" + bonus_info
            else:
                full_query = query

            return full_query
        except Exception as e:
            logger.info(f"Error in get_product_info: {e}")
            return f"Lỗi khi xử lý truy vấn: {str(e)}  - {query}"

    def get_llm_response(self, query: str):
        response = self.llm.get_message(query)
        self.history.append({"role": "model", "content": response})
        return response

    def get_history(self):
        return self.history

    def delete_history(self):
        self.history = []
        return "History deleted successfully"

    def get_shop_info(self, query, url=os.environ["LOCATION_URL"]):
        self.history.append({"role": "user", "content": query})
        return query + "\n" + self.search.get_shop_info(url)

    def get_web_search(self, query: str, max_results: int = 3):
        self.history.append({"role": "user", "content": query})
        return query + "\n" + self.search.get_web_search_result(query, max_results)

    def get_product_link(self, query, product_name: str):
        self.history.append({"role": "user", "content": query})
        return query + "\n" + self.search.get_product_link(product_name)

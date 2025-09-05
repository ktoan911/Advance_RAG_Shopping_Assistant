from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.tools import tool

import src.service.LLM.PROMPT as p
from src.common.logger import get_logger
from src.common.text import TextProcessor
from src.controller.tools import all_tools, all_tools_dict
from src.service.LLM.llm import Chatbot
from src.service.RAG import RAG

load_dotenv()

logger = get_logger("Tools")
search = RAG()
text_processor = TextProcessor()

tool_prompts = {
    "shop_information": p.get_shop_information_instruction(),
    "web_search": p.get_web_search_information_instruction(),
    "buy_link": p.get_buy_link_instruction(),
    "general_query": p.get_general_query_instruction(),
}


@tool(description=tool_prompts["general_query"])
def get_general_message(self, query: str) -> str:
    """
    Args:
        query (str): Full user's query
    Returns:
        str: Added infomation query
    """
    query = str(query).strip()
    try:
        is_needRAG = text_processor.classification_query([query])

        if is_needRAG:
            bonus_info = search.get_graph_search_result(query)
            full_query = query + "\n" + bonus_info
        else:
            full_query = query

        return full_query
    except Exception as e:
        logger.info(f"Error in get_product_info: {e}")
        return f"Lỗi khi xử lý truy vấn: {str(e)}  - {query}"


@tool(description=tool_prompts["shop_information"])
def get_shop_info(self, query: str, url=os.environ["LOCATION_URL"]) -> str:
    """
    Args:
        query (str): Full user's query
    Returns:
        str: Added infomation query
    """
    return query + "\n" + self.search.get_shop_info(url)


@tool(description=tool_prompts["web_search"])
def get_web_search(self, query: str, max_results: int = 3) -> str:
    """
    Args:
        query (str): Full user's query
    Returns:
        str: Added infomation query
    """
    return query + "\n" + self.search.get_web_search_result(query, max_results)


@tool(description=tool_prompts["buy_link"])
def get_product_link(self, query: str, product_name: str) -> str:
    """
    Args:
        query (str): Full user's query
        product_name (str): Name of the product to find a purchase link for
    Returns:
        str: Added infomation query
    """
    return query + "\n" + self.search.get_product_link(product_name)


all_tools = [
    get_general_message,
    get_shop_info,
    get_web_search,
    get_product_link,
]
all_tools_dict = {
    "get_general_message": get_general_message,
    "get_shop_info": get_shop_info,
    "get_web_search": get_web_search,
    "get_product_link": get_product_link,
}

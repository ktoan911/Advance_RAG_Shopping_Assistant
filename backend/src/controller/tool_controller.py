from __future__ import annotations

import os

from dotenv import load_dotenv

import src.service.LLM.PROMPT as p
from src.common.logger import get_logger
from src.common.text import TextProcessor
from src.controller.memory_manager import MemoryManager
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
        self.num_history = num_history
        t = Tools()
        self.tools = t.get_tools()
        self.memory_manager = MemoryManager()

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

    def get_general_message(self, query):
        query = str(query).strip()
        try:
            is_needRAG = self.text_processor.classification_query([query])
            self.history.append({"role": "user", "content": query})
            bonus_info = ""
            if is_needRAG:
                bonus_info = self.search.get_graph_search_result(query)

            return bonus_info
        except Exception as e:
            logger.info(f"Error in get_product_info: {e}")
            return f"Lỗi khi xử lý truy vấn: {str(e)}  - {query}"

    def get_llm_response(self, raw_query: str, info_prompt: str):
        mem_prompt = self._build_context_prompt(raw_query)
        full_prompt = (
            mem_prompt + "\n" + info_prompt if info_prompt != "" else mem_prompt
        )
        response = self.llm.get_message(full_prompt)
        self.history.append({"role": "model", "content": response})
        self._extract_and_save_entities(raw_query)

        self.memory_manager.save_conversation_context(
            {"input": raw_query}, {"output": response}
        )

        return response

    def get_history(self):
        return self.history

    def delete_history(self):
        self.history = []
        return "History deleted successfully"

    def get_shop_info(self, query, url=os.environ["LOCATION_URL"]):
        self.history.append({"role": "user", "content": query})
        return self.search.get_shop_info(url)

    def get_web_search(self, query: str, max_results: int = 3):
        self.history.append({"role": "user", "content": query})
        return self.search.get_web_search_result(query, max_results)

    def get_product_link(self, query, product_name: str):
        self.history.append({"role": "user", "content": query})
        return self.search.get_product_link(product_name)

    def _build_context_prompt(self, user_input: str) -> str:
        context = self.memory_manager.get_comprehensive_context(user_input)

        # Xây dựng prompt
        prompt_parts = [self.system_prompt]

        # Thêm thông tin về entities (thông tin cá nhân)
        if context.get("relevant_entities"):
            prompt_parts.append("\n=== THÔNG TIN ĐÃ BIẾT VỀ NGƯỜI DÙNG ===")
            for entity, facts in context["relevant_entities"].items():
                if facts and isinstance(facts, list):
                    prompt_parts.append(f"{entity}: {', '.join(facts)}")

        # Thêm memories liên quan
        if (
            context.get("relevant_memories")
            and context["relevant_memories"]
            != "Không tìm thấy thông tin liên quan trong bộ nhớ."
        ):
            prompt_parts.append(
                "\n=== THÔNG TIN LIÊN QUAN TỪ CÁC CUỘC TRÒ CHUYỆN TRƯỚC ==="
            )
            prompt_parts.append(context["relevant_memories"])

        # Thêm lịch sử trò chuyện gần đây
        if context.get("recent_conversation"):
            prompt_parts.append("\n=== LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY ===")
            for msg in context["recent_conversation"][
                -5:
            ]:  # Chỉ lấy 5 tin nhắn gần nhất
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    role = "Người dùng" if msg["role"] == "human" else "AI"
                    prompt_parts.append(f"{role}: {msg['content']}")

        # Thêm câu hỏi hiện tại
        prompt_parts.append(f"\n=== CÂU HỎI HIỆN TẠI ===\nNgười dùng: {user_input}")
        prompt_parts.append("\nHãy trả lời một cách tự nhiên và hữu ích:")

        return "\n".join(prompt_parts)

    def _extract_and_save_entities(self, user_input: str) -> None:
        personal_keywords = {
            "tên": ["tên tôi là", "tôi tên", "mình tên", "tôi là", "tên tớ", "tớ tên"],
            "tuổi": ["tôi", "tuổi", "năm nay", "sinh năm"],
            "nghề nghiệp": ["tôi làm", "nghề", "công việc", "làm việc tại"],
            "sở thích": ["thích", "yêu thích", "sở thích", "hobby", "yêu"],
            "địa chỉ": ["tôi ở", "sống ở", "địa chỉ", "quê ở"],
            "gia đình": ["vợ", "chồng", "con", "bố mẹ", "anh chị em"],
        }

        # Kiểm tra và trích xuất thông tin từ user input
        user_lower = user_input.lower()
        for entity_type, keywords in personal_keywords.items():
            for keyword in keywords:
                if keyword in user_lower:
                    # Lưu thông tin vào entity store
                    self.memory_manager.add_entity_fact(entity_type, user_input)
                    break

from __future__ import annotations

from dotenv import load_dotenv

import src.service.LLM.PROMPT as p
from src.common.logger import get_logger
from src.controller.memory_controller import MemoryController
from src.controller.tools import all_tools, all_tools_dict
from src.service.LLM.llm import Chatbot

load_dotenv()

logger = get_logger("Controller")


class ChatController:
    def __init__(self, user_id: str, num_history: int = 10):
        self.llm = Chatbot(instructions=p.INSTRUCTIONS)
        self.agent = Chatbot(all_tools=all_tools)
        self.history = []
        self.num_history = num_history
        self.memory_manager = MemoryController(user_id=user_id, llm=self.llm)

    def get_message(self, query, need_history: bool = True) -> str:
        tools_call = self.agent.function_calling(query)
        add_info = self.execute_tool_call(tools_call[0])
        self._extract_and_save_entities(query)
        if need_history:
            full_prompt = self._build_context_prompt(
                user_input=query, add_info=add_info
            )
        else:
            full_prompt = f"=== CÂU HỎI HIỆN TẠI ===\nNgười dùng: {query}\n=== THÔNG TIN BỔ SUNG ===\n{add_info}\nHãy trả lời một cách tự nhiên và hữu ích:"

        ai_response = self.llm.get_message(full_prompt, need_history=True)
        self.memory_manager.save_conversation_context(
            {"input": query}, {"output": ai_response}
        )
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "model", "content": ai_response})
        return ai_response

    def execute_tool_call(tool_call: dict):
        tool_name = tool_call["name"]
        args = tool_call.get("args", {})

        if tool_name not in all_tools_dict:
            raise ValueError(f"Tool {tool_name} not found!")

        tool = all_tools_dict[tool_name]
        return tool.invoke(args)

    def get_history(self):
        return self.history

    def delete_history(self):
        self.history = []
        return "History deleted successfully"

    def _build_context_prompt(self, user_input: str, add_info: str = None) -> str:
        context = self.memory_manager.get_comprehensive_context(user_input)

        # Xây dựng prompt
        prompt_parts = [self.instructions]

        if add_info:
            prompt_parts.append(f"\n=== THÔNG TIN BỔ SUNG ===\n{add_info}")
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
            "tên": ["tên tôi là", "tôi tên", "mình tên", "tôi là"],
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

    def get_memory_summary(self):
        return self.memory_manager.get_memory_summary()

    def clear_session(self) -> None:
        self.memory_manager.clear_session_memory()

    def clear_all_memory(self) -> None:
        self.memory_manager.clear_all_memory()

    def get_conversation_history(self, limit: int = 10) -> list:
        messages = self.memory_manager.get_conversation_context(limit)
        history = []

        for msg in messages:
            if hasattr(msg, "__class__"):
                if "Human" in str(type(msg)):
                    history.append({"role": "user", "content": msg.content})
                elif "AI" in str(type(msg)):
                    history.append({"role": "assistant", "content": msg.content})

        return history

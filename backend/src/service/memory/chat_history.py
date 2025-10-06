import json
import time
from typing import List

from langchain.schema import BaseChatMessageHistory
from langchain.schema.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from src.model.chat_db import ChatDB


class ChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, user_id: str, session_id: str = "default"):
        self.user_id = user_id
        self.session_id = session_id
        self.chat_db = ChatDB()

    def _message_to_dict(self, message: BaseMessage) -> dict:
        return {
            "type": message.__class__.__name__,
            "content": message.content,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": time.time(),
        }

    def exists(self):
        return False

    def get(self):
        return []

    def set(self, messages):
        return None

    def _dict_to_message(self, message_dict: dict) -> BaseMessage:
        message_type = message_dict["type"]
        content = message_dict["content"]

        if message_type == "HumanMessage":
            return HumanMessage(content=content)
        elif message_type == "AIMessage":
            return AIMessage(content=content)
        elif message_type == "SystemMessage":
            return SystemMessage(content=content)
        else:
            return HumanMessage(content=content)

    def _load_messages(self) -> List[dict]:
        try:
            message_dicts = list(self.chat_db.get_user(self.user_id))
            if not message_dicts:
                return []
            return message_dicts
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @property
    def messages(self) -> List[BaseMessage]:
        message_dicts = self._load_messages()
        return [self._dict_to_message(msg_dict) for msg_dict in message_dicts]

    def delete(self) -> None:
        self.chat_db.delete_user(self.user_id)

    def get_recent_messages(self, limit: int = 10) -> List[BaseMessage]:
        return self.messages[-limit:] if len(self.messages) > limit else self.messages

    def get_conversation_summary(self) -> str:
        messages = self.messages
        if not messages:
            return "Chưa có cuộc trò chuyện nào."

        summary_parts = []
        for message in messages[-10:]: 
            if isinstance(message, HumanMessage):
                summary_parts.append(f"Người dùng: {message.content[:100]}...")
            elif isinstance(message, AIMessage):
                summary_parts.append(f"AI: {message.content[:100]}...")

        return "\n".join(summary_parts)

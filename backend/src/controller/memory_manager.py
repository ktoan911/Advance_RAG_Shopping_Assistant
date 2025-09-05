"""
Memory Manager để quản lý và kết hợp tất cả các loại memory
"""

from typing import Any, Dict, List

from langchain.memory import ConversationBufferMemory
from langchain.schema.messages import BaseMessage

from src.service.memory.json_chat_history import JSONChatMessageHistory
from src.service.memory.json_entity_store import JSONEntityStore
from src.service.memory.vector_memory import VectorStoreMemory


class MemoryManager:
    def __init__(self, user_id: str, session_id: str = "default"):
        self.user_id = user_id
        self.session_id = session_id
        self._initialize_memories()

    def _initialize_memories(self) -> None:
        self.entity_store = JSONEntityStore(self.user_id)

        self.chat_history = JSONChatMessageHistory(self.user_id, self.session_id)

        self.conversation_memory = ConversationBufferMemory(
            chat_memory=self.chat_history,
            memory_key="chat_history",
            return_messages=True,
        )

        self.vector_memory = VectorStoreMemory(self.user_id)

    def add_entity_fact(self, entity: str, fact: str) -> None:
        self.entity_store.add_fact(entity, fact)

        self.vector_memory.add_memory(
            content=f"Thông tin về {entity}: {fact}",
            memory_type="entity_fact",
            additional_metadata={"entity": entity},
        )

    def get_conversation_context(self, limit: int = 10) -> List[BaseMessage]:
        return self.chat_history.get_recent_messages(limit)

    def get_all_entities(self) -> Dict[str, List[str]]:
        return self.entity_store.get_all_entities()

    def search_relevant_memories(self, query: str, limit: int = 5) -> str:
        return self.vector_memory.get_memory_summary(query)

    def get_memory_summary(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "total_entities": len(self.entity_store.get_all_entities()),
            "conversation_summary": self.chat_history.get_conversation_summary(),
            "entities": self.entity_store.get_all_entities(),
        }

    def clear_session_memory(self) -> None:
        self.chat_history.clear()

    def clear_all_memory(self) -> None:
        self.chat_history.clear()
        self.entity_store.clear()
        self.vector_memory.clear_memories()

    def search_chat_history(self, query: str, limit: int = 5) -> List[BaseMessage]:
        return self.chat_history.search_messages(query, limit)

    def save_conversation_context(
        self, inputs: Dict[str, Any], outputs: Dict[str, str]
    ) -> None:
        self.conversation_memory.save_context(inputs, outputs)

        self.vector_memory.save_context(inputs, outputs)

    def get_comprehensive_context(
        self, current_input: str, context_limit: int = 5
    ) -> Dict[str, Any]:
        conversation_messages = self.get_conversation_context(context_limit)

        context = {
            "recent_conversation": [
                {
                    "role": "human" if "Human" in str(type(msg)) else "ai",
                    "content": msg.content,
                }
                for msg in conversation_messages
            ]
            if conversation_messages
            else [],
            "relevant_entities": self.get_all_entities(),
            "relevant_memories": self.search_relevant_memories(
                current_input, context_limit
            ),
            "memory_summary": self.get_memory_summary(),
        }

        return context

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from langchain.docstore.document import Document
from langchain.schema import BaseMemory

try:
    from langchain_mongodb import MongoDBAtlasVectorSearch
except ImportError:
    from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from pydantic import Field

from src.model.chat_db import ChatDB

from .safe_embeddings import SafeEmbeddings


def ensure_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


class VectorStoreMemory(BaseMemory):
    user_id: str = Field(default="")
    embeddings: Optional[Any] = Field(default=None, exclude=True)
    metadata_path: Optional[Path] = Field(default=None, exclude=True)
    vector_store: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, user_id: str, **data):
        ensure_event_loop()

        super().__init__(user_id=user_id, **data)
        self.embeddings = SafeEmbeddings()

        self.chat_db = ChatDB()
        self.vector_store = MongoDBAtlasVectorSearch(
            collection=self.chat_db._collection, embedding=self.embeddings
        )

    def add_memory(
        self,
        content: str,
        memory_type: str = "conversation",
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        ensure_event_loop()

        metadata = {
            "user_id": self.user_id,
            "type": memory_type,
            "timestamp": str(np.datetime64("now")),
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        document = Document(page_content=content, metadata=metadata)

        try:
            self.vector_store.add_documents([document])
        except Exception as e:
            print(f"Lỗi khi thêm memory: {e}")

    def retrieve_memories(self, query: str, k: int = 5) -> List[Document]:
        ensure_event_loop()

        try:
            # similarity
            docs = self.vector_store.similarity_search(query, k=k)

            filtered_docs = [doc for doc in docs if doc.metadata.get("type") != "init"]

            return filtered_docs
        except Exception as e:
            print(f"Lỗi khi truy xuất memories: {e}")
            return []

    def get_memory_summary(self, query: str) -> str:
        memories = self.retrieve_memories(query)

        if not memories:
            return "Không tìm thấy thông tin liên quan trong bộ nhớ."

        summary_parts = []
        for i, memory in enumerate(memories, 1):
            memory_type = memory.metadata.get("type", "unknown")
            content_preview = (
                memory.page_content[:200] + "..."
                if len(memory.page_content) > 200
                else memory.page_content
            )

            summary_parts.append(f"{i}. [{memory_type}] {content_preview}")

        return "\n".join(summary_parts)

    def clear_memories(self) -> None:
        try:
            self.chat_db.delete_user(self.user_id)
            dummy_doc = Document(
                page_content="Khởi tạo vector store",
                metadata={"user_id": self.user_id, "type": "init"},
            )
            self.vector_store = MongoDBAtlasVectorSearch.from_documents(
                documents=[dummy_doc],
                embedding=self.embeddings,
                collection=self.chat_db._collection,
            )

        except Exception as e:
            print(f"Lỗi khi xóa memories: {e}")

    def clear(self) -> None:
        self.clear_memories()

    @property
    def memory_variables(self) -> List[str]:
        return ["relevant_memories"]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        query = inputs.get("input", "")
        if query:
            relevant_memories = self.get_memory_summary(query)
            return {"relevant_memories": relevant_memories}
        return {"relevant_memories": ""}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        user_input = inputs.get("input", "")
        ai_output = outputs.get("output", "")

        if user_input and ai_output:
            # Save chat
            conversation = f"Người dùng: {user_input}\nAI: {ai_output}"
            self.add_memory(
                content=conversation,
                memory_type="conversation",
                additional_metadata={"user_input": user_input, "ai_output": ai_output},
            )

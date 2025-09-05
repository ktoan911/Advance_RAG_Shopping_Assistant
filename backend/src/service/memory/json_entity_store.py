from typing import Dict, List, Optional

from langchain.memory.entity import BaseEntityStore
from pydantic import Field

from src.model.chat_db import ChatDB


class JSONEntityStore(BaseEntityStore):
    user_id: str = Field(default="")
    chat_db: Optional[ChatDB] = Field(default=None)

    def __init__(self, user_id: str):
        # Initialize với user_id và data khác
        super().__init__(user_id=user_id)
        self.chat_db = ChatDB()

    def _get_user_entity(self):
        user_entity = self.chat_db.get_user(self.user_id)
        if user_entity is None:
            user_entity = {"user_id": self.user_id}
            self.chat_db.insert_user(user_entity)
        return user_entity

    def clear(self) -> None:
        self.chat_db.delete_user(self.user_id)

    def get_all_entities(self) -> Dict[str, List[str]]:
        user_entity = self._get_user_entity()
        # Return only the entity data, excluding user_id and MongoDB _id
        return {k: v for k, v in user_entity.items() if k not in ["_id", "user_id"]}

    def add_fact(self, entity_key: str, fact: str) -> None:
        entities = self._get_user_entity()
        if entity_key not in entities:
            entities[entity_key] = []

        # Tránh lưu trùng lặp
        if fact not in entities[entity_key]:
            entities[entity_key].append(fact)

        self.chat_db.update_user(self.user_id, {"$set": entities})

    def delete(self):
        return None

    def exists(self):
        return False

    def get(self):
        return []

    def set(self, messages):
        return None

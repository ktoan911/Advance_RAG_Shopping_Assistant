import os
import sys

# Add the src directory to the Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import dotenv
import pymongo

from src.common.logger import get_logger

dotenv.load_dotenv()
logger = get_logger(__name__)


class ChatDB:
    def __init__(
        self,
        connection_url=os.environ["MONGO_URI"],
        db_name=os.environ["DB_NAME"],
        collection_name=os.environ["COLLECTION_NAME"],
    ):
        try:
            self.connection_url = connection_url.split("@")[-1]
            self.connection = pymongo.MongoClient(connection_url)
            self._db = self.connection[db_name]
            self._collection = self._db[collection_name]
            self.connection_url_not_split = connection_url
        except pymongo.errors.ConnectionFailure as e:
            logger.info(f"Connection failed: {e}")
            return None

    def get_user(self, user_id: str):
        return self._collection.find({"user_id": user_id})

    def insert_user(self, user_data: dict):
        return self._collection.insert_one(user_data)

    def delete_user(self, user_id: str):
        return self._collection.delete_many({"user_id": user_id})

    def update_user(self, user_id: str, update_data: dict):
        return self._collection.update_many({"user_id": user_id}, {"$set": update_data})

    def __del__(self):
        if self.connection:
            self.connection.close()

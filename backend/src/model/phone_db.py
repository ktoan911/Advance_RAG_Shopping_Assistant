import os
import sys

# Add the src directory to the Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import dotenv
import pymongo
from src.common.logger import get_logger
from src.common.text import TextProcessor

# from common.text import get_embedding

dotenv.load_dotenv()
logger = get_logger(__name__)


class PhoneDB:
    def __init__(self, connection_url=os.environ["MONGO_URI"]):
        try:
            self.connection_url = connection_url.split("@")[-1]
            self.connection = pymongo.MongoClient(connection_url)
            self._db = self.connection[os.environ["DB_NAME"]]
            self._collection = self._db[os.environ["COLLECTION_NAME"]]
            self.connection_url_not_split = connection_url
        except pymongo.errors.ConnectionFailure as e:
            logger.info(f"Connection failed: {e}")
            return None

        self.text_processor = TextProcessor()

    def get_all(self):
        return list(self._collection.find({}))

    def vector_search(self, user_query, num_candidates=100, k=20):
        query_embedding = self.text_processor.get_embedding(user_query)
        if query_embedding is None:
            return "Invalid query or embedding generation failed."

        vector_search_stage = {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": num_candidates,
                "limit": k,
            },
        }

        unset_stage = {
            "$unset": "embedding",
        }

        project_stage = {
            "$project": {
                "_id": 0,  # Exclude the _id field
                "url": 1,  # Include the Phone url
                "title": 1,  # Include the Phone field
                "product_promotion": 1,  # Include the Description field
                "product_specs": 1,  # Include the specs field
                "current_price": 1,
                "color_options": 1,
                "score": {
                    "$meta": "vectorSearchScore",  # Include the search score
                },
            },
        }

        sort_stage = {
            "$sort": {
                "score": -1  # Sort by vectorSearchScore in descending order (highest scores first)
            }
        }

        pipeline = [vector_search_stage, unset_stage, project_stage, sort_stage]

        # Thực thi pipeline
        results = self._collection.aggregate(pipeline)
        return list(results)

    def __del__(self):
        if self.connection:
            self.connection.close()

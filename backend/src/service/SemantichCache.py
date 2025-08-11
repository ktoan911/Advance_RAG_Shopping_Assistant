from __future__ import annotations

import os

import pymongo
from dotenv import load_dotenv

load_dotenv()


def design_collections(db):
    questions = db[os.environ['COLLECTION_QUES_NAME']]
    answers = db[os.environ['COLLECTION_ANS_NAME']]
    return questions, answers


def get_mongo_client(mongo_uri):
    """Establish connection to the MongoDB."""
    try:
        # Connect to MongoDB using URI
        client = pymongo.MongoClient(
            mongo_uri, appname='devrel.content.python',
        )
        print('Connection to MongoDB successful')
        return client
    except pymongo.errors.ConnectionFailure as e:
        print(f'Connection failed: {e}')
        return None


client = get_mongo_client(os.environ['MONGO_URI'])
ques, ans = design_collections(client[os.environ['DB_CACHE_NAME']])


class MongoSemanticCache():
    def __init__(self):
        self._ques, self._answer = ques, ans

    def insert(self, data):
        question = data['question']  # collection question
        answer = data['answer']  # collection answers
        question_embedding = data['embedding']

        if not question_embedding:
            return None

        question_doc = {
            'question': question,
            'embedding': question_embedding,
        }
        question_id = self._ques.insert_one(question_doc).inserted_id

        answer_doc = {
            'question_id': question_id,
            'answer': answer,
        }
        self._answer.insert_one(answer_doc)

        return question_id

    def semantic_search(self, query_embedding, limit=4, threshold=0.94):

        if query_embedding is None:
            return 'Invalid query or embedding generation failed.'

        vector_search_stage = {
            '$vectorSearch': {
                'index': 'vector_index',
                'queryVector': query_embedding,
                'path': 'embedding',
                'numCandidates': 400,
                'limit': limit,
            },
        }

        unset_stage = {
            '$unset': 'embedding',
        }

        # join the answers collection with the questions collection by the question_id field
        lookup_stage = {
            '$lookup': {
                # The answers collection
                'from': os.environ['COLLECTION_ANS_NAME'],
                'localField': '_id',         # Field from the questions collection
                'foreignField': 'question_id',  # Field from the answers collection
                'as': 'answers',              # Output array field
            },
        }

        project_stage = {
            '$project': {
                '_id': 0,
                'question': 1,
                'answers.answer': 1,  # Include only the answer
                'score': {
                    '$meta': 'vectorSearchScore',
                },
            },
        }

        pipeline = [
            vector_search_stage,
            unset_stage, lookup_stage, project_stage,
        ]

        results = list(self._ques.aggregate(pipeline))

        filtered_results = [
            result for result in results if result['score'] >= threshold
        ]

        sorted_filtered_results = []
        if len(filtered_results) > 0:
            sorted_filtered_results = sorted(
                filtered_results, key=lambda x: x['score'], reverse=True,
            )

        return sorted_filtered_results

    def check_connection_and_permissions(self):
        try:
            # Check read permission
            self.client.admin.command('ping')
            print('Connection successful.')

            # Check write permission
            self.db['test_collection'].insert_one({'test': 'test'})
            self.db['test_collection'].delete_one({'test': 'test'})
            print('Write permission check successful.')

            # Dropping test_collection if exists
            self.db.drop_collection('test_collection')
        except Exception as e:
            print(f'Unexpected error: {e}')

    def drop_collection(self, collection_name):
        self.db[collection_name].drop()

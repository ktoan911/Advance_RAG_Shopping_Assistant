import os
import random
import re
import sys
from threading import Thread

import torch

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import warnings

from src.common.logger import get_logger
from src.common.text import TextProcessor
from dotenv import load_dotenv
from src.model.phone_db import PhoneDB
from neo4j import GraphDatabase
from src.service.LLM.llm import LLM
from src.service.LLM.PROMPT import extract_entity_relationship_prompt
from torch_geometric.data import Data

from .gae import GAE 

warnings.filterwarnings("ignore")

load_dotenv()
logger = get_logger(__name__)


class Neo4jGraph:
    def __init__(self, uri=None, username=None, password=None):
        if uri is None:
            uri = os.environ.get("AURA_CONNECTION_URI", "neo4j://localhost:7687")
        if username is None:
            username = os.environ.get("AURA_USERNAME", "neo4j")
        if password is None:
            password = os.environ.get("AURA_PASSWORD", "12345678")

        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.llm = LLM(temperature=1, top_p=1)
        self.db = PhoneDB()
        self.text_processor = TextProcessor()

    def extract_entities_and_relationships(self, text, list_output=None):
        def add_output(t):
            list_output.append(self.llm.get_message(t))

        if isinstance(text, str):
            prompt = extract_entity_relationship_prompt(text)
            return self.llm.get_message(prompt)
        elif isinstance(text, list):
            my_threads = []
            for t in text:
                if t is None or t == "":
                    continue
                my_thread = Thread(target=add_output, args=(t,))
                my_thread.start()
                my_threads.append(my_thread)
            for my_thread in my_threads:
                my_thread.join()

    def process_llm_out(self, result):
        response = result

        # Extract entities
        entity_pattern = r"- (.+): (.+)"
        entities = re.findall(entity_pattern, response)
        entity_dict = {
            entity.strip(): entity_type.strip() for entity, entity_type in entities
        }
        entity_list = list(entity_dict.keys())

        # Extract relationships
        relationship_pattern = r"- \(([^,]+), ([^,]+), ([^)]+)\)"
        relationships = re.findall(relationship_pattern, response)
        relationship_list = [
            (
                self.extract_content(subject.strip()),
                self.extract_content(relation.strip().replace(" ", "_").upper()),
                self.extract_content(object_.strip()),
            )
            for subject, relation, object_ in relationships
        ]
        return entity_list, relationship_list

    def build_graph(self):
        list_info = self.text_processor.transform_query(self.db.get_all())
        logger.info(f"Number of documents to process: {len(list_info)}")
        count = 0

        for doc in list_info:
            result = self.extract_entities_and_relationships(doc)
            _, relationship_list = self.process_llm_out(result)
            self.add_node(relationship_list)
            count += 1
            if count % 100 == 0:
                logger.info(f"Processed {count} documents")

    def add_node(self, relationships):
        with self.driver.session() as session:
            for subject, relation, obj in relationships:
                session.write_transaction(self._add_node_tx, subject, obj, relation)

    def _add_node_tx(self, tx, subject, object, relation):
        cypher_query = f"""
            MERGE (a:Entity {{name: $subject}})
            MERGE (b:Entity {{name: $object}})
            MERGE (a)-[:`{relation}`]->(b)
        """
        tx.run(
            cypher_query,
            subject=subject,
            object=object,
            relation=relation,
        )

    def extract_content(self, text: str):
        return text.replace("{", "").replace("}", "")

    def get_node_mapping_id(self):
        try:
            logger.info("Starting get_node_mapping_id query...")
            with self.driver.session() as session:
                nodes_query = "MATCH (n:Entity) RETURN id(n) AS node_id, n.name AS name"
                logger.info(f"Executing query: {nodes_query}")
                nodes = session.run(nodes_query)
                node_mapping = {record["node_id"]: record["name"] for record in nodes}
                reverse_node_mapping = {value: key for key, value in node_mapping.items()}
                logger.info(f"Found {len(node_mapping)} nodes in Neo4j")
                if len(node_mapping) > 0:
                    logger.info(f"Sample nodes: {list(node_mapping.items())[:3]}")
                else:
                    logger.warning("No nodes found! Checking database status...")
                    # Quick diagnostic query
                    result = session.run("MATCH (n) RETURN count(n) as total_count")
                    total_count = result.single()["total_count"]
                    logger.warning(f"Total nodes in database: {total_count}")
            return node_mapping, reverse_node_mapping
        except Exception as e:
            logger.error(f"Error in get_node_mapping_id: {e}")
            return {}, {}

    def get_edge(self):
        try:
            logger.info("Starting get_edge query...")
            with self.driver.session() as session:
                edges_query = "MATCH (n)-[r]->(m) RETURN id(n) AS source, id(m) AS target, type(r) AS relationship_type"
                logger.info(f"Executing query: {edges_query}")
                edges = session.run(edges_query)
                edge_list = [
                    (record["source"], record["target"], record["relationship_type"])
                    for record in edges
                ]
                logger.info(f"Found {len(edge_list)} edges in Neo4j")
                if len(edge_list) > 0:
                    logger.info(f"Sample edges: {edge_list[:3]}")
                else:
                    logger.warning("No edges found! Checking database status...")
                    # Quick diagnostic query  
                    result = session.run("MATCH ()-[r]->() RETURN count(r) as total_edges")
                    total_edges = result.single()["total_edges"]
                    logger.warning(f"Total edges in database: {total_edges}")
            return edge_list
        except Exception as e:
            logger.error(f"Error in get_edge: {e}")
            return []

    def get_graph_data(self):
        node_mapping, reverse_node_mapping = self.get_node_mapping_id()
        # Get edges and edge types
        edge_list = self.get_edge()
        # Create a mapping from edge names to indices
        edge_name_to_index = {
            name: idx for idx, name in enumerate(set(edge[2] for edge in edge_list))
        }

        # Extract all unique relationship types
        unique_relationship_types = {e[2] for e in edge_list}

        return (
            node_mapping,
            reverse_node_mapping,
            edge_list,
            unique_relationship_types,
            edge_name_to_index,
        )

    def get_data_matrix_training(self, training: float = 0.8):
        (
            node_mapping,
            reverse_node_mapping,
            edge_list,
            unique_relationship_types,
            edge_name_to_index,
        ) = self.get_graph_data()

        edge_index = (
            torch.tensor([[e[0], e[1]] for e in edge_list], dtype=torch.long)
            .t()
            .contiguous()
        )

        # Features for nodes (one-hot encoding)
        num_nodes = len(node_mapping)
        features = torch.eye(num_nodes)  # One-hot encoding for each node

        # Split edges into training and validation sets
        num_edges = edge_index.size(1)
        indices = list(range(num_edges))
        random.shuffle(indices)
        split_idx = int(training * num_edges)  # split train and validation sets

        train_indices = indices[:split_idx]
        val_indices = indices[split_idx:]

        train_edge_index = edge_index[:, train_indices]
        val_edge_index = edge_index[:, val_indices]

        train_data = Data(x=features, edge_index=train_edge_index)
        val_data = Data(x=features, edge_index=val_edge_index)

        return train_data, val_data, features

    def get_all_graph_embeddings(
        self, num_nodes, edge_list, model_path=r"models/best_gcn_model.pt"
    ):
        # Validate inputs
        if num_nodes <= 0:
            raise ValueError(f"num_nodes must be positive, got {num_nodes}")
        
        if not edge_list:
            logger.warning("Edge list is empty, creating dummy embeddings")
            # Return dummy embeddings if no edges
            return torch.randn(num_nodes, 8)  # 8 is embedding_dim
        
        logger.info(f"Loading graph embeddings for {num_nodes} nodes and {len(edge_list)} edges")
        
        model = GAE(
            input_dim=num_nodes,
            hidden_dim=16,
            embedding_dim=8,
        )

        # Check if model file exists
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            # Return dummy embeddings if model file doesn't exist
            return torch.randn(num_nodes, 8)

        try:
            model.load_state_dict(torch.load(model_path, map_location='cpu'))
            model.eval()
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            # Return dummy embeddings if model loading fails
            return torch.randn(num_nodes, 8)

        # Validate edge_list format
        try:
            edge_pairs = [[e[0], e[1]] for e in edge_list]
            edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
        except Exception as e:
            logger.error(f"Failed to create edge_index tensor: {e}")
            logger.error(f"Edge list sample: {edge_list[:5] if len(edge_list) >= 5 else edge_list}")
            return torch.randn(num_nodes, 8)
        
        # Validate edge_index dimensions
        if edge_index.shape[0] != 2:
            logger.error(f"Invalid edge_index shape: {edge_index.shape}")
            return torch.randn(num_nodes, 8)
        
        node_features = torch.eye(num_nodes)  # One-hot encoding for each node

        try:
            with torch.no_grad():
                embeddings, _ = model(node_features, edge_index)
            logger.info(f"Successfully generated embeddings with shape: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed during model inference: {e}")
            return torch.randn(num_nodes, 8)

    def close(self):
        self.driver.close()

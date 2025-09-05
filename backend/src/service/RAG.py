from __future__ import annotations

import os
import sys
import time
from collections import defaultdict

# Use relative import since graph is in the same service directory
from .graph.graph import Neo4jGraph

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import torch
import torch.nn.functional as F
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from rapidfuzz import process

from src.common.text import TextProcessor
from src.model.phone_db import PhoneDB

load_dotenv()


class RAG:
    def __init__(self):
        self.db = PhoneDB(
            connection_url=os.environ["MONGO_URI"],
        )

        self.text_processor = TextProcessor()
        self.graph = Neo4jGraph()

        try:
            self.edge_list = self.graph.get_edge()
            print(f"Loaded {len(self.edge_list)} edges from Neo4j")

            self.source_nodes = [e[0] for e in self.edge_list]
            self.node_mapping, _ = self.graph.get_node_mapping_id()
            print(f"Loaded {len(self.node_mapping)} nodes from Neo4j")

            if not self.node_mapping:
                print("Warning: No nodes found in Neo4j database")
                self.embeddings_graph_nodes = torch.randn(1, 8)  # Dummy embedding
                self.node_embeddings_norm = F.normalize(
                    self.embeddings_graph_nodes, p=2, dim=1
                )
            else:
                self.embeddings_graph_nodes = self.graph.get_all_graph_embeddings(
                    num_nodes=len(self.node_mapping), edge_list=self.edge_list
                )
                self.node_embeddings_norm = F.normalize(
                    self.embeddings_graph_nodes, p=2, dim=1
                )

            self.edge_lookup = {}
            for src, tgt, rel in self.edge_list:
                self.edge_lookup[(src, tgt)] = rel

            print("Graph embeddings loaded successfully")

        except Exception as e:
            print(f"Error loading graph data: {e}")
            print("Using dummy embeddings as fallback")
            self.edge_list = []
            self.source_nodes = []
            self.node_mapping = {}
            self.embeddings_graph_nodes = torch.randn(1, 8)
            self.node_embeddings_norm = F.normalize(
                self.embeddings_graph_nodes, p=2, dim=1
            )
            self.edge_lookup = {}

        self.ddgs = DDGS()
        self.all_phones = {i["title"]: i["url"] for i in self.db.get_all()}

    def get_senmatic_search_result(self, query, num_candidates=100, k=20) -> list[str]:
        db_information = self.db.vector_search(
            query,
            num_candidates,
            k,
        )

        return self.text_processor.transform_query(db_information)

    def get_graph_search_result(self, query, senmatic_k=5, graph_k=5) -> list[str]:
        senmatic_search_result = self.get_senmatic_search_result(
            query=query, k=senmatic_k
        )
        grouped_result = defaultdict(list)
        query_infos = []
        query_entities = []
        self.graph.extract_entities_and_relationships(
            senmatic_search_result, list_output=query_infos
        )
        for query_info in query_infos:
            if query_info is None or query_info == "":
                continue
            query_entity, _ = self.graph.process_llm_out(query_info)
            if query_entity:
                query_entities.extend(query_entity)
        matches = self._find_closest_entities(query_entities, self.node_mapping)
        if not matches or len(matches) == 0:
            return "===Thông tin bổ sung cho câu hỏi===:\n" + ".\n".join(
                senmatic_search_result
            )

        matches = list(
            set(
                [
                    match_id
                    for _, match_id, _, _ in matches
                    if match_id in self.node_mapping
                ]
            )
        )

        for match_id in matches:
            query_embedding = self.embeddings_graph_nodes[match_id]
            query_embedding = F.normalize(query_embedding, p=2, dim=0)

            similarity_scores = torch.matmul(
                query_embedding.unsqueeze(0), self.node_embeddings_norm.T
            ).squeeze()

            top_k_indices = torch.topk(similarity_scores, graph_k).indices
            for idx in top_k_indices:
                similar_node_id = idx.item()
                # Check for direct connection in the edge list
                direct_connections = []
                temp = self.edge_lookup.get((match_id, similar_node_id), None)
                if temp is not None:
                    direct_connections.append((match_id, similar_node_id, temp))
                    if match_id in self.source_nodes:
                        direct_connections.append((match_id, similar_node_id, temp))
                    else:
                        direct_connections.append((similar_node_id, match_id, temp))
                if direct_connections:
                    for connection in direct_connections:
                        source = self.node_mapping[connection[0]]
                        target = self.node_mapping[connection[1]]
                        relationship = connection[2]
                        grouped_result[source].append(f"{relationship} {target}")
        graph_search_result = [
            f"{src}: {', '.join(rels)}" for src, rels in grouped_result.items()
        ]
        return "=== Thông tin bổ sung cho câu hỏi ===:\n" + ".\n".join(
            sorted(list(set(graph_search_result)))
        )

    def _find_closest_entities(self, entities, node_mapping):
        """
        Finds the closest matching entities in node_mapping for a list of query entities.

        Parameters:
            entities (list): List of entity names to match.
            node_mapping (dict): Mapping of node IDs to entity names.

        Returns:
            list: A list of tuples [(query_entity, closest_match_id, closest_match_name, score)].
        """
        results = []
        node_names = list(node_mapping.values())
        for entity in entities:
            closest_match, score, index = process.extractOne(entity, node_names)
            closest_match_id = list(node_mapping.keys())[index]
            results.append((entity, closest_match_id, closest_match, score))
        return results

    def get_web_search_result(
        self, query: str, max_results: int = 10, num_tries=3
    ) -> list[dict]:
        web_results = []
        n = num_tries
        while n > 0:
            try:
                web_results = self.ddgs.text(query, max_results=max_results)
                web_results = [
                    f"Tiêu đề: {result['title']}. Nguồn:{result['href']}. Nội dung:{result['body']}"
                    for result in web_results
                ]
                return "=== Thông tin bổ sung cho câu hỏi ===:\n" + ".\n".join(
                    sorted(list(set(web_results)))
                )
            except Exception:
                time.sleep(0.5)
                n -= 1
        return "Không tìm thấy thông tin bổ sung từ web."

    def get_shop_info(self, url=os.environ["LOCATION_URL"]):
        data = pd.read_csv(url).to_dict(orient="records")
        loc = [
            f"Cơ sở {i}: {item['location']}.Link google map: {item['maps']}. Giờ mở cửa: {item['open']}"
            for i, item in enumerate(data, start=1)
        ]

        return "=== Thông tin cửa hàng ===:\n" + ".\n".join(sorted(list(set(loc))))

    def get_product_link(self, product_name: str):
        sim_product = process.extract(product_name, self.all_phones.keys(), limit=3)
        return "=== Thông tin bổ sung cho câu hỏi ===: \n" + "\n".join(
            [f"{name} - {self.all_phones[name]}" for name, _, _ in sim_product]
        )

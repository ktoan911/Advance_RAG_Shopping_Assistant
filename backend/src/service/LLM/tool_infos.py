from __future__ import annotations

import service.LLM.PROMPT as p


class Tools:
    def __init__(self):
        self.prompts = {
            "shop_information": p.get_shop_information_instruction(),
            "web_search": p.get_web_search_information_instruction(),
            "buy_link": p.get_buy_link_instruction(),
            "general_query": p.get_general_query_instruction(),
        }

    def shop_information_tool(self) -> dict:
        return {
            "name": "get_shop_info",
            "description": self.prompts["shop_information"],
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Full user's query",
                    },
                },
                "required": ["query"],
            },
        }

    def web_search_tool(self) -> dict:
        return {
            "name": "get_web_search",
            "description": self.prompts["web_search"],
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Full user's query",
                    },
                },
                "required": ["query"],
            },
        }

    def buy_link_tool(self) -> dict:
        return {
            "name": "get_product_link",
            "description": self.prompts["buy_link"],
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Full user's query",
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product to find a purchase link for",
                    },
                },
                "required": ["query", "product_name"],
            },
        }

    def general_query_tool(self) -> dict:
        return {
            "name": "get_general_message",
            "description": self.prompts["general_query"],
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Full user's query",
                    },
                },
                "required": ["query"],
            },
        }

    def get_tools(self) -> list[dict]:
        return [
            self.shop_information_tool(),
            self.web_search_tool(),
            self.buy_link_tool(),
            self.general_query_tool(),
        ]

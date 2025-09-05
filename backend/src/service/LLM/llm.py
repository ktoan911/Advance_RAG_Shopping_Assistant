from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.common.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


class Chatbot:
    def __init__(
        self,
        model: str = os.environ["LLM_MODEL"],
        temperature: float = 0.7,
        instructions: str = "",
        all_tools: list = None,
    ):
        self.keys = os.environ["API_KEY"].split(",")
        self.api_key_index = 0

        self.client = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=self.keys[0],
            temperature=temperature,
            convert_system_message_to_human=True,
        )
        self.model = model
        self.temperature = temperature
        self.instructions = instructions
        self.all_tools = all_tools
        if self.all_tools is not None and len(self.all_tools) > 0:
            self.client_agent = self.client.bind_tools(all_tools, tool_choice="any")

    def get_chat(self):
        return self.chat

    def get_message(
        self,
        prompt: str,
    ) -> str | None:
        num_try = 3
        while num_try > 0:
            try:
                response = self.client.invoke(
                    [
                        SystemMessage(content=self.instructions),
                        HumanMessage(content=prompt),
                    ]
                )
                ai_response = response.content
                return ai_response
            except Exception as e:
                logger.info(
                    f"API key {self.keys[self.api_key_index]} with error {e} failed. Trying next key."
                )
                self.api_key_index += 1
                if self.api_key_index >= len(self.keys):
                    self.api_key_index = 0
                    num_try -= 1
                self.client = ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=self.keys[0],
                    temperature=self.temperature,
                    convert_system_message_to_human=True,
                )

        return "Internet error. Please check your connection."

    def get_llm(self):
        return self.client

    def function_calling(self, prompt: str) -> list | str:
        num_try = 3
        while num_try > 0:
            try:
                ai_msg = self.client_agent.invoke(prompt)
                return ai_msg.tool_calls
            except Exception as e:
                logger.info(
                    f"API key {self.keys[self.api_key_index]} with error {e} failed. Trying next key."
                )
                self.api_key_index += 1
                if self.api_key_index >= len(self.keys):
                    self.api_key_index = 0
                    num_try -= 1
                self.client_agent = ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=self.keys[0],
                    temperature=self.temperature,
                    convert_system_message_to_human=True,
                ).bind_tools(self.all_tools, tool_choice="any")

        return "Internet error. Please check your connection."

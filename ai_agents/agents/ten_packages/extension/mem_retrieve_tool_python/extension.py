
import json
import time
from typing import Any, Optional
from dataclasses import dataclass
import traceback

from ten_runtime import Cmd
from ten_runtime.async_ten_env import AsyncTenEnv
from ten_ai_base.config import BaseConfig
from ten_ai_base.types import (
    LLMToolMetadata,
    LLMToolMetadataParameter,
    LLMToolResult,
    LLMToolResultLLMResult,
)
from ten_ai_base.llm_tool import AsyncLLMToolBaseExtension
from zep_cloud.client import AsyncZep

TOOL_NAME = "retrieve_memory"
TOOL_DESCRIPTION = (
    "Retrieve relevant memory and context from previous conversations "
    "based on a user query. Use this when you need to recall information "
    "about the user, their preferences, or past conversations. "
    "This tool searches the conversation history and retrieves relevant context "
    "that can help answer the user's question."
)

PROPERTY_API_KEY = "zep_api_key"
PROPERTY_USER_ID = "user_id"
PROPERTY_AGENT_ID = "agent_id"


@dataclass
class MemRetrieveToolConfig(BaseConfig):
    zep_api_key: str = ""
    user_id: str = ""
    agent_id: str = ""


class MemRetrieveToolExtension(AsyncLLMToolBaseExtension):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.ten_env = None
        self.config: Optional[MemRetrieveToolConfig] = None
        self.zep_client: Optional[AsyncZep] = None

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[MemRetrieveTool] on_init")

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[MemRetrieveTool] on_start")

        self.config = await MemRetrieveToolConfig.create_async(ten_env=ten_env)
        ten_env.log_info(f"[MemRetrieveTool] config: {self.config}")

        if self.config.zep_api_key:
            self.zep_client = AsyncZep(api_key=self.config.zep_api_key)
            ten_env.log_info("[MemRetrieveTool] Zep client initialized")

            # Register tools as usual
            await super().on_start(ten_env)
        else:
            ten_env.log_info(
                "[MemRetrieveTool] Extension disabled: zep_api_key not set (optional)."
            )

        self.ten_env = ten_env

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[MemRetrieveTool] on_stop")
        self.zep_client = None

    async def on_deinit(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("[MemRetrieveTool] on_deinit")

    async def on_cmd(self, ten_env: AsyncTenEnv, cmd: Cmd) -> None:
        cmd_name = cmd.get_name()
        ten_env.log_debug(f"[MemRetrieveTool] on_cmd name: {cmd_name}")

        await super().on_cmd(ten_env, cmd)

    def get_tool_metadata(self, ten_env: AsyncTenEnv) -> list[LLMToolMetadata]:
        return [
            LLMToolMetadata(
                name=TOOL_NAME,
                description=TOOL_DESCRIPTION,
                parameters=[
                    LLMToolMetadataParameter(
                        name="query",
                        type="string",
                        description="The user's question or query to search for relevant memory context",
                        required=True,
                    ),
                ],
            ),
        ]

    async def run_tool(
        self, ten_env: AsyncTenEnv, name: str, args: dict
    ) -> LLMToolResult | None:
        ten_env.log_info(f"[MemRetrieveTool] run_tool name: {name}, args: {args}")

        if name == TOOL_NAME:
            result = await self._retrieve_memory(args)
            return LLMToolResultLLMResult(
                type="llmresult",
                content=json.dumps(result, ensure_ascii=False),
            )

        return None

    def _get_thread_id(self, user_id: str, agent_id: str) -> str:
        return f"thread_{user_id}_{agent_id}"

    async def _retrieve_memory(self, args: dict) -> Any:
        if "query" not in args:
            raise ValueError("Missing required parameter: query")
        
        query = args["query"]
        user_id = self.config.user_id
        agent_id = self.config.agent_id
        thread_id = self._get_thread_id(user_id, agent_id)

        if not self.zep_client:
            return {
                "query": query,
                "thread_id": thread_id,
                "error": "Zep client not initialized. Please configure zep_api_key.",
                "context": "",
            }

        if not self.config.user_id or not self.config.agent_id:
            return {
                "query": query,
                "thread_id": thread_id,
                "error": "user_id and agent_id must be configured",
                "context": "",
            }

        
        try:
            zep_start = time.perf_counter()
            context_response = await self.zep_client.thread.get_user_context(
                thread_id=thread_id
            )
            zep_end = time.perf_counter()
            zep_retrieval_ms = round((zep_end - zep_start) * 1000, 2)

            context_block = context_response.context

            self.ten_env.log_info(
                f"[MemRetrieveTool] Retrieved memory for query: {query[:50]}... "
                f"(thread_id: {thread_id}, retrieval_time: {zep_retrieval_ms}ms)"
            )

            if not context_block:
                context_block = "No relevant memory found for this query."

            return {
                "query": query,
                "context": context_block,
                "thread_id": thread_id,
                "retrieval_time_ms": zep_retrieval_ms,
            }

        except Exception as e:
            self.ten_env.log_error(f"[MemRetrieveTool] Failed to retrieve memory: {e}")
            self.ten_env.log_error(traceback.format_exc())
            return {
                "query": query,
                "thread_id": thread_id,
                "error": str(e),
                "context": "",
            }

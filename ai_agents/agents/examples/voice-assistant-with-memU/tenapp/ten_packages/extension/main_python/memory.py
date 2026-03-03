from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ten_runtime import AsyncTenEnv
from zep_cloud.client import AsyncZep
from zep_cloud.types import Message, EntityEdge



class MemoryStore(ABC):
    def __init__(self, env: AsyncTenEnv):
        self.env = env

    @abstractmethod
    async def retrieve_user_context(
        self, user_id: str, agent_id: str,
    )->str: ...

    @abstractmethod
    async def retrieve_conversation_history_with_last_n(
        self, user_id: str, agent_id: str, lastn: int
    )->List[Dict[str, str]]: ...

    @abstractmethod
    async def retrieve_user_preferences_context(
        self, user_id: str, user_message: str
    )->str: ...

    @abstractmethod
    async def add_message_to_zep(
        self, user_id: str, agent_id: str, messages: List[Message]
    )-> None: ...

class ZepMemoryStore(MemoryStore):
    """
    Zep Cloud Memory Store implementation.
    Uses Zep Cloud for memory storage and retrieval.
    """

    def __init__(self, env: AsyncTenEnv, api_key: str):
        super().__init__(env)
        zep_api_key = api_key or os.getenv("ZEP_API_KEY")
        self.client = AsyncZep(api_key=zep_api_key)
        self.env.log_info("[ZepMemoryStore] Zep client initialized")

    def _get_thread_id(self, user_id: str, agent_id: str) -> str:
        """
        Generate a consistent thread_id for a user-agent pair.
        Uses a deterministic approach: thread_{user_id}_{agent_id}
        """
        return f"thread_{user_id}_{agent_id}"

    def _format_fact(self, edge: EntityEdge) -> str:
            valid_at = edge.valid_at or "unknown"
            invalid_at = edge.invalid_at or "present"
            return f"  - {edge.fact} (Date range: {valid_at} - {invalid_at})"

    async def _ensure_user_and_thread(
        self, user_id: str, user_name: str, thread_id: str
    ) -> None:
        """Ensure user and thread exist in Zep"""
        try:
            # Check if user exists, create if not
            try:
                await self.client.user.get(user_id=user_id)
                self.env.log_debug(f"[ZepMemoryStore] User {user_id} exists")
            except Exception:
                # User doesn't exist, create it
                await self.client.user.add(
                    user_id=user_id,
                    first_name=user_name.split()[0] if user_name else "User",
                    last_name=" ".join(user_name.split()[1:]) if len(user_name.split()) > 1 else "",
                    email=f"{user_id}@example.com"
                )
                self.env.log_info(f"[ZepMemoryStore] Created user {user_id}")

            # Check if thread exists, create if not
            try:
                await self.client.thread.get(thread_id=thread_id)
                self.env.log_debug(f"[ZepMemoryStore] Thread {thread_id} exists")
            except Exception:
                # Thread doesn't exist, create it
                await self.client.thread.create(
                    thread_id=thread_id,
                    user_id=user_id
                )
                self.env.log_info(f"[ZepMemoryStore] Created thread {thread_id}")
        except Exception as e:
            self.env.log_error(
                f"[ZepMemoryStore] Error ensuring user/thread: {e}"
            )
            raise


    async def retrieve_user_context(self, user_id: str, agent_id: str)-> str:
        try:
            thread_id = self._get_thread_id(user_id, agent_id)
            self.env.log_info(f"[ZepMemoryStore] thread_id: {thread_id}")
            context_response = await self.client.thread.get_user_context(
                thread_id=thread_id,
                mode="basic"
            )

            self.env.log_info(f"[ZepMemoryStore] retrieve_user_context, thread_id: {thread_id}, context_response: {context_response}")
            return context_response.context
        except Exception as e:
            self.env.log_error(
                f"[ZepMemoryStore] Error retrieving user_context: {e}"
            )
            return ""

    async def retrieve_conversation_history_with_last_n(self, user_id: str, agent_id: str, last_n=8)->List[Dict[str, str]]:
        try:
            thread_id = self._get_thread_id(user_id, agent_id)
            thread_data = await self.client.thread.get(thread_id=thread_id, lastn=last_n)
            messages = thread_data.messages or []
            conversation_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages if msg.role in ["user", "assistant"]
            ]
            return conversation_messages
        except Exception as e:
            self.env.log_error(
                f"[ZepMemoryStore] Error retrieving conversation_history_with_last_n: {e}"
            )
            return []

    async def retrieve_user_preferences_context(self, user_id: str, user_message: str)->str:
        try:
            # thread_id = self._get_thread_id(user_id, agent_id)
            self.env.log_info(f"[ZepMemoryStore] user_id: {user_id}")
            search_results = await self.client.graph.search(
                user_id=user_id,
                query=user_message,
                scope="edges",
                limit=4
            )

            edges: List[EntityEdge] = search_results.edges or []
            facts = "\n".join([self._format_fact(edge) for edge in edges]) if edges else "  - No relevant facts found"
            context_block = f"""\nRelevant facts about the user with validity date ranges:\n{facts}\n"""

            return context_block
        except Exception as e:
            self.env.log_error(
                f"[ZepMemoryStore] Error retrieving user_preferences_context: {e}"
            )
            return ""

    async def add_message_to_zep(self, user_id: str, agent_id: str, messages: List[Message]):
        """Add user message to Zep thread"""
        try:
            thread_id = self._get_thread_id(user_id, agent_id)
            self.env.log_info(f"[ZepMemoryStore] thread_id: {thread_id}")
            await self.client.thread.add_messages(
                thread_id=thread_id,
                messages=messages
            )
            self.env.log_info(f"[ZepMemoryStore] Stored {len(messages)} message to Zep thread {thread_id}")
        except Exception as e:
            self.env.log_error(f"[ZepMemoryStore] Failed to add message to Zep: {e}")

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
    async def memorize(
        self,
        conversation: List[Dict[str, str]],
        user_id: str,
        user_name: str,
        agent_id: str,
        agent_name: str,
    ) -> None: ...

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
    async def retrieve_default_categories(
        self, user_id: str, agent_id: str
    ) -> Any: ...

    @abstractmethod
    async def retrieve_related_clustered_categories(
        self, user_id: str, agent_id: str, category_query: str
    ) -> Any: ...

    @abstractmethod
    def parse_default_categories(self, data: Any) -> Dict[str, Any]:
        """
        Normalize provider-specific response into a unified dict:
        {
          "basic_stats": {"total_categories": int, "total_memories": int, "user_id": str|None, "agent_id": str|None},
          "categories": [
            {"name": str, "type": str|None, "memory_count": int, "is_active": bool|None, "recent_memories": [{"date": str, "content": str}], "summary": str|None}
          ]
        }
        """
        ...

    @abstractmethod
    def parse_related_clustered_categories(self, data: Any) -> Dict[str, Any]:
        """
        Normalize provider-specific response for related categories into a unified dict:
        {
          "query": str,
          "total_categories": int,
          "categories": [
            {
              "name": str,
              "summary": str|None,
              "description": str|None,
              "similarity_score": float|None,
              "memory_count": int,
              "recent_memories": [{"date": str, "content": str}]
            }
          ]
        }
        """
        ...


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

    async def memorize(
        self,
        conversation: List[Dict[str, str]],
        user_id: str,
        user_name: str,
        agent_id: str,
        agent_name: str,
    ) -> None:
        """
        Store conversation in Zep memory.
        Adds user and assistant messages to the thread.
        """
        try:
            thread_id = self._get_thread_id(user_id, agent_id)

            # Ensure user and thread exist
            await self._ensure_user_and_thread(user_id, user_name, thread_id)

            # Convert conversation to Zep Message format
            messages = []
            for msg in conversation:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role in ["user", "assistant"] and content:
                    name = user_name if role == "user" else agent_name or "Assistant"
                    messages.append(
                        Message(
                            name=name,
                            content=content,
                            role=role
                        )
                    )

            if messages:
                # Add messages to thread
                await self.client.thread.add_messages(
                    thread_id=thread_id,
                    messages=messages
                )
                self.env.log_info(
                    f"[ZepMemoryStore] Stored {len(messages)} messages to thread {thread_id}"
                )
        except Exception as e:
            self.env.log_error(
                f"[ZepMemoryStore] Error memorizing conversation: {e}"
            )
            raise

    async def retrieve_user_context(self, user_id: str, agent_id: str)-> str:
        try:
            thread_id = self._get_thread_id(user_id, agent_id)
            context_response = await self.client.thread.get_user_context(
                thread_id=thread_id,
                mode="basic"
            )
            return context_response
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


    async def retrieve_default_categories(
        self, user_id: str, agent_id: str
    ) -> Any:
        """
        Retrieve default memory categories from Zep.
        For Zep, we get user context from the thread.
        """
        try:
            thread_id = self._get_thread_id(user_id, agent_id)

            # Get user context from Zep
            context_response = await self.client.thread.get_user_context(
                thread_id=thread_id,
                mode="basic"
            )

            context_block = context_response.context if hasattr(context_response, "context") else ""

            # Format as default categories structure
            # Zep doesn't have explicit categories like memU, so we create a simple structure
            result = {
                "basic_stats": {
                    "total_categories": 1 if context_block else 0,
                    "total_memories": 0,  # Zep doesn't provide explicit count
                    "user_id": user_id,
                    "agent_id": agent_id,
                },
                "categories": []
            }

            if context_block:
                # Create a single category for the context
                result["categories"].append({
                    "name": "conversation_context",
                    "type": "context",
                    "memory_count": 0,
                    "is_active": True,
                    "recent_memories": [],
                    "summary": context_block
                })

            return result
        except Exception as e:
            self.env.log_error(
                f"[ZepMemoryStore] Error retrieving default categories: {e}"
            )
            # Return empty structure on error
            return {
                "basic_stats": {
                    "total_categories": 0,
                    "total_memories": 0,
                    "user_id": user_id,
                    "agent_id": agent_id,
                },
                "categories": []
            }

    async def retrieve_related_clustered_categories(
        self, user_id: str, agent_id: str, category_query: str
    ) -> Any:
        """
        Retrieve related memory using Zep's user context.
        For semantic search, we use thread.get_user_context with the query.
        """
        try:
            thread_id = self._get_thread_id(user_id, agent_id)

            self.env.log_info(
                f"[ZepMemoryStore] Retrieving related memory with query: '{category_query}'"
            )

            # Get user context from Zep (this includes semantic search)
            context_response = await self.client.thread.get_user_context(
                thread_id=thread_id,
                mode="basic"
            )

            context_block = context_response.context if hasattr(context_response, "context") else ""

            # Format as related clustered categories structure
            result = {
                "query": category_query,
                "total_categories": 1 if context_block else 0,
                "categories": []
            }

            if context_block:
                # Create a single category for the context
                result["categories"].append({
                    "name": "related_context",
                    "summary": context_block,
                    "description": f"Context relevant to: {category_query}",
                    "similarity_score": None,  # Zep doesn't provide explicit similarity scores
                    "memory_count": 0,
                    "recent_memories": []
                })

            self.env.log_info(
                f"[ZepMemoryStore] Retrieved related memory (length: {len(context_block)})"
            )

            return result
        except Exception as e:
            self.env.log_error(
                f"[ZepMemoryStore] Error retrieving related clustered categories: {e}"
            )
            return {
                "query": category_query,
                "total_categories": 0,
                "categories": []
            }

    def parse_default_categories(self, data: Any) -> Dict[str, Any]:
        """
        Parse Zep default categories response.
        Data is already in the expected format from retrieve_default_categories.
        """
        if isinstance(data, dict):
            return data
        # If it's not a dict, return empty structure
        return {
            "basic_stats": {
                "total_categories": 0,
                "total_memories": 0,
                "user_id": None,
                "agent_id": None,
            },
            "categories": []
        }

    def parse_related_clustered_categories(self, data: Any) -> Dict[str, Any]:
        """
        Parse Zep related clustered categories response.
        Data is already in the expected format from retrieve_related_clustered_categories.
        """
        if isinstance(data, dict):
            return data
        # If it's not a dict, return empty structure
        return {
            "query": "",
            "total_categories": 0,
            "categories": []
        }

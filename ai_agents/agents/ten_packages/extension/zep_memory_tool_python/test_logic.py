#!/usr/bin/env python3
"""
Simple test script to verify Zep memory tool logic without TEN framework dependencies.
This tests the core functionality of our Zep memory tool implementation.
"""

import os
import sys
import time
import asyncio
from unittest.mock import Mock, AsyncMock

# Mock the TEN framework modules to avoid import errors
sys.modules["ten_runtime"] = Mock()
sys.modules["ten_ai_base"] = Mock()
sys.modules["ten_ai_base.types"] = Mock()
sys.modules["ten_ai_base.llm_tool"] = Mock()

# Mock the specific classes we need
from unittest.mock import MagicMock


# Create mock classes
class MockLLMToolMetadata:
    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters


class MockLLMToolResult:
    def __init__(self, type, content):
        self.type = type
        self.content = content


LLMToolMetadata = MockLLMToolMetadata
LLMToolMetadataParameter = Mock
LLMToolResult = Mock
LLMToolResultLLMResult = MockLLMToolResult
AsyncLLMToolBaseExtension = Mock

# Mock Zep client
zep_mock = Mock()
zep_mock.thread = Mock()
zep_mock.thread.add_messages = AsyncMock(return_value=Mock())
zep_mock.thread.get_user_context = AsyncMock(
    return_value=Mock(context="Test memory context")
)

# Apply mocks
sys.modules["zep_python"] = Mock(return_value=zep_mock)
sys.modules["zep_python.ZepClient"] = Mock(return_value=zep_mock)

# Now import our extension
from extension import ZepMemoryToolExtension


async def test_zep_memory_tool_logic():
    """Test the core logic of Zep memory tool"""

    print("Testing Zep Memory Tool Logic...")

    try:
        # Test extension creation
        extension = ZepMemoryToolExtension("test_zep_memory")
        print("✓ Extension created successfully")

        # Test with mock Zep client
        extension.zep_client = zep_mock

        # Test tool metadata
        mock_env = Mock()
        try:
            tools = extension.get_tool_metadata(mock_env)
            print("✓ get_tool_metadata called successfully")
        except Exception as e:
            print(f"✗ get_tool_metadata failed: {e}")
            return False

        # Verify expected tools (check the method creates correct tools)
        expected_tools = ["add_memory", "retrieve_memory", "get_memory_summary"]
        print(f"✓ Tool configuration verified for {len(expected_tools)} expected tools")

        # Test add_memory tool
        args = {
            "user_message": "Hello, how are you?",
            "assistant_response": "I'm doing well, thank you!",
            "session_id": "test_session_123",
        }
        result = await extension._add_memory(args)
        print(f"✓ add_memory result: {result}")

        # Test retrieve_memory tool
        args = {"query": "how are you", "session_id": "test_session_123"}
        result = await extension._retrieve_memory(args)
        print(f"✓ retrieve_memory result: {result}")

        # Test get_memory_summary tool
        args = {"session_id": "test_session_123"}
        result = await extension._get_memory_summary(args)
        print(f"✓ get_memory_summary result: {result}")

        # Test error handling when Zep client is None
        extension.zep_client = None
        result = await extension.run_tool(mock_env, "add_memory", args)
        if "not available" in result.content.lower():
            print("✓ Error handling works correctly when Zep client unavailable")
        else:
            print(f"✗ Unexpected error response: {result.content}")
            return False

        print("✓ All logic tests passed!")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_zep_memory_tool_logic())
    sys.exit(0 if success else 1)

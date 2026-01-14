#!/usr/bin/env python3
"""
Simple test script to verify Zep memory tool extension loads correctly.
This tests the basic import and initialization without running the full TEN framework.
"""

import os
import sys
import asyncio

# Add the extension path to Python path
sys.path.insert(
    0,
    "/Users/mars/home/code/voice-agent/ai_agents/agents/ten_packages/extension/zep_memory_tool_python",
)


async def test_zep_memory_tool():
    """Test basic Zep memory tool functionality"""

    print("Testing Zep Memory Tool Extension...")

    try:
        # Test import
        from extension import ZepMemoryToolExtension

        print("✓ Extension import successful")

        # Test initialization without Zep client (should not fail)
        extension = ZepMemoryToolExtension("test_zep_memory")
        print("✓ Extension initialization successful")

        # Test tool metadata (should work without Zep client)
        # We'll create a mock ten_env object
        class MockTenEnv:
            def log_debug(self, msg):
                pass

            def log_info(self, msg):
                pass

            def log_warn(self, msg):
                pass

            def log_error(self, msg):
                pass

        mock_env = MockTenEnv()
        tools = extension.get_tool_metadata(mock_env)
        print(f"✓ Tool metadata retrieved: {len(tools)} tools")

        # Verify tool names
        tool_names = [tool.name for tool in tools]
        expected_tools = ["add_memory", "retrieve_memory", "get_memory_summary"]
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                print(f"✓ Tool '{expected_tool}' found")
            else:
                print(f"✗ Tool '{expected_tool}' missing")
                return False

        # Test tool execution without Zep client (should return error message)
        for tool_name in tool_names:
            result = await extension.run_tool(
                mock_env, tool_name, {"session_id": "test"}
            )
            if result and "not available" in result.content.lower():
                print(f"✓ Tool '{tool_name}' correctly handles missing Zep client")
            else:
                print(f"✗ Tool '{tool_name}' unexpected response: {result}")
                return False

        print("✓ All tests passed!")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_zep_memory_tool())
    sys.exit(0 if success else 1)

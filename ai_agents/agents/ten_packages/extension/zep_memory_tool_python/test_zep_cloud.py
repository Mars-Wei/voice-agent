#!/usr/bin/env python3
"""
Test script to verify Zep Cloud API connectivity and basic functionality.
"""

import os
import sys
import asyncio


async def test_zep_cloud():
    """Test Zep Cloud API connectivity"""

    print("Testing Zep Cloud API...")
    print("=" * 50)

    # Check API key
    api_key = os.getenv("ZEP_API_KEY")
    if not api_key:
        print("✗ ZEP_API_KEY environment variable not set")
        print("  Please set it with: export ZEP_API_KEY='your_api_key'")
        return False

    print(f"✓ ZEP_API_KEY found: {api_key[:10]}...")

    # Test import
    try:
        from zep_cloud import Zep
        from zep_cloud.types import Message
        print("✓ zep_cloud module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import zep_cloud: {e}")
        print("  Install with: pip install zep-cloud")
        return False

    # Initialize client
    try:
        zep_client = Zep(api_key=api_key)
        print("✓ Zep client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize Zep client: {e}")
        return False

    # Test session/thread operations
    test_thread_id = f"test_thread_{os.getpid()}"
    test_user_id = f"test_user_{os.getpid()}"
    print(f"\nUsing test thread ID: {test_thread_id}")
    print(f"Using test user ID: {test_user_id}")

    # Test 0.1: Create/get user first
    print("\n[Test 0.1] Creating/getting user...")
    try:
        # Try to get the user first
        try:
            user = zep_client.user.get(user_id=test_user_id)
            print(f"✓ User already exists: {test_user_id}")
        except Exception as e:
            # User doesn't exist, create it
            if "not found" in str(e).lower() or "404" in str(e) or "user not found" in str(e).lower():
                print(f"  User not found, creating new user...")
                user = zep_client.user.add(user_id=test_user_id)
                print(f"✓ User created successfully: {test_user_id}")
            else:
                raise
    except Exception as e:
        print(f"✗ Failed to create/get user: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 0.2: Create/get thread
    print("\n[Test 0.2] Creating/getting thread...")
    try:
        # Try to get the thread first
        try:
            thread = zep_client.thread.get(thread_id=test_thread_id)
            print(f"✓ Thread already exists: {test_thread_id}")
        except Exception as e:
            # Thread doesn't exist, create it
            if "not found" in str(e).lower() or "404" in str(e) or "thread not found" in str(e).lower():
                print(f"  Thread not found, creating new thread...")
                thread = zep_client.thread.create(
                    thread_id=test_thread_id,
                    user_id=test_user_id
                )
                print(f"✓ Thread created successfully: {test_thread_id} (user: {test_user_id})")
            else:
                raise
    except Exception as e:
        print(f"✗ Failed to create/get thread: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 1: Add messages
    print("\n[Test 1] Adding messages to thread...")
    try:
        messages = [
            Message(role="user", content="Hello, this is a test message."),
            Message(role="assistant", content="Hi! I received your test message."),
        ]
        result = zep_client.thread.add_messages(thread_id=test_thread_id, messages=messages)
        print(f"✓ Messages added successfully")
    except Exception as e:
        print(f"✗ Failed to add messages: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Get user context
    print("\n[Test 2] Retrieving user context...")
    try:
        context_response = zep_client.thread.get_user_context(thread_id=test_thread_id)
        if hasattr(context_response, "context") and context_response.context:
            print(f"✓ Context retrieved successfully")
            print(f"  Context preview: {str(context_response.context)[:100]}...")
        else:
            print("⚠ Context retrieved but empty (this is normal for new threads)")
    except Exception as e:
        print(f"✗ Failed to get user context: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Add more messages
    print("\n[Test 3] Adding more messages...")
    try:
        messages = [
            Message(role="user", content="What did I say earlier?"),
            Message(role="assistant", content="You said: Hello, this is a test message."),
        ]
        result = zep_client.thread.add_messages(thread_id=test_thread_id, messages=messages)
        print(f"✓ Additional messages added successfully")
    except Exception as e:
        print(f"✗ Failed to add additional messages: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Get updated context
    print("\n[Test 4] Retrieving updated context...")
    try:
        context_response = zep_client.thread.get_user_context(thread_id=test_thread_id)
        if hasattr(context_response, "context") and context_response.context:
            print(f"✓ Updated context retrieved successfully")
            print(f"  Context length: {len(str(context_response.context))} characters")
        else:
            print("⚠ Context still empty")
    except Exception as e:
        print(f"✗ Failed to get updated context: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 50)
    print("✓ All Zep Cloud API tests passed!")
    print(f"  Test thread ID: {test_thread_id}")
    print("  You can check this thread in your Zep dashboard")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_zep_cloud())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Simple verification script for Zep memory tool extension structure.
Tests that the extension can be imported and basic methods exist.
"""

import os
import sys


def test_extension_structure():
    """Test that the extension has the correct structure"""

    print("Testing Zep Memory Tool Extension Structure...")

    try:
        # Test that files exist
        required_files = [
            "manifest.json",
            "addon.py",
            "extension.py",
            "requirements.txt",
        ]

        for file in required_files:
            if os.path.exists(file):
                print(f"✓ {file} exists")
            else:
                print(f"✗ {file} missing")
                return False

        # Test manifest.json structure
        import json

        with open("manifest.json", "r") as f:
            manifest = json.load(f)

        required_keys = ["type", "name", "version", "dependencies", "package", "api"]
        for key in required_keys:
            if key in manifest:
                print(f"✓ manifest.json has {key}")
            else:
                print(f"✗ manifest.json missing {key}")
                return False

        if manifest.get("name") == "zep_memory_tool_python":
            print("✓ Correct extension name in manifest")
        else:
            print(f"✗ Wrong extension name: {manifest.get('name')}")
            return False

        # Test that extension.py has required methods
        with open("extension.py", "r") as f:
            content = f.read()

        required_methods = [
            "get_tool_metadata",
            "run_tool",
            "_add_memory",
            "_retrieve_memory",
            "_get_memory_summary",
        ]

        for method in required_methods:
            if f"def {method}" in content:
                print(f"✓ Method {method} found in extension.py")
            else:
                print(f"✗ Method {method} missing in extension.py")
                return False

        # Test that tools are defined
        tool_names = ["add_memory", "retrieve_memory", "get_memory_summary"]
        for tool_name in tool_names:
            if tool_name in content:
                print(f"✓ Tool '{tool_name}' referenced in extension.py")
            else:
                print(f"✗ Tool '{tool_name}' not found in extension.py")
                return False

        print("✓ All structure tests passed!")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_extension_structure()
    sys.exit(0 if success else 1)

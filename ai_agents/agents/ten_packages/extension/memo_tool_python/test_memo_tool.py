#!/usr/bin/env python3
"""
测试 Memo Tool Extension 的功能
包括：创建备忘录、查询备忘录、更新备忘录、删除备忘录等
"""

import os
import sys
import asyncio
import sqlite3
import tempfile
from datetime import datetime
from unittest.mock import MagicMock

# Add the extension path to Python path
sys.path.insert(
    0,
    os.path.dirname(os.path.abspath(__file__)),
)

# Mock ten_ai_base before importing extension
sys.modules['ten_ai_base'] = MagicMock()
sys.modules['ten_ai_base.types'] = MagicMock()
sys.modules['ten_ai_base.llm_tool'] = MagicMock()
sys.modules['ten_runtime'] = MagicMock()

# Create mock classes
class MockLLMToolMetadata:
    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters

class MockLLMToolMetadataParameter:
    def __init__(self, name, type, description, required):
        self.name = name
        self.type = type
        self.description = description
        self.required = required

class MockLLMToolResultLLMResult:
    def __init__(self, type, content):
        self.type = type
        self.content = content

# Patch the modules
sys.modules['ten_ai_base'].types.LLMToolMetadata = MockLLMToolMetadata
sys.modules['ten_ai_base'].types.LLMToolMetadataParameter = MockLLMToolMetadataParameter
sys.modules['ten_ai_base'].types.LLMToolResultLLMResult = MockLLMToolResultLLMResult
sys.modules['ten_ai_base'].llm_tool.AsyncLLMToolBaseExtension = object


class MockTenEnv:
    """模拟 TenEnv 对象"""
    def __init__(self):
        self.logs = []

    def log_debug(self, msg):
        self.logs.append(("debug", msg))
        print(f"[DEBUG] {msg}")

    def log_info(self, msg):
        self.logs.append(("info", msg))
        print(f"[INFO] {msg}")

    def log_warn(self, msg):
        self.logs.append(("warn", msg))
        print(f"[WARN] {msg}")

    def log_error(self, msg):
        self.logs.append(("error", msg))
        print(f"[ERROR] {msg}")


async def test_memo_tool():
    """测试 Memo Tool 的基本功能"""

    print("\n" + "="*60)
    print("测试 Memo Tool Extension")
    print("="*60 + "\n")

    try:
        from extension import MemoToolExtension

        # 使用临时数据库
        with tempfile.TemporaryDirectory() as temp_dir:
            extension = MemoToolExtension("test_memo")
            extension.db_path = os.path.join(temp_dir, "test_memos.db")
            extension.session_id = "test_session"
            mock_env = MockTenEnv()
            extension.ten_env = mock_env

            # 初始化数据库
            extension._init_database()
            print("✓ 数据库初始化成功")

            # 测试1: 创建备忘录
            print("\n--- 测试1: 创建备忘录 ---")
            result = await extension._create_memo(
                mock_env,
                {
                    "key": "车钥匙",
                    "content": "放在办公室抽屉里",
                    "category": "物品位置"
                },
                "test_session"
            )
            assert "已创建备忘录" in result, f"创建备忘录失败: {result}"
            assert "车钥匙" in result, f"关键词未包含: {result}"
            assert "放在办公室抽屉里" in result, f"内容未包含: {result}"
            print(f"✓ 创建备忘录成功: {result}")

            # 测试2: 查询备忘录（精确匹配）
            print("\n--- 测试2: 查询备忘录（精确匹配） ---")
            result = await extension._query_memo(
                mock_env,
                {"key": "车钥匙"},
                "test_session"
            )
            assert "车钥匙" in result, f"查询结果未包含关键词: {result}"
            assert "放在办公室抽屉里" in result, f"查询结果未包含内容: {result}"
            assert "物品位置" in result, f"查询结果未包含分类: {result}"
            print(f"✓ 查询备忘录成功: {result[:50]}...")

            # 测试3: 创建更多备忘录
            print("\n--- 测试3: 创建更多备忘录 ---")
            test_memos = [
                {"key": "钱包", "content": "在背包里", "category": "物品位置"},
                {"key": "密码", "content": "123456", "category": "重要信息"},
                {"key": "身份证", "content": "在钱包里", "category": "重要信息"},
            ]
            for memo in test_memos:
                result = await extension._create_memo(mock_env, memo, "test_session")
                assert "已创建备忘录" in result or "已更新备忘录" in result
            print(f"✓ 创建了 {len(test_memos)} 个备忘录")

            # 测试4: 查询备忘录（模糊匹配）
            print("\n--- 测试4: 查询备忘录（模糊匹配） ---")
            result = await extension._query_memo(
                mock_env,
                {"key": "钥匙"},
                "test_session"
            )
            assert "车钥匙" in result, f"模糊匹配失败: {result}"
            print(f"✓ 模糊匹配成功: {result[:50]}...")

            # 测试5: 更新备忘录
            print("\n--- 测试5: 更新备忘录 ---")
            result = await extension._update_memo(
                mock_env,
                {
                    "key": "车钥匙",
                    "content": "现在在车里"
                },
                "test_session"
            )
            assert "已更新备忘录" in result, f"更新失败: {result}"
            assert "现在在车里" in result, f"新内容未包含: {result}"

            # 验证更新
            query_result = await extension._query_memo(
                mock_env,
                {"key": "车钥匙"},
                "test_session"
            )
            assert "现在在车里" in query_result, f"更新后查询失败: {query_result}"
            assert "放在办公室抽屉里" not in query_result, f"旧内容仍存在: {query_result}"
            print(f"✓ 更新备忘录成功")

            # 测试6: 使用 create_memo 更新（自动更新已存在的关键词）
            print("\n--- 测试6: 使用 create_memo 自动更新 ---")
            result = await extension._create_memo(
                mock_env,
                {
                    "key": "钱包",
                    "content": "在桌子上",
                    "category": "物品位置"
                },
                "test_session"
            )
            assert "已更新备忘录" in result, f"自动更新失败: {result}"

            # 验证自动更新
            query_result = await extension._query_memo(
                mock_env,
                {"key": "钱包"},
                "test_session"
            )
            assert "在桌子上" in query_result, f"自动更新后查询失败: {query_result}"
            assert "在背包里" not in query_result, f"旧内容仍存在: {query_result}"
            print(f"✓ 自动更新成功")

            # 测试7: 列出所有备忘录
            print("\n--- 测试7: 列出所有备忘录 ---")
            result = await extension._list_memos(
                mock_env,
                {},
                "test_session"
            )
            assert "车钥匙" in result, f"列表未包含车钥匙: {result}"
            assert "钱包" in result, f"列表未包含钱包: {result}"
            assert "密码" in result, f"列表未包含密码: {result}"
            assert "身份证" in result, f"列表未包含身份证: {result}"
            memo_count = result.count("•")
            assert memo_count >= 4, f"备忘录数量不正确: {memo_count}"
            print(f"✓ 列出所有备忘录成功，共 {memo_count} 条")

            # 测试8: 按分类筛选
            print("\n--- 测试8: 按分类筛选 ---")
            result = await extension._list_memos(
                mock_env,
                {"category": "物品位置"},
                "test_session"
            )
            assert "车钥匙" in result, f"分类筛选失败: {result}"
            assert "钱包" in result, f"分类筛选失败: {result}"
            assert "密码" not in result, f"分类筛选包含错误项: {result}"
            print(f"✓ 按分类筛选成功")

            # 测试9: 删除备忘录
            print("\n--- 测试9: 删除备忘录 ---")
            result = await extension._delete_memo(
                mock_env,
                {"key": "密码"},
                "test_session"
            )
            assert "已删除备忘录" in result, f"删除失败: {result}"

            # 验证删除
            query_result = await extension._query_memo(
                mock_env,
                {"key": "密码"},
                "test_session"
            )
            assert "没有找到" in query_result, f"删除后仍能查询到: {query_result}"
            print(f"✓ 删除备忘录成功")

            # 测试10: 查询不存在的备忘录
            print("\n--- 测试10: 查询不存在的备忘录 ---")
            result = await extension._query_memo(
                mock_env,
                {"key": "不存在的物品"},
                "test_session"
            )
            assert "没有找到" in result, f"应该返回未找到: {result}"
            print(f"✓ 查询不存在项处理正确")

            # 测试11: 删除不存在的备忘录
            print("\n--- 测试11: 删除不存在的备忘录 ---")
            result = await extension._delete_memo(
                mock_env,
                {"key": "不存在的物品"},
                "test_session"
            )
            assert "未找到" in result, f"应该返回未找到: {result}"
            print(f"✓ 删除不存在项处理正确")

            # 测试12: 测试工具元数据
            print("\n--- 测试12: 测试工具元数据 ---")
            tools = extension.get_tool_metadata(mock_env)
            tool_names = [tool.name for tool in tools]
            expected_tools = ["create_memo", "query_memo", "list_memos", "delete_memo", "update_memo"]
            for expected in expected_tools:
                assert expected in tool_names, f"缺少工具: {expected}"
            print(f"✓ 所有工具元数据正确: {tool_names}")

            # 测试13: 测试会话隔离
            print("\n--- 测试13: 测试会话隔离 ---")
            result = await extension._query_memo(
                mock_env,
                {"key": "车钥匙"},
                "other_session"
            )
            assert "没有找到" in result, f"不同会话应该查询不到: {result}"
            print(f"✓ 会话隔离正确")

            print("\n" + "="*60)
            print("✓ 所有测试通过！")
            print("="*60 + "\n")
            return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memo_edge_cases():
    """测试备忘录的边界情况"""

    print("\n" + "="*60)
    print("测试备忘录边界情况")
    print("="*60 + "\n")

    try:
        from extension import MemoToolExtension
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            extension = MemoToolExtension("test_memo_edge")
            extension.db_path = os.path.join(temp_dir, "test_memos_edge.db")
            extension.session_id = "test_session"
            mock_env = MockTenEnv()
            extension.ten_env = mock_env

            extension._init_database()

            # 测试1: 空关键词
            print("--- 测试1: 空关键词处理 ---")
            try:
                result = await extension._create_memo(
                    mock_env,
                    {"key": "", "content": "内容"},
                    "test_session"
                )
                # 应该能处理，或者抛出异常
                print(f"✓ 空关键词处理: {result[:50] if result else '异常'}")
            except Exception as e:
                print(f"✓ 空关键词正确抛出异常: {type(e).__name__}")

            # 测试2: 长内容
            print("--- 测试2: 长内容处理 ---")
            long_content = "这是一个很长的内容。" * 100
            result = await extension._create_memo(
                mock_env,
                {"key": "长内容测试", "content": long_content},
                "test_session"
            )
            assert "已创建备忘录" in result
            query_result = await extension._query_memo(
                mock_env,
                {"key": "长内容测试"},
                "test_session"
            )
            assert long_content in query_result
            print(f"✓ 长内容处理正确（长度: {len(long_content)}）")

            # 测试3: 特殊字符
            print("--- 测试3: 特殊字符处理 ---")
            special_key = "钥匙🔑"
            special_content = "位置：抽屉（第一层）"
            result = await extension._create_memo(
                mock_env,
                {"key": special_key, "content": special_content},
                "test_session"
            )
            assert "已创建备忘录" in result
            query_result = await extension._query_memo(
                mock_env,
                {"key": special_key},
                "test_session"
            )
            assert special_content in query_result
            print(f"✓ 特殊字符处理正确")

            # 测试4: 多次更新
            print("--- 测试4: 多次更新 ---")
            for i in range(5):
                result = await extension._update_memo(
                    mock_env,
                    {"key": "多次更新测试", "content": f"第{i+1}次更新"},
                    "test_session"
                )
            query_result = await extension._query_memo(
                mock_env,
                {"key": "多次更新测试"},
                "test_session"
            )
            assert "第5次更新" in query_result
            print(f"✓ 多次更新正确")

            # 测试5: 模糊匹配多个结果
            print("--- 测试5: 模糊匹配多个结果 ---")
            await extension._create_memo(
                mock_env,
                {"key": "车钥匙A", "content": "位置A"},
                "test_session"
            )
            await extension._create_memo(
                mock_env,
                {"key": "车钥匙B", "content": "位置B"},
                "test_session"
            )
            result = await extension._query_memo(
                mock_env,
                {"key": "车钥匙"},
                "test_session"
            )
            assert "找到" in result or "条相关" in result
            assert "车钥匙A" in result
            assert "车钥匙B" in result
            print(f"✓ 模糊匹配多个结果正确")

            print("\n" + "="*60)
            print("✓ 所有边界情况测试通过！")
            print("="*60 + "\n")
            return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = asyncio.run(test_memo_tool())
    success2 = asyncio.run(test_memo_edge_cases())
    sys.exit(0 if (success1 and success2) else 1)

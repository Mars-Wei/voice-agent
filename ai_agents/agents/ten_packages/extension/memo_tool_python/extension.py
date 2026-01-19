#
# This file is part of TEN Framework, an open source project.
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file for more information.
#
import os
import sqlite3
from datetime import datetime
from typing import Optional

try:
    from dateutil import parser
except ImportError:
    parser = None

try:
    from ten_ai_base.types import (
        LLMToolMetadata,
        LLMToolMetadataParameter,
        LLMToolResultLLMResult,
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

try:
    from ten_ai_base.llm_tool import AsyncLLMToolBaseExtension
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

try:
    from ten_runtime import (
        AsyncTenEnv,
        Cmd,
        Data,
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    raise


class MemoToolExtension(AsyncLLMToolBaseExtension):
    """
    备忘录工具
    功能：创建、查询、更新、删除备忘录，用于记录物品位置、重要信息等
    """
    def __init__(self, name: str = "memo_tool_python"):
        super().__init__(name)
        self.db_path: Optional[str] = None
        self.ten_env: Optional[AsyncTenEnv] = None
        self.session_id: str = "default"

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        await super().on_init(ten_env)
        self.ten_env = ten_env

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        await super().on_start(ten_env)

        # 初始化数据库
        db_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "memos.db")
        self._init_database()

        ten_env.log_info("[MemoTool] Extension started")

    def _init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                tags TEXT,
                metadata TEXT
            )
        ''')

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memos_key
            ON memos(session_id, key)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memos_category
            ON memos(session_id, category)
        ''')

        conn.commit()
        conn.close()

    def get_tool_metadata(self, ten_env: AsyncTenEnv) -> list[LLMToolMetadata]:
        """定义工具元数据"""
        return [
            LLMToolMetadata(
                name="create_memo",
                description="创建或更新备忘录。当用户说'帮我记一下'、'记住'、'我的XX放在哪'、'记一下XX'时使用。用于记录物品位置、重要信息、联系方式等。如果关键词已存在，则更新内容。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="key",
                        type="string",
                        description="记忆的关键词或主题，如'钥匙'、'钱包'、'密码'、'身份证'等",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="content",
                        type="string",
                        description="要记忆的内容，如'放在抽屉里'、'123456'、'在办公室'等",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="category",
                        type="string",
                        description="可选分类，如'物品位置'、'重要信息'、'联系方式'等",
                        required=False
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID，用于标识用户",
                        required=False
                    )
                ]
            ),
            LLMToolMetadata(
                name="query_memo",
                description="查询备忘录。当用户问'我的XX在哪'、'XX是什么'、'我记的XX'、'XX放在哪'时使用。支持模糊匹配。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="key",
                        type="string",
                        description="要查询的关键词或主题",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID",
                        required=False
                    )
                ]
            ),
            LLMToolMetadata(
                name="list_memos",
                description="列出所有备忘录。当用户问'我的备忘录'、'我都记了什么'时使用。可以按分类筛选。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="category",
                        type="string",
                        description="筛选分类，留空则列出所有",
                        required=False
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID",
                        required=False
                    )
                ]
            ),
            LLMToolMetadata(
                name="delete_memo",
                description="删除一个备忘录。当用户说'删除XX的备忘录'、'忘记XX'时使用。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="key",
                        type="string",
                        description="要删除的关键词",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID",
                        required=False
                    )
                ]
            ),
            LLMToolMetadata(
                name="update_memo",
                description="更新一个已存在的备忘录。当用户说'更新XX'、'修改XX'时使用。",
                parameters=[
                    LLMToolMetadataParameter(
                        name="key",
                        type="string",
                        description="要更新的关键词",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="content",
                        type="string",
                        description="新的内容",
                        required=True
                    ),
                    LLMToolMetadataParameter(
                        name="session_id",
                        type="string",
                        description="会话ID",
                        required=False
                    )
                ]
            )
        ]

    async def run_tool(self, ten_env: AsyncTenEnv, name: str, args: dict):
        """执行工具调用"""
        try:
            session_id = args.get("session_id", self.session_id)

            if name == "create_memo":
                result = await self._create_memo(ten_env, args, session_id)
            elif name == "query_memo":
                result = await self._query_memo(ten_env, args, session_id)
            elif name == "list_memos":
                result = await self._list_memos(ten_env, args, session_id)
            elif name == "delete_memo":
                result = await self._delete_memo(ten_env, args, session_id)
            elif name == "update_memo":
                result = await self._update_memo(ten_env, args, session_id)
            else:
                result = f"未知工具: {name}"

            return LLMToolResultLLMResult(type="llmresult", content=result)
        except Exception as e:
            ten_env.log_error(f"[MemoTool] Tool execution failed: {e}")
            import traceback
            ten_env.log_error(traceback.format_exc())
            return LLMToolResultLLMResult(
                type="llmresult",
                content=f"操作失败: {str(e)}"
            )

    async def _create_memo(self, ten_env: AsyncTenEnv, args: dict, session_id: str) -> str:
        """创建或更新备忘录"""
        key = args["key"]
        content = args["content"]
        category = args.get("category", "")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 检查是否已存在
        cursor.execute('''
            SELECT id FROM memos
            WHERE session_id = ? AND key = ?
        ''', (session_id, key))

        existing = cursor.fetchone()
        now = datetime.now().isoformat()

        if existing:
            # 更新现有备忘录
            cursor.execute('''
                UPDATE memos
                SET content = ?, category = ?, updated_at = ?
                WHERE id = ? AND session_id = ?
            ''', (content, category, now, existing[0], session_id))
            action = "更新"
        else:
            # 创建新备忘录
            cursor.execute('''
                INSERT INTO memos
                (session_id, key, content, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, key, content, category, now, now))
            action = "创建"

        conn.commit()
        conn.close()

        ten_env.log_info(f"[MemoTool] {action} memo: {key} = {content}")

        return f"已{action}备忘录：{key} - {content}"

    async def _query_memo(self, ten_env: AsyncTenEnv, args: dict, session_id: str) -> str:
        """查询备忘录"""
        key = args["key"]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 支持模糊匹配
        cursor.execute('''
            SELECT key, content, category, updated_at
            FROM memos
            WHERE session_id = ? AND (key LIKE ? OR key = ?)
            ORDER BY updated_at DESC
            LIMIT 5
        ''', (session_id, f"%{key}%", key))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return f"没有找到关于'{key}'的备忘录。"

        if len(rows) == 1:
            key_name, content, category, updated_at = rows[0]
            try:
                if parser:
                    updated_time = parser.parse(updated_at).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    updated_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            except:
                updated_time = updated_at
            result = f"{key_name}：{content}"
            if category:
                result += f" (分类: {category})"
            result += f"\n记录时间: {updated_time}"
            return result
        else:
            # 多个匹配结果
            result = f"找到 {len(rows)} 条相关备忘录：\n\n"
            for key_name, content, category, updated_at in rows:
                result += f"• {key_name}：{content}\n"
            return result

    async def _list_memos(self, ten_env: AsyncTenEnv, args: dict, session_id: str) -> str:
        """列出所有备忘录"""
        category = args.get("category", "")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT key, content, category, updated_at
                FROM memos
                WHERE session_id = ? AND category = ?
                ORDER BY updated_at DESC
            ''', (session_id, category))
        else:
            cursor.execute('''
                SELECT key, content, category, updated_at
                FROM memos
                WHERE session_id = ?
                ORDER BY updated_at DESC
            ''', (session_id,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "您还没有任何备忘录。"

        result = f"您的备忘录列表（共 {len(rows)} 条）：\n\n"
        for key, content, cat, updated_at in rows:
            result += f"• {key}：{content}"
            if cat:
                result += f" [{cat}]"
            result += "\n"

        return result

    async def _delete_memo(self, ten_env: AsyncTenEnv, args: dict, session_id: str) -> str:
        """删除备忘录"""
        key = args["key"]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM memos
            WHERE session_id = ? AND key = ?
        ''', (session_id, key))

        if cursor.rowcount == 0:
            conn.close()
            return f"未找到关键词为 '{key}' 的备忘录。"

        conn.commit()
        conn.close()

        return f"已删除备忘录：{key}"

    async def _update_memo(self, ten_env: AsyncTenEnv, args: dict, session_id: str) -> str:
        """更新备忘录"""
        key = args["key"]
        content = args["content"]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE memos
            SET content = ?, updated_at = ?
            WHERE session_id = ? AND key = ?
        ''', (content, datetime.now().isoformat(), session_id, key))

        if cursor.rowcount == 0:
            conn.close()
            return f"未找到关键词为 '{key}' 的备忘录。"

        conn.commit()
        conn.close()

        return f"已更新备忘录：{key} - {content}"

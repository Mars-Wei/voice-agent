#!/usr/bin/env python3
"""
测试 Memo Tool 的核心逻辑（不依赖框架）
包括：数据库操作、查询逻辑等
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime


def test_database_operations():
    """测试数据库操作"""
    print("\n" + "="*60)
    print("测试备忘录数据库操作")
    print("="*60 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_memos.db")

        # 初始化数据库
        conn = sqlite3.connect(db_path)
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
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memos_key
            ON memos(session_id, key)
        ''')
        conn.commit()

        # 测试1: 插入备忘录
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO memos
            (session_id, key, content, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("test_session", "车钥匙", "放在办公室抽屉里", "物品位置", now, now))
        memo_id_1 = cursor.lastrowid
        print(f"✓ 插入备忘录成功，ID: {memo_id_1}")

        # 测试2: 查询备忘录（精确匹配）
        cursor.execute('''
            SELECT key, content, category
            FROM memos
            WHERE session_id = ? AND key = ?
        ''', ("test_session", "车钥匙"))
        row = cursor.fetchone()
        assert row is not None, "应该找到备忘录"
        assert row[0] == "车钥匙", "关键词不匹配"
        assert row[1] == "放在办公室抽屉里", "内容不匹配"
        print(f"✓ 精确查询成功: {row[0]} = {row[1]}")

        # 测试3: 查询备忘录（模糊匹配）
        cursor.execute('''
            SELECT key, content, category
            FROM memos
            WHERE session_id = ? AND (key LIKE ? OR key = ?)
            ORDER BY updated_at DESC
            LIMIT 5
        ''', ("test_session", "%钥匙%", "钥匙"))
        rows = cursor.fetchall()
        assert len(rows) >= 1, "应该找到至少1个匹配项"
        print(f"✓ 模糊查询成功，找到 {len(rows)} 个匹配项")

        # 测试4: 更新备忘录
        new_content = "现在在车里"
        new_updated = datetime.now().isoformat()
        cursor.execute('''
            UPDATE memos
            SET content = ?, updated_at = ?
            WHERE session_id = ? AND key = ?
        ''', (new_content, new_updated, "test_session", "车钥匙"))
        assert cursor.rowcount == 1, "应该更新1条记录"

        cursor.execute('SELECT content FROM memos WHERE id = ?', (memo_id_1,))
        updated_content = cursor.fetchone()[0]
        assert updated_content == new_content, "内容未更新"
        print(f"✓ 更新备忘录成功: {updated_content}")

        # 测试5: 检查是否存在（用于自动更新）
        cursor.execute('''
            SELECT id FROM memos
            WHERE session_id = ? AND key = ?
        ''', ("test_session", "钱包"))
        existing = cursor.fetchone()
        assert existing is None, "钱包应该不存在"

        # 插入新备忘录
        cursor.execute('''
            INSERT INTO memos
            (session_id, key, content, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("test_session", "钱包", "在背包里", "物品位置", now, now))
        memo_id_2 = cursor.lastrowid

        # 再次检查，应该存在
        cursor.execute('''
            SELECT id FROM memos
            WHERE session_id = ? AND key = ?
        ''', ("test_session", "钱包"))
        existing = cursor.fetchone()
        assert existing is not None, "钱包应该存在"
        print(f"✓ 存在性检查成功")

        # 测试6: 使用 create_memo 逻辑（自动更新已存在的）
        cursor.execute('''
            SELECT id FROM memos
            WHERE session_id = ? AND key = ?
        ''', ("test_session", "钱包"))
        existing = cursor.fetchone()

        if existing:
            # 更新
            cursor.execute('''
                UPDATE memos
                SET content = ?, category = ?, updated_at = ?
                WHERE id = ? AND session_id = ?
            ''', ("在桌子上", "物品位置", datetime.now().isoformat(), existing[0], "test_session"))
            action = "更新"
        else:
            # 创建
            cursor.execute('''
                INSERT INTO memos
                (session_id, key, content, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("test_session", "钱包", "在桌子上", "物品位置", datetime.now().isoformat(), datetime.now().isoformat()))
            action = "创建"

        assert action == "更新", "应该执行更新操作"
        cursor.execute('SELECT content FROM memos WHERE id = ?', (memo_id_2,))
        final_content = cursor.fetchone()[0]
        assert final_content == "在桌子上", "内容应该已更新"
        print(f"✓ 自动更新逻辑成功: {action}")

        # 测试7: 列出所有备忘录
        cursor.execute('''
            SELECT key, content, category, updated_at
            FROM memos
            WHERE session_id = ?
            ORDER BY updated_at DESC
        ''', ("test_session",))
        rows = cursor.fetchall()
        assert len(rows) >= 2, f"应该至少有2条记录，实际{len(rows)}条"
        print(f"✓ 列出所有备忘录成功，共 {len(rows)} 条")

        # 测试8: 按分类筛选
        cursor.execute('''
            SELECT key, content, category
            FROM memos
            WHERE session_id = ? AND category = ?
            ORDER BY updated_at DESC
        ''', ("test_session", "物品位置"))
        rows = cursor.fetchall()
        assert len(rows) >= 2, "应该至少有2条物品位置记录"
        for row in rows:
            assert row[2] == "物品位置", "分类应该都是物品位置"
        print(f"✓ 按分类筛选成功，找到 {len(rows)} 条")

        # 测试9: 删除备忘录
        cursor.execute('''
            DELETE FROM memos
            WHERE session_id = ? AND key = ?
        ''', ("test_session", "钱包"))
        assert cursor.rowcount == 1, "应该删除1条记录"

        cursor.execute('SELECT id FROM memos WHERE id = ?', (memo_id_2,))
        deleted = cursor.fetchone()
        assert deleted is None, "记录应该已删除"
        print(f"✓ 删除备忘录成功")

        # 测试10: 会话隔离
        cursor.execute('''
            SELECT id FROM memos
            WHERE session_id = ? AND key = ?
        ''', ("other_session", "车钥匙"))
        other_session_result = cursor.fetchone()
        assert other_session_result is None, "不同会话应该查询不到"
        print(f"✓ 会话隔离正确")

        conn.close()
        print("\n✓ 所有数据库操作测试通过！\n")


if __name__ == "__main__":
    try:
        test_database_operations()
        print("="*60)
        print("✓ 所有测试通过！")
        print("="*60)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

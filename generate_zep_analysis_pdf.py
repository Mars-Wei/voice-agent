#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate PDF report for zep_memory_tool_python analysis."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Chinese font support
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Try to register Chinese fonts
chinese_font_name = 'Helvetica'
try:
    if os.path.exists('/System/Library/Fonts/PingFang.ttc'):
        pdfmetrics.registerFont(TTFont('PingFang', '/System/Library/Fonts/PingFang.ttc'))
        chinese_font_name = 'PingFang'
    elif os.path.exists('/Library/Fonts/Arial Unicode.ttf'):
        pdfmetrics.registerFont(TTFont('ArialUnicode', '/Library/Fonts/Arial Unicode.ttf'))
        chinese_font_name = 'ArialUnicode'
except Exception:
    pass

def create_pdf():
    doc = SimpleDocTemplate(
        "/Volumes/WD-SSD/code/voice-agent/zep_memory_tool_python_接口分析报告.pdf",
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=chinese_font_name,
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontName=chinese_font_name,
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=chinese_font_name,
        fontSize=12,
        spaceAfter=8,
        spaceBefore=12
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=chinese_font_name,
        fontSize=10,
        spaceAfter=6,
        leading=14
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=9,
        spaceAfter=6,
        leftIndent=20
    )

    story = []

    # Title
    story.append(Paragraph("zep_memory_tool_python 接口分析报告", title_style))
    story.append(Spacer(1, 20))

    # Section 1: Overview
    story.append(Paragraph("1. 扩展概述", heading1_style))
    story.append(Paragraph(
        "zep_memory_tool_python 是一个 LLM Tool 扩展，基于 AsyncLLMToolBaseExtension 提供长期记忆功能。",
        normal_style
    ))
    story.append(Paragraph(
        "路径: ai_agents/agents/ten_packages/extension/zep_memory_tool_python/",
        normal_style
    ))

    # Section 2: Directory Structure
    story.append(Paragraph("2. 目录结构", heading1_style))

    dir_data = [
        ['文件', '用途'],
        ['manifest.json', '扩展元数据、依赖、API接口定义'],
        ['property.json', '默认配置'],
        ['addon.py', '扩展注册'],
        ['extension.py', '核心逻辑'],
        ['__init__.py', '包初始化'],
        ['requirements.txt', '外部依赖: zep-cloud>=3.0.0'],
        ['README.md', '文档'],
        ['test_*.py', '测试文件'],
    ]

    dir_table = Table(dir_data, colWidths=[4*cm, 11*cm])
    dir_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(dir_table)
    story.append(Spacer(1, 20))

    # Section 3: LLM Tools
    story.append(Paragraph("3. 提供的 3 个 LLM Tool", heading1_style))

    tools_data = [
        ['Tool Name', '参数', '功能'],
        ['add_memory', 'user_message, assistant_response, session_id', '存储对话到长期记忆'],
        ['retrieve_memory', 'query, session_id', '基于查询检索记忆'],
        ['get_memory_summary', 'session_id', '获取用户记忆摘要'],
    ]

    tools_table = Table(tools_data, colWidths=[4*cm, 6*cm, 5*cm])
    tools_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(tools_table)
    story.append(Spacer(1, 20))

    # Section 4: API Calls
    story.append(Paragraph("4. Zep Cloud API 调用", heading1_style))

    api_data = [
        ['Zep SDK 方法', '用途'],
        ['zep_client.user.get(user_id=...)', '检查用户是否存在'],
        ['zep_client.user.add(user_id=...)', '创建用户'],
        ['zep_client.thread.get(thread_id=...)', '检查会话是否存在'],
        ['zep_client.thread.create(thread_id=..., user_id=...)', '创建会话'],
        ['zep_client.thread.add_messages(thread_id=..., messages=...)', '添加消息'],
        ['zep_client.thread.get_user_context(thread_id=...)', '检索记忆上下文'],
    ]

    api_table = Table(api_data, colWidths=[8*cm, 7*cm])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 20))

    # Section 5: Environment Variables
    story.append(Paragraph("5. 环境变量", heading1_style))

    env_data = [
        ['变量', '必填', '说明'],
        ['ZEP_API_KEY', '是', 'Zep Cloud API Key'],
        ['ZEP_API_URL', '否', '默认为 https://api.getzep.com'],
    ]

    env_table = Table(env_data, colWidths=[4*cm, 2*cm, 9*cm])
    env_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(env_table)
    story.append(Spacer(1, 20))

    # Page break before replacement guide
    story.append(PageBreak())

    # Section 6: Replacement Guide
    story.append(Paragraph("6. 如何替换为自己的服务", heading1_style))
    story.append(Paragraph(
        "你需要创建一个新的 extension，核心是修改 extension.py 中的 3 个私有方法。",
        normal_style
    ))

    # Step 1
    story.append(Paragraph("6.1 创建新 Extension 目录结构", heading2_style))
    story.append(Paragraph("your_memory_tool_python/", normal_style))
    story.append(Paragraph("├── manifest.json      # 复制并修改 name/addon", code_style))
    story.append(Paragraph("├── property.json     # 你的默认配置", code_style))
    story.append(Paragraph("├── addon.py          # 注册新 addon", code_style))
    story.append(Paragraph("├── extension.py      # 核心逻辑（修改这里）", code_style))
    story.append(Paragraph("└── requirements.txt # 你的依赖", code_style))
    story.append(Spacer(1, 10))

    # Step 2
    story.append(Paragraph("6.2 必须实现的方法签名", heading2_style))

    story.append(Paragraph("from ten_ai_base.llm_tool import AsyncLLMToolBaseExtension", code_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("class YourMemoryToolExtension(AsyncLLMToolBaseExtension):", code_style))
    story.append(Paragraph('    def get_tool_metadata(self, ten_env) -> list[LLMToolMetadata]:', code_style))
    story.append(Paragraph('        """返回 3 个 tool 的 metadata（名称/描述/参数），保持不变"""', code_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("    async def run_tool(self, ten_env, name: str, args: dict):", code_style))
    story.append(Paragraph("        # 根据 name 分发到对应处理函数", code_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("    async def _add_memory(self, ten_env, args: dict) -> str:", code_style))
    story.append(Paragraph("        \"\"\"替换为你的 API：存储对话\"\"\"", code_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("    async def _retrieve_memory(self, ten_env, args: dict) -> str:", code_style))
    story.append(Paragraph("        \"\"\"替换为你的 API：搜索记忆\"\"\"", code_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("    async def _get_memory_summary(self, ten_env, args: dict) -> str:", code_style))
    story.append(Paragraph("        \"\"\"替换为你的 API：获取摘要\"\"\"", code_style))
    story.append(Spacer(1, 10))

    # Step 3
    story.append(Paragraph("6.3 替换点", heading2_style))
    story.append(Paragraph(
        "主要在 extension.py:145-212 的 3 个私有方法。",
        normal_style
    ))
    story.append(Paragraph(
        "把 zep_cloud SDK 调用换成你自己的 HTTP API 调用即可。",
        normal_style
    ))
    story.append(Spacer(1, 10))

    # Step 4
    story.append(Paragraph("6.4 manifest.json 中的接口定义保持不变", heading2_style))
    story.append(Paragraph(
        "cmd_in (tool_call) 和 cmd_out (tool_register, chat_completion) 的接口定义不需要改，",
        normal_style
    ))
    story.append(Paragraph(
        "因为这是 TEN framework 的内部接口。",
        normal_style
    ))
    story.append(Spacer(1, 20))

    # Section 7: Key Code Locations
    story.append(Paragraph("7. 关键代码位置", heading1_style))

    code_loc_data = [
        ['位置', '功能'],
        ['extension.py:60-80', 'on_start() - 初始化 Zep 客户端'],
        ['extension.py:145-170', '_add_memory() - 添加记忆'],
        ['extension.py:172-190', '_retrieve_memory() - 检索记忆'],
        ['extension.py:192-212', '_get_memory_summary() - 获取摘要'],
        ['extension.py:120-140', 'run_tool() - 分发工具调用'],
        ['extension.py:82-118', 'get_tool_metadata() - 返回工具元数据'],
    ]

    code_loc_table = Table(code_loc_data, colWidths=[4*cm, 11*cm])
    code_loc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(code_loc_table)

    doc.build(story)
    print("PDF generated successfully!")
    print("Output: /Volumes/WD-SSD/code/voice-agent/zep_memory_tool_python_接口分析报告.pdf")

if __name__ == "__main__":
    create_pdf()

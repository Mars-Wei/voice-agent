# Memory Retrieve Tool Extension

一个基于 Zep Cloud 的记忆检索工具扩展，允许 LLM 智能体主动检索相关记忆和上下文信息。

## 功能特性

- **对话上下文检索**：基于用户查询从 Zep Cloud 检索历史对话摘要和上下文信息
- **智能记忆检索**：使用 Zep 的 `thread.get_user_context()` API (mode="basic") 进行语义搜索
- **工具集成**：作为 LLM 工具，可以被 LLM 主动调用
- **性能监控**：记录检索耗时，便于性能分析

## 配置

### 环境变量

```bash
export ZEP_API_KEY="your_zep_api_key"
export USER_ID="user001"  # 可选，可在 property.json 中配置
export AGENT_ID="agent001"  # 可选，可在 property.json 中配置
```

### property.json 配置

```json
{
  "zep_api_key": "${env:ZEP_API_KEY}",
  "user_id": "${env:USER_ID|user001}",
  "agent_id": "${env:AGENT_ID|agent001}"
}
```

## 使用方法

### 1. 在 property.json 中添加节点

```json
{
  "nodes": [
    {
      "type": "extension",
      "name": "mem_retrieve_tool",
      "addon": "mem_retrieve_tool_python",
      "extension_group": "default",
      "property": {
        "zep_api_key": "${env:ZEP_API_KEY}",
        "user_id": "${env:USER_ID|user001}",
        "agent_id": "${env:AGENT_ID|agent001}"
      }
    }
  ]
}
```

### 2. 连接工具到 main_control

```json
{
  "connections": [
    {
      "extension": "main_control",
      "cmd": [
        {
          "names": ["tool_register"],
          "source": [
            {
              "extension": "mem_retrieve_tool"
            }
          ]
        }
      ]
    }
  ]
}
```

## 工具说明

### 工具名称
`retrieve_memory`

### 工具描述
检索与用户查询相关的记忆和上下文信息。当需要回忆用户信息、偏好或历史对话时使用此工具。

### 参数
- `query` (string, required): 用户的查询或问题，用于搜索相关的记忆上下文

### 返回格式

```json
{
  "query": "用户查询",
  "context": "检索到的记忆上下文",
  "thread_id": "thread_user001_agent001",
  "retrieval_time_ms": 123.45
}
```

## 工作原理

1. **线程ID生成**：根据 `user_id` 和 `agent_id` 生成一致的线程ID (`thread_{user_id}_{agent_id}`)
2. **上下文检索**：使用 Zep 的 `thread.get_user_context(thread_id, mode="basic")` API 检索对话上下文
3. **语义搜索**：Zep 基于用户查询进行语义搜索，返回相关的记忆上下文
4. **性能监控**：记录检索耗时，便于性能分析和优化

**实现参考**：本工具的实现参考了 `debug05.py` 中的记忆检索模式，使用相同的 API 调用方式。

## 示例

当用户问："我之前说过我喜欢什么颜色？"

LLM 可以调用 `retrieve_memory` 工具：
```json
{
  "query": "用户喜欢的颜色"
}
```

工具会返回相关的记忆上下文，帮助 LLM 回答用户的问题。

## 依赖

- `zep-cloud`: Zep Cloud Python SDK
- `ten_runtime_python`: TEN Framework Python 运行时
- `ten_ai_base`: TEN Framework AI 基础库

## 注意事项

- 如果 `zep_api_key` 未配置，工具扩展会加载但不会注册工具（可选功能）
- `user_id` 和 `agent_id` 用于确定检索哪个用户的记忆
- 工具使用 `thread_{user_id}_{agent_id}` 作为线程 ID

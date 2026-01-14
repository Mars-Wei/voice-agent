# Zep Memory Tool Extension

A TEN Framework extension that provides Zep-based long-term memory capabilities for voice assistants.

## Features

- **Long-term Memory**: Store and retrieve conversation history using Zep
- **Semantic Search**: Find relevant memories based on natural language queries
- **LLM Tool Integration**: Memory operations available as LLM tools
- **Session-based**: Memories are organized by conversation sessions

## Installation

1. Install the Zep Python SDK:
```bash
pip install zep-python
```

2. Set environment variables:
```bash
export ZEP_API_KEY="your_zep_api_key_here"
export ZEP_API_URL="https://api.getzep.com"  # or your self-hosted URL
```

## Configuration

The extension is configured in the voice-assistant's `property.json`:

```json
{
  "type": "extension",
  "name": "zep_memory_tool_python",
  "addon": "zep_memory_tool_python",
  "extension_group": "default",
  "property": {}
}
```

And added to `manifest.json`:

```json
{
  "path": "../../../ten_packages/extension/zep_memory_tool_python"
}
```

## Available Tools

### 1. add_memory
Store a conversation turn in long-term memory.

**Parameters:**
- `user_message` (string): The user's message
- `assistant_response` (string): The assistant's response
- `session_id` (string): Unique session identifier

### 2. retrieve_memory
Search for relevant memories based on a query.

**Parameters:**
- `query` (string): The search query
- `session_id` (string): Unique session identifier

### 3. get_memory_summary
Get a summary of the user's memory profile.

**Parameters:**
- `session_id` (string): Unique session identifier

## Usage

The memory tools are automatically available to the LLM. The LLM can decide when to use memory operations based on the conversation context.

### Example LLM Prompt Integration

```json
{
  "prompt": "You are a helpful voice assistant with access to memory tools for long-term conversation recall.\n\nMEMORY TOOLS AVAILABLE:\n1. add_memory - Add conversation turns to long-term memory\n2. retrieve_memory - Search for relevant past information\n3. get_memory_summary - Get user profile summary\n\nUse these tools appropriately:\n- Call add_memory after each meaningful conversation exchange\n- Call retrieve_memory when you need to recall specific information\n- Call get_memory_summary at conversation start to understand the user\n\nBe conversational and remember user details naturally."
}
```

## Architecture

The extension follows the TEN Framework's LLM Tool Extension pattern:

- Inherits from `AsyncLLMToolBaseExtension`
- Implements `get_tool_metadata()` to define available tools
- Implements `run_tool()` to execute memory operations
- Uses Zep's Python SDK for memory operations

## Memory Organization

- **Sessions**: Memories are organized by `session_id`
- **Threads**: Each session creates a Zep thread for conversation continuity
- **Messages**: User and assistant messages are stored with timestamps and metadata

## Error Handling

- If Zep API key is not configured, the extension logs a warning but doesn't fail
- Memory operations that fail return user-friendly error messages
- The extension gracefully degrades when Zep services are unavailable

## Development

### Testing

Run the structure test:
```bash
python test_structure.py
```

### File Structure

```
zep_memory_tool_python/
├── manifest.json          # Extension metadata and API definition
├── property.json          # Default configuration
├── addon.py              # Extension registration
├── extension.py          # Main implementation
├── test_structure.py     # Basic structure validation
└── README.md             # This documentation
```

## Troubleshooting

### Common Issues

1. **"zep-python not installed"**
   ```
   pip install zep-python
   ```

2. **"ZEP_API_KEY not set"**
   ```
   export ZEP_API_KEY="your_api_key"
   ```

3. **Memory operations failing**
   - Check Zep service status
   - Verify API key and URL configuration
   - Check network connectivity

### Logs

The extension logs memory operations with the `[ZepMemoryTool]` prefix:
- Initialization status
- Memory operation results
- Error conditions

## Integration with Voice Assistant

The memory tool integrates seamlessly with the voice assistant workflow:

1. **User speaks** → ASR converts to text
2. **LLM processes** → May call memory tools for context
3. **Memory retrieved** → Added to LLM context
4. **LLM responds** → Response sent to TTS
5. **Memory stored** → Conversation turn saved for future reference

This creates a continuous memory loop where the assistant can remember and reference previous conversations naturally.
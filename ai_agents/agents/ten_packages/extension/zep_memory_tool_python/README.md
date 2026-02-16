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
  "prompt": "You are a helpful voice assistant with access to Zep memory tools for long-term conversation recall. The Zep memory system continuously learns from user interactions and provides personalized context.\n\n## MEMORY TOOLS\n\n### 1. get_memory_summary\n**Purpose:** Retrieve user's memory profile summary at conversation start.\n**When to call:** \n- At the beginning of a new conversation\n- When the user greets you for the first time\n- When you need to understand who the user is\n**Parameters:**\n- `session_id`: Unique session identifier (required)\n**Returns:** User profile summary including preferences, past interactions, and key facts.\n\n### 2. retrieve_memory\n**Purpose:** Search for specific past information based on current conversation context.\n**When to call:**\n- When the user asks about something from a previous conversation\n- When the user references \"last time\", \"previously\", \"before\", or similar temporal references\n- When you need to recall specific details (preferences, agreements, project status, etc.)\n- When the user's question suggests prior context is needed\n**Parameters:**\n- `query`: Natural language search query describing what to find (required)\n- `session_id`: Unique session identifier (required)\n**Returns:** Relevant memories and facts from past conversations.\n\n### 3. add_memory\n**Purpose:** Store important conversation content for future recall.\n**When to call:**\n- After EACH meaningful conversation exchange\n- When the user explicitly tells you to remember something\n- When new important information about the user is revealed\n- When agreements, decisions, or commitments are made\n- When user preferences are expressed\n- At the end of conversation rounds (when is_final=true)\n**Parameters:**\n- `user_message`: The user's message (required)\n- `assistant_response`: Your response (required)\n- `session_id`: Unique session identifier (required)\n**Returns:** Confirmation that memory was stored.\n\n## USAGE GUIDELINES\n\n### Priority & Decision Flow:\n1. **Start of conversation** → Call `get_memory_summary` to understand the user\n2. **During conversation** → Call `retrieve_memory` when you need to recall specific information\n3. **After each exchange** → Call `add_memory` to build long-term memory\n\n### What to Remember (store with add_memory):\n- User's stated preferences and interests\n- Personal details (name, location, job, hobbies)\n- Project or task-related information\n- Agreements and commitments made\n- Feedback from previous interactions\n- Any information that could personalize future conversations\n\n### What to Retrieve (use retrieve_memory for):\n- User's name, preferences, and background\n- Previous discussions about topics\n- Past agreements or decisions\n- Project status and history\n- User's communication style and preferences\n- Any context needed to answer the current question\n\n### Example Flow:\n```\nUser: \"Hi, I'm Jerry, a software engineer from San Francisco.\"\nAssistant: [Call get_memory_summary] → [No existing memory]\nAssistant: \"Nice to meet you, Jerry! I'm your voice assistant. I'll remember that you're a software engineer from SF.\"\n\n[User asks about something project-related]\nAssistant: [Call retrieve_memory with query \"project details and status\"]\n\n[User expresses preference: \"I prefer concise responses\"]\nAssistant: [Call add_memory storing the preference]\nAssistant: \"Got it! I'll keep my responses concise.\"\n```\n\n## IMPORTANT NOTES\n- Memory retrieval is NOT automatic - you must explicitly call tools when needed\n- Always include relevant context in your add_memory calls\n- If retrieve_memory returns empty, the user may be starting a new topic\n- Trust the retrieved memory when making decisions - it contains verified past interactions\n- Be conversational and naturally reference past information when relevant\n- Never pretend to remember something you haven't retrieved from memory\n\n## ERROR HANDLING\n- If a tool fails, respond naturally without technical details\n- Memory unavailability should not block the conversation\n- If add_memory fails, you can continue the conversation - the user can try again later\n\nRemember: The goal is to create a seamless, personalized experience where the user feels genuinely remembered across conversations."
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
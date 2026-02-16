# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**TEN Framework** — An open-source framework for building real-time multimodal conversational AI agents. Uses a graph-based architecture where extensions (ASR, LLM, TTS, RTC, tools) connect via `property.json` configurations to form complete AI agent pipelines.

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `ai_agents/agents/examples/` | Complete agent examples (voice-assistant, transcription, etc.) |
| `ai_agents/agents/ten_packages/extension/` | 60+ extensions (ASR, TTS, LLM, tools) |
| `ai_agents/agents/ten_packages/system/ten_ai_base/` | Base classes and API interfaces |
| `ai_agents/server/` | Go API server for agent lifecycle |
| `ai_agents/playground/` | Next.js frontend UI |
| `core/` | TEN Framework core (C++, Rust, Go/Python/Node bindings) |
| `packages/` | Core extensions and example apps |

## Build Commands

### TEN Framework Core (root level)
```bash
task gen                    # Generate build files
task build                  # Build framework
task clean                  # Clean build artifacts
```

### AI Agents (run from `ai_agents/` directory)
```bash
task lint                   # Lint all Python extensions
task lint-extension EXTENSION=deepgram_asr_python
task format                 # Format Python with Black
task check                  # Check formatting
task test                   # Run all tests (server + extensions)
task test-extension EXTENSION=agents/ten_packages/extension/elevenlabs_tts_python
task test-extension-no-install EXTENSION=...  # Skip dependency install
```

### Integration Tests
```bash
task asr-guarder-test EXTENSION=azure_asr_python CONFIG_DIR=tests/configs
task tts-guarder-test EXTENSION=bytedance_tts_duplex CONFIG_DIR=tests/configs
```

### Running Agent Examples
```bash
cd ai_agents/agents/examples/voice-assistant
task install                # Install all dependencies
task run                    # Run everything (frontend + API + TMAN Designer)
task run-frontend           # http://localhost:3000
task run-api-server         # http://localhost:8080
task run-gd-server          # http://localhost:49483 (TMAN Designer)
```

### TypeScript/JavaScript
```bash
# Root level (Biome)
npm run lint && npm run lint:fix
npm run format && npm run format:write

# Playground
cd ai_agents/playground && bun install && bun run dev
```

### Go Server
```bash
cd ai_agents/server && go test -v ./...
```

## Architecture

### Extension System

Extensions are modular components providing specific capabilities. Each extension has:
- `manifest.json` — Metadata, dependencies, API interface definitions
- `property.json` — Default configuration (supports `${env:VAR_NAME}` syntax)
- `addon.py` — Registration using `@register_addon_as_extension` decorator
- `extension.py` — Main logic inheriting from base classes

**Base Classes** (in `ten_ai_base`): `AsyncASRBaseExtension`, `AsyncTTSBaseExtension`, `LLMBaseExtension`

### Graph-Based Configuration

Agents are configured via `predefined_graphs` in `property.json`:
```json
{
  "ten": {
    "predefined_graphs": [{
      "name": "voice_assistant",
      "auto_start": true,
      "graph": {
        "nodes": [
          {"name": "stt", "addon": "deepgram_asr_python", "property": {...}},
          {"name": "llm", "addon": "openai_llm2_python", "property": {...}}
        ],
        "connections": [
          {"extension": "main_control", "data": [{"name": "asr_result", "source": [{"extension": "stt"}]}]}
        ]
      }
    }]
  }
}
```

**Connection types**: `data`, `cmd`, `audio_frame`, `video_frame`

### Server API

Go server manages agent processes:
- `POST /start` — Start agent with graph config
- `POST /stop` — Stop agent
- `POST /ping` — Keep agent alive

## Python Development

### PYTHONPATH Configuration
```bash
export PYTHONPATH="./agents/ten_packages/system/ten_runtime_python/lib:./agents/ten_packages/system/ten_runtime_python/interface:./agents/ten_packages/system/ten_ai_base/interface"
```

### Extension Pattern
```python
from ten_ai_base.asr import AsyncASRBaseExtension
from ten_runtime import Addon, register_addon_as_extension

class MyASRExtension(AsyncASRBaseExtension):
    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        await super().on_init(ten_env)
        config_json, _ = await ten_env.get_property_to_json("")
        self.config = MyConfig.model_validate_json(config_json)

@register_addon_as_extension("my_asr_python")
class MyASRExtensionAddon(Addon):
    def on_create_instance(self, ten: TenEnv, addon_name: str, context) -> None:
        ten.on_create_instance_done(MyASRExtension(addon_name), context)
```

### Config with Pydantic
```python
from pydantic import BaseModel, Field

class MyConfig(BaseModel):
    api_key: str
    model: str = "default"
    params: dict[str, Any] = Field(default_factory=dict)
```

## Code Style

### Python
- **Formatter**: Black, 80 char line length
- **Type Checking**: Pyright basic mode
- **Critical errors**: `reportUnusedCoroutine`, `reportMissingAwait`, `reportUnawaitedAsyncFunctions`

### TypeScript/JavaScript
- **Formatter**: Biome
- **Style**: 2-space indent, double quotes, semicolons

### Go
- Standard Go conventions, `slog` for logging
- JSON tags use snake_case

## Do NOT Modify

Auto-generated files (see `.gitignore`):
- `manifest-lock.json`, `compile_commands.json`, `BUILD.gn`
- `out/`, `.ten/`, `bin/`, `.release/`, `build/`, `node_modules/`

## Development Principles

**YAGNI**: Only implement what's actually needed now.
**KISS**: Prefer simple solutions. Three similar lines > premature abstraction.

## Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Ensure PYTHONPATH includes ten_runtime_python and ten_ai_base |
| Extension not loading | Check addon.py decorator name matches property.json "addon" |
| Test failures | Ensure .env has required API keys |

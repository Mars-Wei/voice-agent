# AGENTS.md

Guidance for AI coding assistants working in this repository.

## Repository Overview

**TEN Framework** - An open-source framework for building real-time multimodal conversational AI agents. Uses graph-based architecture where extensions (ASR, LLM, TTS, RTC, tools) connect via `property.json` configurations.

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `ai_agents/` | AI agent examples, extensions, and playground |
| `ai_agents/agents/examples/` | Complete agent examples (voice-assistant, transcription, etc.) |
| `ai_agents/agents/ten_packages/extension/` | 60+ extensions (ASR, TTS, LLM, tools) |
| `ai_agents/server/` | Go API server for agent lifecycle |
| `ai_agents/playground/` | Next.js frontend UI |
| `core/` | TEN Framework core (C++, Rust, bindings) |
| `packages/` | Core extensions and apps |

## Build/Lint/Test Commands

### Root Level

```bash
# Build TEN Framework core
task build

# Generate build files
task gen
```

### AI Agents (`ai_agents/` directory)

```bash
# Lint all Python extensions
task lint

# Lint specific extension
task lint-extension EXTENSION=deepgram_asr_python

# Format Python code
task format

# Check formatting
task check

# Run all tests
task test

# Test specific extension
task test-extension EXTENSION=agents/ten_packages/extension/elevenlabs_tts_python

# Test without reinstalling deps
task test-extension-no-install EXTENSION=agents/ten_packages/extension/elevenlabs_tts_python

# Integration tests
task asr-guarder-test EXTENSION=azure_asr_python CONFIG_DIR=tests/configs
task tts-guarder-test EXTENSION=bytedance_tts_duplex CONFIG_DIR=tests/configs
```

### Example Projects (e.g., `ai_agents/agents/examples/voice-assistant/`)

```bash
# Install all dependencies
task install

# Run everything (frontend + API server + TMAN Designer)
task run

# Run individual components
task run-frontend     # http://localhost:3000
task run-api-server   # http://localhost:8080
task run-gd-server    # http://localhost:49483 (TMAN Designer)
```

### TypeScript/JavaScript

```bash
# Root level (Biome)
npm run lint          # Check
npm run lint:fix      # Fix
npm run format        # Check format
npm run format:write  # Fix format

# Playground
cd ai_agents/playground
bun install
bun run dev           # Dev server
bun run build         # Production build
bun run lint          # Biome check
```

### Go Server

```bash
cd ai_agents/server
go test -v ./...      # Run tests
go build -o bin/api main.go  # Build
```

## Code Style Guidelines

### Python (Extensions)

**Formatting**: Black with 80 char line length
**Type Checking**: Pyright in basic mode

```python
# Import order: stdlib, third-party, local
from datetime import datetime
import os
from typing import Dict, Any

from typing_extensions import override
from pydantic import BaseModel, Field

from ten_runtime import AsyncTenEnv, AudioFrame
from ten_ai_base.asr import AsyncASRBaseExtension
from .config import MyConfig

# Class naming: PascalCase, descriptive
class DeepgramASRExtension(AsyncASRBaseExtension):
    """Docstring for class."""

    def __init__(self, name: str):
        super().__init__(name)
        self.config: MyConfig | None = None  # Type hints required

    @override
    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        await super().on_init(ten_env)
        # Load config from property.json
        config_json, _ = await ten_env.get_property_to_json("")
        self.config = MyConfig.model_validate_json(config_json)

# Config classes: Pydantic BaseModel
class MyConfig(BaseModel):
    api_key: str
    model: str = "default"
    params: Dict[str, Any] = Field(default_factory=dict)
```

**Critical Pyright Rules (errors)**:
- `reportUnusedCoroutine`
- `reportMissingAwait`
- `reportUnawaitedAsyncFunctions`

**PYTHONPATH for extensions**:
```bash
export PYTHONPATH="./agents/ten_packages/system/ten_runtime_python/lib:./agents/ten_packages/system/ten_runtime_python/interface:./agents/ten_packages/system/ten_ai_base/interface"
```

### TypeScript/JavaScript (Frontend)

**Formatter**: Biome
**Style**: 2-space indent, double quotes, semicolons, ES5 trailing commas

```typescript
// Import order: types first, then libraries, then local
import type { Language } from "@/types";
import axios from "axios";
import { genUUID } from "./utils";

// Interface naming: PascalCase, prefix I for state interfaces
interface StartRequestConfig {
  channel: string;
  userId: number;
  graphName: string;
}

// Function naming: camelCase, api prefix for API calls
export const apiStartService = async (
  config: StartRequestConfig
): Promise<any> => {
  const url = `/api/agents/start`;
  const resp: any = await axios.post(url, config);
  return resp.data || {};
};

// React hooks: use prefix
export function useIsMobileScreen(breakpoint?: string) {
  const [isMobile, setIsMobile] = React.useState(false);
  // ...
  return isMobile;
}

// Redux: createSlice pattern
export const globalSlice = createSlice({
  name: "global",
  initialState: getInitialState(),
  reducers: {
    setOptions: (state, action: PayloadAction<Partial<IOptions>>) => {
      state.options = { ...state.options, ...action.payload };
    },
  },
});
```

**Biome Rules**:
- `useSortedClasses` for Tailwind className ordering
- React recommended rules enabled

### Go (Server)

```go
package main

import (
    "encoding/json"
    "log/slog"
    "net/http"

    "github.com/gin-gonic/gin"
    "app/internal"
)

// Struct naming: PascalCase
type HttpServerConfig struct {
    AppId      string
    Port       string
    WorkersMax int
}

// JSON tags: snake_case
type StartReq struct {
    RequestId   string `json:"request_id,omitempty"`
    ChannelName string `json:"channel_name,omitempty"`
}

// Error handling: slog for logging
func main() {
    if err := doSomething(); err != nil {
        slog.Error("operation failed", "err", err)
        os.Exit(1)
    }
}
```

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `deepgram_asr_python/` |
| Python files | snake_case | `extension.py`, `config.py` |
| TypeScript files | camelCase or PascalCase | `request.ts`, `ChatCard.tsx` |
| React components | PascalCase | `MessageList.tsx` |
| Go files | snake_case | `http_server.go` |
| Config files | kebab-case | `property.json`, `manifest.json` |

## Error Handling

### Python
```python
try:
    result = await external_api_call()
except Exception as e:
    ten_env.log_error(f"API call failed: {e}", category=LOG_CATEGORY_VENDOR)
    await self.send_asr_error(ModuleError(...), vendor_info)
```

### TypeScript
```typescript
try {
  const resp = await axios.post(url, data);
  return resp.data;
} catch (error: any) {
  console.error("Error:", error);
  return rejectWithValue(error.response?.data || error.message);
}
```

### Go
```go
if err != nil {
    slog.Error("operation failed", "err", err, logTag)
    return // or os.Exit(1) for fatal
}
```

## Do NOT Modify

Auto-generated files (see `.gitignore`):
- `manifest-lock.json`, `compile_commands.json`, `BUILD.gn`
- `out/`, `.ten/`, `bin/`, `.release/`, `build/`, `node_modules/`
- `*.log` files

## Development Principles

**YAGNI**: Only implement what's actually needed now.
**KISS**: Prefer simple solutions. Three similar lines > premature abstraction.

## Extension Structure

```
extension_name/
  manifest.json      # Metadata, dependencies, API interface
  property.json      # Default configuration
  addon.py           # Registration with @register_addon_as_extension
  extension.py       # Main logic
  config.py          # Pydantic config model
  tests/
    bin/start        # Test runner script
    conftest.py      # pytest fixtures
    test_*.py        # Test files
```

## Common Issues

**Import errors**: Ensure PYTHONPATH includes ten_runtime_python and ten_ai_base
**Extension not loading**: Check addon.py decorator name matches property.json "addon"
**Test failures**: Ensure .env has required API keys

## Quick Reference

| Task | Command |
|------|---------|
| Lint Python | `task lint` |
| Format Python | `task format` |
| Test extension | `task test-extension EXTENSION=path/to/ext` |
| Run example | `cd agents/examples/voice-assistant && task run` |
| Lint TS/JS | `npm run lint:fix` |
| Go tests | `cd ai_agents/server && go test -v ./...` |

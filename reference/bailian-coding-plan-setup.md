# Alibaba Bailian Coding Plan - OpenCode Setup Guide

The Bailian Coding Plan is a unified subscription from Alibaba Cloud that provides access to multiple leading AI models through a single Anthropic-compatible API endpoint. This guide covers setup for OpenCode.

---

## Overview

| Feature | Details |
|---------|---------|
| **Provider Type** | Anthropic-compatible API |
| **Base URL** | `https://coding-intl.dashscope.aliyuncs.com/apps/anthropic/v1` |
| **Authentication** | API Key |
| **Models Included** | Qwen3.x, GLM-4.7, Kimi-K2.5 |

---

## Prerequisites

1. **Active Bailian Coding Plan subscription** - Available through Alibaba Cloud Model Studio
2. **API Key** - Obtain from Model Studio Console

---

## Configuration

Add the following to your `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "bailian-coding-plan": {
      "npm": "@ai-sdk/anthropic",
      "name": "Model Studio Coding Plan",
      "options": {
        "baseURL": "https://coding-intl.dashscope.aliyuncs.com/apps/anthropic/v1",
        "apiKey": "YOUR_API_KEY_HERE"
      },
      "models": {
        "qwen3.5-plus": {
          "name": "Qwen3.5 Plus",
          "limit": { "context": 262144, "output": 8192 },
          "options": {
            "thinking": {
              "type": "enabled",
              "budgetTokens": 1024
            }
          }
        },
        "qwen3-max-2026-01-23": {
          "name": "Qwen3 Max 2026-01-23",
          "limit": { "context": 262144, "output": 8192 },
          "options": {
            "thinking": {
              "type": "enabled",
              "budgetTokens": 1024
            }
          }
        },
        "qwen3-coder-plus": {
          "name": "Qwen3 Coder Plus",
          "limit": { "context": 262144, "output": 16384 }
        },
        "qwen3-coder-next": {
          "name": "Qwen3 Coder Next",
          "limit": { "context": 262144, "output": 65536 }
        },
        "glm-4.7": {
          "name": "GLM-4.7",
          "limit": { "context": 131072, "output": 8192 }
        },
        "kimi-k2.5": {
          "name": "Kimi K2.5",
          "limit": { "context": 262144, "output": 8192 }
        }
      }
    }
  }
}
```

---

## Available Models

### Model Comparison

| Model | Context | Thinking | Vision | Tool Call | Best For |
|-------|---------|----------|--------|-----------|----------|
| **qwen3.5-plus** | 262K (1M ext.) | Extended | Multimodal | Native | General purpose, multimodal tasks |
| **qwen3-max-2026-01-23** | ~262K | Extended | Multimodal | Native | Complex reasoning, analysis |
| **qwen3-coder-plus** | ~256K | - | - | Native | Code generation, debugging |
| **qwen3-coder-next** | 256K native | - | - | Native | Advanced coding, agentic tasks |
| **glm-4.7** | Large | Interleaved | - | Native | Coding + reasoning, terminal tasks |
| **kimi-k2.5** | 256K | Interleaved | Native | Native | Visual agents, coding, multimodal |

### Model Details

#### Qwen3.5 Plus
- **Architecture**: MoE (397B total, 17B activated)
- **Context**: 262,144 tokens native, extensible to 1M
- **Thinking**: Extended thinking with budgetTokens control
- **Vision**: Native multimodal (images, video, documents)
- **Strengths**: General purpose, multilingual (201 languages), visual reasoning

#### Qwen3 Max
- **Architecture**: Large MoE
- **Context**: ~262K tokens
- **Thinking**: Extended thinking support
- **Vision**: Native multimodal
- **Strengths**: Complex reasoning, deep analysis

#### Qwen3 Coder Plus
- **Context**: ~256K tokens
- **Thinking**: Not supported (non-thinking mode only)
- **Strengths**: Code generation, code review, debugging

#### Qwen3 Coder Next
- **Architecture**: MoE (80B total, 3B activated)
- **Context**: 262,144 tokens native
- **Thinking**: Not supported (non-thinking mode only)
- **Tool Call**: Advanced agentic tool use
- **Max Output**: 65,536 tokens
- **Strengths**: Agentic coding, IDE integration, long-horizon tasks

#### GLM-4.7
- **Provider**: Zhipu AI
- **Thinking**: Interleaved thinking (thinks before every action)
- **Features**: Preserved thinking for multi-turn consistency
- **Strengths**: Agentic coding, terminal tasks, tool use
- **Note**: Model ID may vary - verify in your Bailian console

#### Kimi K2.5
- **Provider**: Moonshot AI
- **Architecture**: MoE (1T total, 32B activated)
- **Context**: 262,144 tokens
- **Vision**: Native multimodal (images, video)
- **Thinking**: Interleaved + instant modes available
- **Strengths**: Visual agents, coding, multimodal reasoning
- **Note**: Model ID may vary - verify in your Bailian console

---

## Usage

### Selecting a Model

In OpenCode, reference models with the provider prefix:

```
bailian-coding-plan/qwen3-coder-next
bailian-coding-plan/qwen3.5-plus
bailian-coding-plan/glm-4.7
bailian-coding-plan/kimi-k2.5
```

### Thinking Mode

#### Qwen Models (Extended Thinking)
Thinking is configured via model options:

```json
{
  "options": {
    "thinking": {
      "type": "enabled",
      "budgetTokens": 1024
    }
  }
}
```

- `budgetTokens`: Number of tokens allocated for thinking (512-4096 typical)
- Higher values = more thorough reasoning but longer response time

#### GLM-4.7 & Kimi-K2.5 (Interleaved Thinking)
These models support interleaved thinking where they think before each action:

```json
{
  "options": {
    "enable_thinking": true
  }
}
```

For instant mode (no thinking):

```json
{
  "options": {
    "enable_thinking": false
  }
}
```

### Recommended Settings by Task

| Task | Recommended Models |
|------|-------------------|
| General coding | `qwen3-coder-next`, `glm-4.7` |
| Complex reasoning | `qwen3-max-2026-01-23`, `qwen3.5-plus` |
| Code review | `qwen3-coder-plus`, `kimi-k2.5` |
| Multimodal (images) | `qwen3.5-plus`, `kimi-k2.5` |
| Long-horizon agents | `qwen3-coder-next`, `glm-4.7` |
| Terminal/CLI tasks | `glm-4.7`, `qwen3-coder-next` |

---

## Troubleshooting

### Connection Errors

| Error | Solution |
|-------|----------|
| `401 Unauthorized` | Verify API key is correct and active |
| `404 Not Found` | Check baseURL: `coding-intl.` prefix required for international |
| `Connection refused` | Verify network connectivity to `dashscope.aliyuncs.com` |

### Model Errors

| Error | Solution |
|-------|----------|
| `Model not found` | Confirm model ID matches your subscription's available models |
| `Thinking not supported` | Check if model supports thinking (see table above) |
| `Context length exceeded` | Reduce input size or switch to higher context model |

### Regional Endpoints

| Region | Base URL |
|--------|----------|
| International | `https://coding-intl.dashscope.aliyuncs.com/apps/anthropic/v1` |
| China/Beijing | `https://coding.dashscope.aliyuncs.com/apps/anthropic/v1` |

### Verifying Model IDs

Model IDs in Bailian may differ from open-source names. To verify:

1. Log into Model Studio Console
2. Navigate to your Coding Plan subscription
3. Check available model identifiers
4. Update `opencode.json` with correct IDs

---

## API Compatibility

The Coding Plan endpoint is **Anthropic-compatible**, meaning:

- Uses Claude-style message format
- Supports `system`, `user`, `assistant` roles
- Tool calling via Anthropic's tool format
- Vision via `image_url` content blocks

### Example API Request

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="your-api-key",
    base_url="https://coding-intl.dashscope.aliyuncs.com/apps/anthropic/v1"
)

response = client.messages.create(
    model="qwen3-coder-next",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Write a Python function to merge sorted arrays"}
    ]
)
```

---

## Resources

- [Alibaba Cloud Model Studio](https://modelstudio.alibabacloud.com/)
- [Qwen Documentation](https://qwen.ai/)
- [GLM Documentation](https://z.ai/)
- [Kimi Documentation](https://platform.moonshot.ai/)
- [OpenCode Configuration](https://opencode.ai/config.json)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-02-23 | Initial documentation with Qwen3.x, GLM-4.7, Kimi-K2.5 |

---

> **Note**: Model IDs for GLM-4.7 and Kimi-K2.5 should be verified in your Bailian console as they may differ from the placeholder values used here.
---
title: "adapters"
created: 2026-03-24T19:05:55Z
---
# Adapter Reference

Adapters are converters between your code's request/response format and each provider's native format. TokenPak includes **5 built-in adapters**, all FREE.

---

## Overview

| Adapter | Provider | Status | Best For |
|---------|----------|--------|----------|
| `anthropic` | Anthropic (Claude) | ✅ | Default, most mature |
| `openai_chat` | OpenAI Chat API | ✅ | GPT-4, GPT-3.5-Turbo |
| `openai_responses` | OpenAI Responses (Legacy) | ✅ | Older OpenAI integrations |
| `google` | Google Gemini | ✅ | Switching to Gemini |
| `passthrough` | Raw JSON | ✅ | Debugging, custom providers |

---

## 1. Anthropic Adapter

The **default adapter**. Uses the Anthropic (Claude) API format.

### Configuration

```yaml
# config.yaml
provider: anthropic
```

### Basic Usage

Point the standard Anthropic SDK at the proxy via `base_url`:

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
)

response = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "What is 2 + 2?"}
    ]
)

print(response.content[0].text)  # "4"
```

Or use the TokenPak SDK adapter directly:

```python
from tokenpak.sdk import AnthropicAdapter

adapter = AnthropicAdapter(base_url="http://127.0.0.1:8766", api_key="sk-ant-...")
response = adapter.call({
    "model": "claude-opus-4-8",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "What is 2 + 2?"}],
})
print(response["content"][0]["text"])
```

### With System Prompt

```python
response = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=100,
    system="You are a helpful math tutor.",
    messages=[
        {"role": "user", "content": "Explain why 2 + 2 = 4"}
    ]
)
```

### With Tool Use

```python
response = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=100,
    tools=[
        {
            "name": "calculator",
            "description": "Perform a calculation",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression"
                    }
                },
                "required": ["expression"]
            }
        }
    ],
    messages=[
        {"role": "user", "content": "What is 15 * 7?"}
    ]
)

# Handle tool use in response
if response.stop_reason == "tool_use":
    for block in response.content:
        if block.type == "tool_use":
            print(f"Tool: {block.name}, Input: {block.input}")
```

### Streaming

```python
with client.messages.stream(
    model="claude-opus-4-8",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Write a poem about tokenization"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

---

## 2. OpenAI Chat Adapter

Routes requests to OpenAI's Chat API (GPT-4, GPT-3.5-Turbo).

### Configuration

```yaml
provider: openai
model: gpt-4o
```

### Basic Usage

Point the standard OpenAI SDK at the proxy via `base_url` (note the `/v1` suffix):

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8766/v1",
    api_key="sk-...",  # OpenAI key
)

response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Explain quantum computing briefly"}
    ]
)

print(response.choices[0].message.content)
```

Or use the TokenPak SDK adapter:

```python
from tokenpak.sdk import OpenAIAdapter

adapter = OpenAIAdapter(base_url="http://127.0.0.1:8766", api_key="sk-...")
response = adapter.call({
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello"}],
})
```

### Temperature & Top-P

```python
response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=100,
    temperature=0.7,  # 0 = deterministic, 2 = creative
    top_p=0.9,  # nucleus sampling
    messages=[
        {"role": "user", "content": "Generate a creative story title"}
    ]
)
```

### Function / Tool Calling (OpenAI style)

```python
response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=100,
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "unit": {"type": "string", "enum": ["C", "F"]}
                    },
                    "required": ["location"]
                }
            }
        }
    ],
    messages=[
        {"role": "user", "content": "What's the weather in San Francisco?"}
    ]
)
```

### JSON Mode

```python
import json

response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=200,
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "user",
            "content": 'Return a JSON object with fields: "name", "age", "occupation"'
        }
    ]
)

data = json.loads(response.choices[0].message.content)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="gpt-4o",
    stream=True,
    messages=[
        {"role": "user", "content": "Write a haiku"}
    ]
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

---

## 3. OpenAI Responses Adapter (Legacy)

For older integrations using the OpenAI Responses/Completions API. **Not recommended for new projects** (OpenAI deprecated this). Route legacy completions through the proxy using the standard OpenAI SDK pointed at the proxy `base_url`:

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8766/v1", api_key="sk-...")

response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="Q: What is the capital of France?\nA:",
    max_tokens=10
)
print(response.choices[0].text)
```

**Use the OpenAI Chat adapter for new code.**

---

## 4. Google Gemini Provider

> **Note:** The `tokenpak.sdk` adapter layer ships Anthropic, OpenAI, LangChain, and LiteLLM adapters. Gemini is reachable through the proxy via the OpenAI-compatible path or LiteLLM-style routing, rather than a dedicated Gemini SDK adapter. The example below is conceptual and uses the proxy's OpenAI-compatible endpoint.

### Via LiteLLM-style routing

```python
from tokenpak.sdk import LiteLLMAdapter

adapter = LiteLLMAdapter(base_url="http://127.0.0.1:8766", api_key="AIza...")
response = adapter.call({
    "model": "gemini/gemini-1.5-pro",
    "messages": [{"role": "user", "content": "What makes a good API design?"}],
})
```

Multimodal/vision support depends on the upstream provider and the request shape it accepts; send images using that provider's native content format.

---

## 5. Passthrough Usage

For debugging, custom providers, or testing. Sends raw JSON to the provider.

### Configuration

```yaml
provider: passthrough
```

### Usage (Manual Request)

```python
import httpx

# Send raw JSON directly
response = httpx.post(
    "http://127.0.0.1:8766/v1/messages",
    json={
        "model": "claude-opus-4-8",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    },
    headers={
        "Authorization": "Bearer sk-ant-...",
        "Content-Type": "application/json"
    }
)

print(response.json())
```

### Use Cases

- **Testing:** Debug proxy behavior without SDK
- **Custom providers:** Route to non-standard endpoints
- **Experimentation:** Send raw API requests

---

## Choosing the Right Adapter

### Use Anthropic if:
- ✅ Primary provider is Claude
- ✅ You want the most mature integration
- ✅ Starting a new project

### Use OpenAI Chat if:
- ✅ Primary provider is OpenAI (GPT-4, GPT-3.5)
- ✅ Need function calling or JSON mode
- ✅ Migrating from OpenAI SDK

### Use Google if:
- ✅ Primary provider is Gemini
- ✅ Want multimodal (vision) support
- ✅ Using Google's ecosystem

### Use Passthrough if:
- ✅ Debugging proxy issues
- ✅ Using a custom/unsupported provider
- ✅ Testing raw API behavior

---

## Configuration Examples

### Multi-Provider Fallback

```yaml
# Try Claude first, fall back to Gemini, then GPT-4
provider: anthropic
fallback:
  - google
  - openai

providers:
  anthropic:
    model: claude-opus-4-8
  google:
    model: gemini-pro
  openai:
    model: gpt-4o
```

### Cost-Optimized Routing

```yaml
# Use cheaper Haiku for simple tasks, Opus for complex
provider: anthropic
routing:
  simple_tasks: claude-haiku-4-5  # Cheaper
  complex_tasks: claude-opus-4-8  # More capable
```

---

## Error Handling

The TokenPak SDK adapters raise a canonical exception hierarchy. See [Error Handling Guide](./error-handling.md).

```python
from tokenpak.sdk.base import (
    TokenPakAdapterError,
    TokenPakTimeoutError,
    TokenPakAuthError,
    TokenPakConfigError,
)

try:
    response = adapter.call(request)
except TokenPakTimeoutError:
    print("Proxy timed out")
except TokenPakAuthError as e:
    print(f"Auth failed (HTTP {e.status_code})")
except TokenPakAdapterError as e:
    print(f"Adapter error: {e}")
```

---

## Next Steps

- **Token counting:** See [Installation](./installation.md)
- **Error handling:** Check [Error Handling Guide](./error-handling.md)
- **Advanced routing:** See [Feature Matrix](./features.md) 

All adapters work out-of-the-box with FREE TokenPak.

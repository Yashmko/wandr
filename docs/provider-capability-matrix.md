# Relay Provider Capability Matrix

| Provider | Prefix | Supported `delivery_channel` | Delivery method | Primary request knob |
| --- | --- | --- | --- | --- |
| OpenAI Responses | `openai` | `sandbox`, `stdout`, `output` | sandbox/stdout/output | `reasoning_effort` |
| Anthropic Managed | `anthropic` | `sandbox`, `output` | sandbox/output | `speed` |
| Perplexity Agent API | `perplexity` | `share`, `output` | share/output | `reasoning_effort` |
| Exa Agent | `exa` | `output` | output | `effort` |
| Parallel Task API | `parallel` | `output` | output | `processor` |
| Gemini Deep Research | `gemini` | `output` | output | `reasoning_effort` |

Validation is enforced by:
- `scripts/validate_configs.py` (config/runtime checks)
- `scripts/validate_provider_contracts.py` (provider contract conformance)

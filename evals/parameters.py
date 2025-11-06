"""Parameter definitions for Braintrust evaluations.

Prompt parameters (type="prompt") render as full editors in the playground
with system messages, model selection, and other options.
"""

from src.config import DEFAULT_SYSTEM_PROMPT, DEFAULT_MODEL


SYSTEM_PROMPT_PARAM = {
    "type": "prompt",
    "description": "Configure the system prompt and model for the assistant",
    "default": {
        "prompt": {
            "type": "chat",
            "messages": [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}],
        },
        "options": {"model": DEFAULT_MODEL},
    },
}


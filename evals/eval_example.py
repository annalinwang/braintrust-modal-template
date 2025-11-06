"""Example Braintrust evaluation with remote eval support.

Shows how to:
- Define a task that calls an LLM
- Use configurable parameters from the playground
- Score outputs with LLM-as-a-judge
"""

import os
from braintrust import Eval, init_dataset
from autoevals import LLMClassifier
from openai import OpenAI

from src.config import DEFAULT_SYSTEM_PROMPT, DEFAULT_MODEL
from evals.parameters import SYSTEM_PROMPT_PARAM


async def example_task(input: dict, hooks=None):
    """Call OpenAI with a user message and return the response."""
    
    # Extract system prompt and model from prompt parameter (or use defaults)
    prompt_param = hooks.parameters.get("prompt") if hooks and hooks.parameters else None
    
    if prompt_param and hasattr(prompt_param, "prompt"):
        # Get system message from prompt parameter
        system_prompt = next(
            (msg.content for msg in prompt_param.prompt.messages if msg.role == "system"),
            DEFAULT_SYSTEM_PROMPT
        )
        model = prompt_param.options.get("model", DEFAULT_MODEL) if hasattr(prompt_param, "options") else DEFAULT_MODEL
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT
        model = DEFAULT_MODEL

    # Get user message from dataset input
    if isinstance(input, str):
        user_message = input
    elif "input" in input:
        user_message = input["input"]
    else:
        user_message = str(input) if input else ""

    # Build messages array
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if user_message:
        messages.append({"role": "user", "content": user_message})

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    completion = client.chat.completions.create(model=model, messages=messages)

    return {"output": completion.choices[0].message.content}


# Scorer: LLM-as-a-judge
quality_scorer = LLMClassifier(
    name="Response Quality",
    prompt_template="""Evaluate this AI response:

Question: {{input}}
Response: {{output}}

Rate as: EXCELLENT, GOOD, FAIR, or POOR""",
    choice_scores={"EXCELLENT": 1.0, "GOOD": 0.75, "FAIR": 0.5, "POOR": 0.0},
    use_cot=True,
    model="gpt-4o",
)


# Scorer: Custom function
async def length_scorer(output):
    """Score based on response length (prefer 50-200 chars)."""
    length = len(output.get("output", ""))
    if length < 50:
        return 0.5
    elif length <= 200:
        return 1.0
    else:
        return 0.8


# Define evaluation
Eval(
    "example-evaluation",
    experiment_name="example-experiment",
    data=init_dataset("braintrust-modal-template", "Example Dataset"),
    task=example_task,
    scores=[quality_scorer, length_scorer],
    parameters={"prompt": SYSTEM_PROMPT_PARAM},
)


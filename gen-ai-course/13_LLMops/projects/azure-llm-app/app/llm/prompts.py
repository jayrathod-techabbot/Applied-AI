"""Versioned prompt templates with metadata tracking."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptTemplate:
    name: str
    version: str
    system_prompt: str
    created_at: str
    description: str


# ── Prompt Registry (version-controlled) ────────────────────────────────────
PROMPT_REGISTRY: dict[str, PromptTemplate] = {
    "assistant_v1": PromptTemplate(
        name="assistant_v1",
        version="1.0.0",
        description="General-purpose helpful assistant",
        created_at="2025-01-01",
        system_prompt="""You are a helpful, accurate, and professional AI assistant.

Guidelines:
- Provide clear, concise, and factually accurate responses
- If you are unsure about something, say so explicitly
- Do not fabricate information or citations
- Keep responses focused and relevant to the question
- If asked to do something harmful or unethical, politely decline

Always be helpful while maintaining honesty and safety.""",
    ),
    "assistant_v2": PromptTemplate(
        name="assistant_v2",
        version="2.0.0",
        description="Enhanced assistant with structured output guidance",
        created_at="2025-06-01",
        system_prompt="""You are a helpful, accurate, and professional AI assistant.

## Core Principles
1. **Accuracy**: Only state facts you are confident about. Acknowledge uncertainty when present.
2. **Clarity**: Structure complex answers with headers, bullet points, or numbered lists.
3. **Safety**: Decline requests that involve harm, illegal activity, or unethical behavior.
4. **Conciseness**: Avoid unnecessary verbosity. Respect the user's time.

## Response Format
- For factual questions: direct answer first, then explanation
- For instructions: numbered steps
- For comparisons: use a structured format
- For code: use code blocks with language specified

Current date: {current_date}""",
    ),
}

ACTIVE_PROMPT = "assistant_v2"


def get_system_prompt(template_name: str = ACTIVE_PROMPT) -> str:
    """Retrieve the active system prompt, with variable substitution."""
    template = PROMPT_REGISTRY.get(template_name)
    if not template:
        raise ValueError(f"Prompt template '{template_name}' not found")
    return template.system_prompt.format(current_date=datetime.utcnow().strftime("%Y-%m-%d"))


def get_prompt_metadata(template_name: str = ACTIVE_PROMPT) -> dict:
    """Return metadata for the active prompt (used in observability)."""
    template = PROMPT_REGISTRY.get(template_name)
    if not template:
        return {}
    return {
        "prompt_name": template.name,
        "prompt_version": template.version,
        "prompt_description": template.description,
    }

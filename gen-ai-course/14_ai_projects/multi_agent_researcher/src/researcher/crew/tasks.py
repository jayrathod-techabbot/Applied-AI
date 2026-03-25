"""
Task definitions for the Multi-Agent Researcher pipeline.

Tasks map directly to the delegation flow:
  1. research_task  – Researcher gathers raw data.
  2. critic_task    – Critic verifies claims; may trigger re-search.
  3. writer_task    – Writer synthesises and saves the final report.

`build_tasks(topic)` is the public factory that wires everything together.
"""

from __future__ import annotations

from crewai import Task

from researcher.crew.agents import critic_agent, researcher_agent, writer_agent


def build_tasks(topic: str) -> tuple[Task, Task, Task]:
    """
    Create the three pipeline tasks parameterised by `topic`.

    Returns
    -------
    research_task, critic_task, writer_task
    """

    research_task = Task(
        description=(
            f"Research the topic: **{topic}**\n\n"
            "Steps:\n"
            "1. Query the Azure AI Search index with at least 3 different search queries "
            "   covering different facets of the topic.\n"
            "2. Perform at least 3 web searches with varied query formulations to capture "
            "   current information.\n"
            "3. Compile a structured list of raw claims. Each claim must include:\n"
            "   - The factual statement.\n"
            "   - The source URL or document name and page number.\n"
            "   - A brief note on relevance.\n"
            "4. If the Critic requests a re-search on a specific sub-topic, perform "
            "   additional targeted searches and append the new findings.\n\n"
            "Output: A markdown list of raw claims with full source attribution."
        ),
        expected_output=(
            "A markdown-formatted list of at least 10 raw research claims, each with:\n"
            "- Claim text\n"
            "- Source (URL or document + page)\n"
            "- Relevance note\n\n"
            "Example format:\n"
            "## Raw Research Claims\n"
            "1. **Claim:** ...\n"
            "   **Source:** https://...\n"
            "   **Relevance:** ...\n"
        ),
        agent=researcher_agent,
    )

    critic_task = Task(
        description=(
            f"Critically verify the research claims compiled about: **{topic}**\n\n"
            "Steps:\n"
            "1. Read all raw claims from the Researcher's output.\n"
            "2. For each claim:\n"
            "   a. Assign a verification score from 0 (unverifiable) to 10 (fully verified).\n"
            "   b. Note whether the claim is supported, contradicted, or unverifiable.\n"
            "   c. If score < 6: specify precise refined search terms and delegate a "
            "      re-search request back to the Researcher.\n"
            "3. Collect the Researcher's revised findings and re-score them.\n"
            "4. Produce a final verified claims list that includes only claims scoring >= 6.\n\n"
            "Output: A verified claims list with scores and any flagged contradictions."
        ),
        expected_output=(
            "A markdown table of verified claims:\n"
            "| # | Claim | Score | Source | Status |\n"
            "|---|-------|-------|--------|--------|\n"
            "| 1 | ...   | 8     | URL    | Verified |\n\n"
            "Followed by a 'Flagged Issues' section listing any contradictions or "
            "claims that were dropped due to low confidence."
        ),
        agent=critic_agent,
        context=[research_task],
    )

    writer_task = Task(
        description=(
            f"Write a comprehensive research report on: **{topic}**\n\n"
            "Steps:\n"
            "1. Use the verified claims list from the Critic as your source of truth.\n"
            "2. Structure the report with the following sections:\n"
            "   - Executive Summary (3–5 sentences)\n"
            "   - Background / Context\n"
            "   - Key Findings (organised by theme, inline citations [1], [2], …)\n"
            "   - Analysis & Implications\n"
            "   - Conclusion\n"
            "   - References (numbered list of all cited sources)\n"
            "3. Every factual statement must carry at least one inline citation.\n"
            "4. After completing the markdown report, call the `cosmos_memory` tool "
            "   with operation='save', the topic, the full markdown content, and the "
            "   list of source URLs to persist the report.\n\n"
            "Output: Full markdown report + confirmation of Cosmos DB save."
        ),
        expected_output=(
            "A complete markdown research report (minimum 800 words) containing:\n"
            "- All required sections listed above\n"
            "- Inline citations throughout\n"
            "- A References section\n"
            "- A final line confirming the report was saved: "
            "  'Report saved to Cosmos DB: <document-id>'"
        ),
        agent=writer_agent,
        context=[critic_task],
    )

    return research_task, critic_task, writer_task

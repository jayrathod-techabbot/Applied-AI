"""
Agent definitions for the Multi-Agent Researcher platform.

Three agents form the research pipeline:
  - researcher_agent  : gathers raw data via Azure AI Search and web search.
  - critic_agent      : verifies facts, scores claims, requests re-searches.
  - writer_agent      : synthesises verified claims into a structured markdown report.
"""

from __future__ import annotations

from crewai import Agent
from langchain_openai import AzureChatOpenAI

from researcher.config import settings
from researcher.tools.memory_tool import CosmosMemoryTool
from researcher.tools.search_tool import AzureDocSearchTool
from researcher.tools.web_search_tool import WebSearchTool

# ---------------------------------------------------------------------------
# Shared LLM (GPT-4o via Azure OpenAI)
# ---------------------------------------------------------------------------

_llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    api_key=settings.azure_openai_key,
    azure_deployment=settings.azure_openai_deployment,
    api_version="2024-02-01",
    temperature=0.2,
)

# ---------------------------------------------------------------------------
# Tool instances
# ---------------------------------------------------------------------------

_doc_search = AzureDocSearchTool()
_web_search = WebSearchTool()
_cosmos_memory = CosmosMemoryTool()

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

researcher_agent = Agent(
    role="Research Specialist",
    goal=(
        "Gather comprehensive, accurate raw information on the assigned topic by "
        "querying the Azure AI Search document index and performing live web searches. "
        "Collect at minimum 10 distinct factual claims with their source URLs or "
        "document references."
    ),
    backstory=(
        "You are an expert research analyst with access to a proprietary document "
        "knowledge base and the live web. Your job is to cast a wide net: retrieve "
        "relevant passages from indexed documents, cross-check them with current web "
        "sources, and compile a structured list of raw claims with citations. "
        "When asked to re-search a specific sub-topic (by the Critic), you refine "
        "your search terms and try alternative queries until you surface credible evidence."
    ),
    llm=_llm,
    tools=[_doc_search, _web_search],
    verbose=True,
    allow_delegation=False,
    max_iter=8,
)

critic_agent = Agent(
    role="Fact Verification Specialist",
    goal=(
        "Review every claim produced by the Researcher. "
        "Assign each claim a verification score (0–10). "
        "Flag contradictions, unsupported assertions, or stale data. "
        "For claims scoring below 6, request a targeted re-search from the Researcher "
        "with specific refined query terms."
    ),
    backstory=(
        "You are a seasoned fact-checker and editor with deep expertise in source "
        "verification. You cross-reference claims against multiple independent sources, "
        "spot logical contradictions, and apply journalistic rigour to every statement. "
        "You communicate clearly to the Researcher exactly what additional evidence is "
        "needed when a claim cannot be verified."
    ),
    llm=_llm,
    tools=[_web_search],
    verbose=True,
    allow_delegation=True,
    max_iter=6,
)

writer_agent = Agent(
    role="Research Report Writer",
    goal=(
        "Synthesise all verified claims into a polished, well-structured markdown "
        "research report. Include an executive summary, thematic sections with inline "
        "citations, a conclusion, and a numbered list of all sources. "
        "After writing the report, persist it to Cosmos DB using the memory tool."
    ),
    backstory=(
        "You are a professional technical writer who transforms raw research findings "
        "into clear, executive-level reports. You organise information logically, "
        "write in plain English, and ensure every factual statement carries a citation. "
        "You also maintain a source-provenance record in Cosmos DB so that the report "
        "can be audited and retrieved later."
    ),
    llm=_llm,
    tools=[_cosmos_memory],
    verbose=True,
    allow_delegation=False,
    max_iter=5,
)

"""
crew_builder.py – Assembles the CrewAI Crew for a given research topic.

Public API
----------
build_crew(topic: str) -> Crew
    Returns a configured Crew ready for `crew.kickoff()`.
"""

from __future__ import annotations

from crewai import Crew, Process

from researcher.crew.agents import critic_agent, researcher_agent, writer_agent
from researcher.crew.tasks import build_tasks


def build_crew(topic: str) -> Crew:
    """
    Build and return a CrewAI Crew for the given research topic.

    Parameters
    ----------
    topic : str
        The subject matter to research (e.g. "Quantum computing advances in 2025").

    Returns
    -------
    Crew
        A fully configured CrewAI Crew instance with sequential processing
        and crew-level memory enabled.

    Notes
    -----
    - Process.sequential ensures the delegation flow:
        Researcher → Critic (with possible re-delegation) → Writer.
    - memory=True activates CrewAI's built-in short-term and long-term memory
      so agents can refer back to earlier findings within the same run.
    - verbose=True streams agent reasoning to stdout, useful for debugging.
    """

    research_task, critic_task, writer_task = build_tasks(topic)

    crew = Crew(
        agents=[researcher_agent, critic_agent, writer_agent],
        tasks=[research_task, critic_task, writer_task],
        process=Process.sequential,
        memory=True,
        verbose=True,
        full_output=True,
    )

    return crew

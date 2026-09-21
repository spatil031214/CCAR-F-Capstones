"""Synthesis Agent with proper inline citation preservation."""

import logging
import re
from typing import Dict, Any, List, Tuple
from openai import OpenAI
from models.context import ResearchContext
from models.findings import Citation, ResearchReport

logger = logging.getLogger(__name__)


class SynthesisAgentV2:
    """Synthesis agent that preserves and enhances inline citations."""

    def __init__(self, client: OpenAI, model: str = "gpt-4-turbo"):
        self.client = client
        self.model = model
        self.name = "Synthesis Agent"

    async def synthesize(
        self,
        context: ResearchContext,
        agent_reports: Dict[str, Dict[str, Any]],
    ) -> ResearchReport:
        """
        Synthesize findings while preserving inline citations.

        Args:
            context: ResearchContext with topic and tone
            agent_reports: Dictionary of agent name -> findings dict

        Returns:
            ResearchReport with synthesized content and attributed sources
        """
        logger.info(f"Synthesis Agent: Creating final report for '{context.topic}'")

        # Build system prompt emphasizing citation preservation
        system_prompt = f"""You are a master synthesist creating a comprehensive research report.

Topic: {context.topic}
Tone: {context.tone}

CRITICAL REQUIREMENTS:
1. PRESERVE ALL inline citations from source findings [Source, Year]
2. Create a clear, well-organized report
3. Use evidence from all provided sources
4. Maintain academic integrity with proper citations
5. Flag conflicting information appropriately
6. EVERY claim must have a source attribution

REPORT STRUCTURE:
1. Executive Summary (2-3 sentences with key findings)
2. Main Content (3-4 sections with INLINE CITATIONS)
3. Key Findings (with attribution)
4. Conclusion
5. Note: Bibliography will be added separately

CRITICAL: Do not remove or lose any [Source, Year] citations from the findings below."""

        # Build message with all findings and their citations preserved
        message_content = self._build_synthesis_message_with_citations(
            context, agent_reports
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": message_content,
            }
        ]

        # Call OpenAI to synthesize
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )

        # Extract synthesized content
        synthesis_text = ""
        if response.choices and response.choices[0].message.content:
            synthesis_text = response.choices[0].message.content

        # Create report with full citation preservation
        report = self._create_report_with_citations(
            context.topic,
            synthesis_text,
            agent_reports,
        )

        logger.debug(f"Report synthesized with {len(report.all_citations)} citations")

        return report

    def _build_synthesis_message_with_citations(
        self,
        context: ResearchContext,
        agent_reports: Dict[str, Dict[str, Any]],
    ) -> str:
        """Build message for synthesis, explicitly including citations."""
        message = f"Create a comprehensive research report on: {context.topic}\n\n"
        message += "IMPORTANT: The sources below have inline citations [Source, Year].\n"
        message += "PRESERVE these citations in your synthesized report.\n"
        message += "Do NOT lose or remove any source attributions.\n\n"
        message += "=" * 80 + "\n"
        message += "FINDINGS FROM RESEARCH AGENTS (with inline citations):\n"
        message += "=" * 80 + "\n\n"

        for agent_name, report in agent_reports.items():
            if report.get("status") == "completed":
                message += f"\n--- {agent_name} ---\n"
                findings = report.get("findings", "No findings.")
                message += findings

                # Also list explicit citations for this agent
                if report.get("citations"):
                    message += f"\n\nSources cited by {agent_name}:\n"
                    for citation in report.get("citations", []):
                        if isinstance(citation, dict):
                            title = citation.get("title", "Unknown")
                            message += f"  - {title}\n"
                        else:
                            message += f"  - {citation.title}\n"
                message += "\n"

            if report.get("verification"):
                message += f"\n--- Verification Results (Confidence Scores) ---\n"
                message += report.get("verification", "") + "\n"

        message += "\n" + "=" * 80 + "\n"
        message += "SYNTHESIS INSTRUCTIONS:\n"
        message += "=" * 80 + "\n"
        message += """
1. Synthesize these findings into a cohesive, well-structured report
2. KEEP ALL inline citations [Source, Year] in your report
3. Add new citations where needed for additional context
4. Organize logically by topic/theme
5. Use proper markdown formatting
6. Ensure every significant claim has a source attribution

Create the synthesized report now:
"""
        return message

    def _create_report_with_citations(
        self,
        topic: str,
        synthesis_text: str,
        agent_reports: Dict[str, Dict[str, Any]],
    ) -> ResearchReport:
        """Create a ResearchReport with proper citation preservation."""
        report = ResearchReport(topic=topic)

        # Extract summary (first paragraph)
        paragraphs = synthesis_text.split("\n\n")
        if paragraphs:
            report.summary = paragraphs[0]

        # Add synthesized content with inline citations preserved
        report.add_section("Full Report", synthesis_text)

        # Collect and deduplicate citations from all agents
        all_citations = self._collect_citations_from_agents(agent_reports)

        # Extract any additional citations from the synthesis text itself
        synthesis_citations = self._extract_citations_from_text(synthesis_text)
        for citation in synthesis_citations:
            if citation not in all_citations:
                all_citations.append(citation)

        report.all_citations = all_citations

        # Store agent reports for reference
        for agent_name, findings in agent_reports.items():
            if findings.get("findings"):
                report.agent_reports[agent_name] = findings["findings"]

        logger.debug(f"Final report has {len(report.all_citations)} total citations")
        return report

    def _collect_citations_from_agents(
        self,
        agent_reports: Dict[str, Dict[str, Any]],
    ) -> List[Citation]:
        """Collect and deduplicate citations from all agents."""
        all_citations = []
        seen_urls = set()

        for agent_name, findings in agent_reports.items():
            if findings.get("citations"):
                for citation_data in findings["citations"]:
                    # Handle both dict and Citation objects
                    if isinstance(citation_data, dict):
                        citation = Citation(**citation_data)
                    else:
                        citation = citation_data

                    # Deduplicate by URL
                    if citation.url not in seen_urls:
                        all_citations.append(citation)
                        seen_urls.add(citation.url)
                        logger.debug(f"Added citation from {agent_name}: {citation.title}")

        return all_citations

    def _extract_citations_from_text(self, text: str) -> List[Citation]:
        """Extract citations from synthesized text."""
        citations = []
        seen_sources = set()

        # Pattern: [Source Name, Year] or [Source Name]
        bracket_pattern = r'\[([^\]]+(?:,\s*\d{4})?)\]'
        for match in re.finditer(bracket_pattern, text):
            source = match.group(1).strip()
            if source not in seen_sources and source.lower() not in ["1", "2", "3"]:
                citation = Citation(
                    url=f"source://{source}",
                    title=source,
                    source_type="synthesis",
                    confidence=0.7,
                )
                citations.append(citation)
                seen_sources.add(source)

        return citations


async def example_usage():
    """Example of synthesis with citation preservation."""
    from openai import OpenAI
    from models.context import ResearchContext
    import asyncio

    client = OpenAI()
    agent = SynthesisAgentV2(client)

    # Mock agent reports with citations
    agent_reports = {
        "Web Search Agent": {
            "status": "completed",
            "findings": "AI has revolutionized healthcare [Nature Medicine, 2024]. Machine learning improves diagnosis accuracy [Google Health, 2024].",
            "citations": [
                {"url": "source://Nature Medicine, 2024", "title": "Nature Medicine, 2024", "confidence": 0.9, "source_type": "research"},
                {"url": "source://Google Health, 2024", "title": "Google Health, 2024", "confidence": 0.8, "source_type": "research"},
            ]
        }
    }

    context = ResearchContext(
        topic="AI in Healthcare",
        tone="academic",
        max_sources=5,
    )

    result = await agent.synthesize(context, agent_reports)

    print("\n=== Synthesized Report with Citations ===\n")
    print(result.to_markdown())


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

"""Synthesis Agent for combining findings into a cohesive report."""

import logging
from typing import Dict, Any, List
from openai import OpenAI
from models.context import ResearchContext
from models.findings import Citation, ResearchReport

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """Agent that synthesizes research findings into a comprehensive report."""

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
        Synthesize findings from all agents into a comprehensive report.

        Args:
            context: ResearchContext with topic and tone
            agent_reports: Dictionary of agent name -> findings dict

        Returns:
            ResearchReport with final synthesized content
        """
        logger.info(f"Synthesis Agent: Creating final report for '{context.topic}'")

        # Build the system prompt
        system_prompt = f"""You are a master synthesist creating a comprehensive research report.

Topic: {context.topic}
Tone: {context.tone}

REPORT GUIDELINES:
1. Create a clear, well-organized report
2. Use evidence from all provided sources
3. Synthesize findings into coherent sections
4. Maintain academic integrity with proper citations
5. Flag conflicting information appropriately
6. Provide a balanced perspective

REPORT STRUCTURE:
1. Executive Summary (2-3 sentences)
2. Main Content (3-4 sections based on focus areas)
3. Key Findings
4. Conclusion
5. Source Attribution"""

        # Build the message with all findings
        message_content = self._build_synthesis_message(context, agent_reports)

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

        # Call the API to synthesize with OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )

        # Extract the synthesized content
        synthesis_text = ""
        if response.choices and response.choices[0].message.content:
            synthesis_text = response.choices[0].message.content

        # Create the research report
        report = self._create_report(
            context.topic,
            synthesis_text,
            agent_reports,
        )

        logger.debug(f"Report synthesized with {len(report.all_citations)} citations")

        return report

    def _build_synthesis_message(
        self,
        context: ResearchContext,
        agent_reports: Dict[str, Dict[str, Any]],
    ) -> str:
        """Build the message for synthesis containing all findings."""
        message = f"Create a comprehensive research report on: {context.topic}\n\n"
        message += "Below are findings from multiple research agents:\n\n"

        for agent_name, report in agent_reports.items():
            if report.get("status") == "completed":
                message += f"--- {agent_name} ---\n"
                message += f"{report.get('findings', 'No findings.')}\n\n"

            if report.get("verification"):
                message += f"--- Verification Results ---\n"
                message += f"{report.get('verification', '')}\n\n"

        message += "Please synthesize these findings into a cohesive, well-structured report."
        return message

    def _create_report(
        self,
        topic: str,
        synthesis_text: str,
        agent_reports: Dict[str, Dict[str, Any]],
    ) -> ResearchReport:
        """Create a ResearchReport object from synthesized content."""
        report = ResearchReport(topic=topic)

        # Extract summary (first paragraph)
        paragraphs = synthesis_text.split("\n\n")
        if paragraphs:
            report.summary = paragraphs[0]

        # Add the full synthesis as the main section
        report.add_section("Full Report", synthesis_text)

        # Collect all citations from agent reports
        all_citations = []
        for agent_name, findings in agent_reports.items():
            if findings.get("citations"):
                for citation_dict in findings["citations"]:
                    if isinstance(citation_dict, dict):
                        citation = Citation(**citation_dict)
                    else:
                        citation = citation_dict
                    if citation not in all_citations:
                        all_citations.append(citation)

        # Deduplicate citations by URL
        seen_urls = set()
        unique_citations = []
        for citation in all_citations:
            if citation.url not in seen_urls:
                unique_citations.append(citation)
                seen_urls.add(citation.url)

        report.all_citations = unique_citations

        # Store agent reports for reference
        for agent_name, findings in agent_reports.items():
            if findings.get("findings"):
                report.agent_reports[agent_name] = findings["findings"]

        return report

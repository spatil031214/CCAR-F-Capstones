"""Web Search Agent with proper citation extraction and inline attribution."""

import logging
import re
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from models.context import ResearchContext
from models.findings import Citation

logger = logging.getLogger(__name__)


class WebSearchAgentV2:
    """Web search agent with proper source attribution."""

    def __init__(self, client: OpenAI, model: str = "gpt-4-turbo"):
        self.client = client
        self.model = model
        self.name = "Web Search Agent"

    async def research(self, context: ResearchContext) -> Dict[str, Any]:
        """
        Research with proper citation extraction and inline attribution.

        Args:
            context: ResearchContext with topic and search parameters

        Returns:
            Dictionary with findings (with inline citations), and citations list
        """
        logger.info(f"Web Search Agent: Researching '{context.topic}'")

        # Build system prompt that instructs agent to include citations
        system_prompt = f"""You are a research specialist. Your task is to thoroughly research:

{context.to_prompt()}

CRITICAL: For EVERY claim you make, include the source in this format:
- Use [Source Name, Year] or [Website Name] inline
- Include actual URLs or source identifiers
- Example: "AI has revolutionized healthcare [Nature Medicine, 2024]" or "Machine learning advances rapidly [TechCrunch, 2024]"

Structure your response as:
1. Key findings with INLINE CITATIONS
2. Each claim must be attributed to a source
3. Use consistent citation format throughout

Return findings with clear, inline source attribution."""

        # Build messages
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Please research comprehensively with inline citations: {context.topic}",
            }
        ]

        # Get research findings from OpenAI
        findings_text = ""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )

        if response.choices and response.choices[0].message.content:
            findings_text = response.choices[0].message.content

        # Extract citations from the findings text
        citations = self._extract_citations_from_text(findings_text)

        logger.debug(f"Extracted {len(citations)} citations from web search findings")

        return {
            "agent": self.name,
            "topic": context.topic,
            "findings": findings_text,
            "citations": [c.to_dict() for c in citations],
            "status": "completed",
        }

    def _extract_citations_from_text(self, text: str) -> List[Citation]:
        """
        Extract citations from research findings text.

        Looks for patterns like:
        - [Source Name, Year]
        - [Website Name]
        - (Source: URL)
        """
        citations = []
        seen_sources = set()

        # Pattern 1: [Source Name, Year] or [Source Name]
        bracket_pattern = r'\[([^\]]+(?:,\s*\d{4})?)\]'
        for match in re.finditer(bracket_pattern, text):
            source = match.group(1).strip()
            if source not in seen_sources:
                citation = Citation(
                    url=f"source://{source}",  # Placeholder URL
                    title=source,
                    source_type="research",
                    confidence=0.8,
                )
                citations.append(citation)
                seen_sources.add(source)
                logger.debug(f"Extracted citation: {source}")

        # Pattern 2: URLs in parentheses or text
        url_pattern = r'https?://[^\s\)"\]<>]+'
        for match in re.finditer(url_pattern, text):
            url = match.group(0)
            if url not in seen_sources:
                # Extract domain as title
                domain = url.split('//')[1].split('/')[0].replace('www.', '')
                citation = Citation(
                    url=url,
                    title=domain,
                    source_type="web",
                    confidence=0.9,
                )
                citations.append(citation)
                seen_sources.add(url)
                logger.debug(f"Extracted URL citation: {url}")

        return citations


async def example_usage():
    """Example of improved citation extraction."""
    from openai import OpenAI
    from models.context import ResearchContext
    import asyncio

    client = OpenAI()
    agent = WebSearchAgentV2(client)

    context = ResearchContext(
        topic="Latest developments in quantum computing",
        tone="technical",
        max_sources=5,
    )

    result = await agent.research(context)

    print("\n=== Web Search Results with Citations ===\n")
    print("FINDINGS:")
    print(result["findings"])
    print(f"\nEXTRACTED CITATIONS ({len(result['citations'])}):")
    for citation in result["citations"]:
        print(f"  - {citation['title']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

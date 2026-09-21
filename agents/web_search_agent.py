"""Web Search Agent for finding current information about topics."""

import logging
from typing import List, Dict, Any
from openai import OpenAI
from models.context import ResearchContext
from models.findings import Finding, Citation
from utils.citations import extract_citations_from_web_search

logger = logging.getLogger(__name__)


class WebSearchAgent:
    """Agent that uses web search to find information about a topic."""

    def __init__(self, client: OpenAI, model: str = "gpt-4-turbo"):
        self.client = client
        self.model = model
        self.name = "Web Search Agent"

    async def research(self, context: ResearchContext) -> Dict[str, Any]:
        """
        Research a topic using web search.

        Args:
            context: ResearchContext with topic and search parameters

        Returns:
            Dictionary with findings, citations, and summary
        """
        logger.info(f"Web Search Agent: Researching '{context.topic}'")

        # Build the system prompt
        system_prompt = f"""You are a research specialist focused on finding current, comprehensive information.

Your task is to thoroughly research the following topic:

{context.to_prompt()}

IMPORTANT INSTRUCTIONS:
1. Gather comprehensive information on the topic
2. Consider multiple perspectives
3. Extract key information and note important sources when known
4. Focus on the priority focus areas if provided
5. Return a comprehensive summary of findings with citations

Return your findings as structured data with clear source attribution where possible."""

        # Build messages with system prompt as first message
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Please research this topic comprehensively: {context.topic}",
            }
        ]

        # Run the agentic loop with OpenAI API
        all_citations = []
        findings_text = ""

        iteration = 0
        max_iterations = 2

        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Web Search iteration {iteration}/{max_iterations}")

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                messages=messages,
            )

            # Extract response text
            if response.choices and response.choices[0].message.content:
                findings_text += response.choices[0].message.content
                logger.debug("Web Search Agent finished")
                break
            else:
                logger.warning(f"Unexpected response format")
                break

        return {
            "agent": self.name,
            "topic": context.topic,
            "findings": findings_text,
            "citations": all_citations,
            "status": "completed",
        }

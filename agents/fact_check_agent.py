"""Fact-Checking Agent for verifying claims and cross-referencing information."""

import logging
from typing import Dict, Any, List
from openai import OpenAI
from models.context import ResearchContext
from models.findings import Citation

logger = logging.getLogger(__name__)


class FactCheckAgent:
    """Agent that verifies claims and cross-references information."""

    def __init__(self, client: OpenAI, model: str = "gpt-4-turbo"):
        self.client = client
        self.model = model
        self.name = "Fact-Check Agent"

    async def verify(self, context: ResearchContext, findings: str) -> Dict[str, Any]:
        """
        Verify claims in the research findings.

        Args:
            context: ResearchContext with topic and verification parameters
            findings: Text containing claims to verify

        Returns:
            Dictionary with verification results and confidence scores
        """
        logger.info(f"Fact-Check Agent: Verifying findings for '{context.topic}'")

        if not findings or not findings.strip():
            logger.warning("No findings provided for fact-checking")
            return {
                "agent": self.name,
                "topic": context.topic,
                "verification": "No findings to verify.",
                "confidence_scores": {},
                "conflicting_claims": [],
                "status": "skipped",
            }

        # Build the system prompt
        system_prompt = f"""You are a fact-checking specialist. Your task is to verify claims in research findings.

{context.to_prompt()}

VERIFICATION PROCESS:
1. Identify key claims in the provided findings
2. Assess confidence level: High (90-100%), Medium (70-89%), Low (50-69%), Unverifiable (<50%)
3. Identify any conflicting information
4. Flag unverifiable claims for manual review

Return a structured verification report with:
- Claim: The statement being verified
- Status: Verified / Partially Verified / Conflicting / Unverifiable
- Confidence: Percentage (0-100%)
- Evidence: Brief explanation or contradictory evidence"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Please verify the following research findings:\n\n{findings}",
            }
        ]

        # Run the API call with OpenAI
        logger.debug(f"Fact-check verification")

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )

        # Extract verification text
        verification_text = ""
        if response.choices and response.choices[0].message.content:
            verification_text = response.choices[0].message.content
            logger.debug("Fact-Check Agent finished")

        return {
            "agent": self.name,
            "topic": context.topic,
            "verification": verification_text,
            "confidence_scores": self._extract_confidence_scores(verification_text),
            "conflicting_claims": self._extract_conflicts(verification_text),
            "status": "completed",
        }

    def _extract_confidence_scores(self, verification_text: str) -> Dict[str, float]:
        """Extract confidence scores from verification text."""
        scores = {}
        # Simple extraction - in production, use more sophisticated parsing
        lines = verification_text.split("\n")
        for line in lines:
            if "confidence" in line.lower() and "%" in line:
                # Extract percentage values
                import re

                matches = re.findall(r"(\d+)%", line)
                if matches:
                    try:
                        score = float(matches[0]) / 100.0
                        # Store with a generic key; could be more specific
                        if "confidence_avg" not in scores:
                            scores["overall_confidence"] = score
                    except (ValueError, IndexError):
                        pass
        return scores

    def _extract_conflicts(self, verification_text: str) -> List[str]:
        """Extract conflicting claims from verification text."""
        conflicts = []
        lines = verification_text.split("\n")
        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ["conflict", "contradict", "disagree", "differs"]
            ):
                conflicts.append(line.strip())
        return conflicts

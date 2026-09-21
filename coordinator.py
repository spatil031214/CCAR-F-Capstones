"""Main Research Coordinator that orchestrates all specialized subagents."""

import logging
import asyncio
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from models.context import ResearchContext
from models.findings import ResearchReport
from agents.web_search_agent import WebSearchAgent
from agents.document_agent import DocumentAnalysisAgent
from agents.fact_check_agent import FactCheckAgent
from agents.synthesis_agent import SynthesisAgent

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class ResearchCoordinator:
    """
    Coordinates multiple specialized subagents to research a topic comprehensively.

    Task Decomposition:
    1. Web Search Agent: Finds current information from the web
    2. Document Analysis Agent: Analyzes provided documents
    3. Fact-Check Agent: Verifies claims and cross-references
    4. Synthesis Agent: Combines all findings into final report
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
        debug: bool = False,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.debug = debug

        # Initialize subagents
        self.web_search_agent = WebSearchAgent(self.client, model)
        self.document_agent = DocumentAnalysisAgent(self.client, model)
        self.fact_check_agent = FactCheckAgent(self.client, model)
        self.synthesis_agent = SynthesisAgent(self.client, model)

        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    async def research(
        self,
        topic: str,
        focus_areas: Optional[List[str]] = None,
        tone: str = "balanced",
        documents: Optional[List[Dict[str, str]]] = None,
        max_sources: int = 5,
    ) -> ResearchReport:
        """
        Coordinate research on a topic using all available agents.

        Args:
            topic: The research topic/question
            focus_areas: Optional list of areas to focus on
            tone: Report tone - academic, business, technical, balanced
            documents: Optional list of documents to analyze
            max_sources: Maximum number of sources to use

        Returns:
            ResearchReport with complete findings and citations
        """
        logger.info(f"Starting research on: {topic}")
        logger.info(f"Focus areas: {focus_areas or 'None specified'}")

        # Create research context - explicit and passed to all agents
        context = ResearchContext(
            topic=topic,
            focus_areas=focus_areas or [],
            tone=tone,
            max_sources=max_sources,
            include_document_analysis=bool(documents),
            document_paths=[doc.get("path", "") for doc in (documents or [])],
        )

        # Storage for all agent results
        agent_reports: Dict[str, Dict[str, Any]] = {}

        # Phase 1: Web Search + Document Analysis (run in PARALLEL if documents provided)
        logger.info("Phase 1: Starting parallel agents (Web Search + Document Analysis)")

        async def run_web_search():
            """Run web search agent."""
            try:
                return await self.web_search_agent.research(context)
            except Exception as e:
                logger.error(f"Web Search failed: {e}")
                return {
                    "status": "failed",
                    "error": str(e),
                    "findings": "",
                }

        async def run_document_analysis():
            """Run document analysis agent."""
            if not documents:
                logger.info("⊘ Document Analysis skipped (no documents provided)")
                return None
            try:
                return await self.document_agent.research(context, documents)
            except Exception as e:
                logger.error(f"Document Analysis failed: {e}")
                return {
                    "status": "failed",
                    "error": str(e),
                    "findings": "",
                }

        # Run both agents in parallel
        if documents:
            logger.info("Running Web Search and Document Analysis in PARALLEL...")
            web_results, doc_results = await asyncio.gather(
                run_web_search(),
                run_document_analysis(),
            )
        else:
            logger.info("Running Web Search (Document Analysis skipped)...")
            web_results = await run_web_search()
            doc_results = None

        agent_reports["Web Search Agent"] = web_results
        logger.info("✓ Web Search completed")

        if doc_results:
            agent_reports["Document Analysis Agent"] = doc_results
            logger.info("✓ Document Analysis completed")

        # Phase 3: Fact-Checking Agent
        logger.info("Phase 3: Fact-Checking")
        try:
            combined_findings = self._combine_findings(agent_reports)
            fact_check_results = await self.fact_check_agent.verify(
                context, combined_findings
            )
            agent_reports["Fact-Check Agent"] = fact_check_results
            logger.info("✓ Fact-Checking completed")
        except Exception as e:
            logger.error(f"Fact-Checking failed: {e}")
            agent_reports["Fact-Check Agent"] = {
                "status": "failed",
                "error": str(e),
                "verification": "",
            }

        # Phase 4: Synthesis Agent (Final Report)
        logger.info("Phase 4: Report Synthesis")
        try:
            final_report = await self.synthesis_agent.synthesize(context, agent_reports)
            logger.info("✓ Synthesis completed")
            logger.info(f"Final report contains {len(final_report.all_citations)} citations")
            return final_report
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            # Return a partial report if synthesis fails
            report = ResearchReport(topic=topic)
            report.summary = f"Error during synthesis: {str(e)}"
            report.agent_reports = {
                name: r.get("findings", "") for name, r in agent_reports.items()
            }
            return report

    def _combine_findings(self, agent_reports: Dict[str, Dict[str, Any]]) -> str:
        """Combine findings from all agents for fact-checking."""
        combined = ""
        for agent_name, report in agent_reports.items():
            if report.get("status") == "completed":
                combined += f"\n--- {agent_name} ---\n"
                combined += report.get("findings", "")
        return combined


async def main():
    """Example usage of the Research Coordinator."""
    import os

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")

    # Create coordinator
    coordinator = ResearchCoordinator(api_key=api_key, debug=True)

    # Research a topic
    report = await coordinator.research(
        topic="Recent advances in machine learning for healthcare",
        focus_areas=[
            "Medical imaging applications",
            "Diagnostic accuracy improvements",
            "Privacy and ethics",
        ],
        tone="academic",
        max_sources=5,
    )

    # Output results
    print("\n" + "=" * 80)
    print(report.to_markdown())
    print("=" * 80)

    return report


if __name__ == "__main__":
    # Run the async main function
    report = asyncio.run(main())

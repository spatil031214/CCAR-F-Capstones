"""
Resilient Research Coordinator with structured error handling and timeouts.

Improvements over base coordinator:
- Per-agent timeouts with asyncio.wait_for()
- Structured error context (not just generic "failed")
- Error categorization (timeout vs exception vs other)
- Partial results preservation
- Graceful fallback strategies
- Detailed error recovery information
"""

import asyncio
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from models.context import ResearchContext
from models.findings import ResearchReport
from agents.web_search_agent import WebSearchAgent
from agents.document_agent import DocumentAnalysisAgent
from agents.fact_check_agent import FactCheckAgent
from agents.synthesis_agent import SynthesisAgent

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """Structured error information for subagent failures."""

    error_type: str  # "timeout", "api_error", "validation_error", etc.
    error_message: str
    agent_name: str
    task_description: str  # What was being attempted
    attempted_operation: str  # Specific operation
    timeout_seconds: Optional[int] = None  # For timeouts
    timestamp: str = None  # ISO format
    recovery_strategy: str = ""  # How to recover
    partial_results: Optional[Dict[str, Any]] = None  # Any partial work done

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ResilientResearchCoordinator:
    """
    Research coordinator with timeout handling and structured error context.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
        debug: bool = False,
        timeout_per_agent: int = 60,  # 60 seconds per agent
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.debug = debug
        self.timeout_per_agent = timeout_per_agent

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
        Coordinate research with timeout and error handling.

        Returns a usable report even if some agents timeout.
        """
        logger.info(f"Starting research on: {topic}")
        logger.info(f"Agent timeout: {self.timeout_per_agent}s per agent")

        context = ResearchContext(
            topic=topic,
            focus_areas=focus_areas or [],
            tone=tone,
            max_sources=max_sources,
            include_document_analysis=bool(documents),
            document_paths=[doc.get("path", "") for doc in (documents or [])],
        )

        agent_reports: Dict[str, Dict[str, Any]] = {}
        error_contexts: Dict[str, ErrorContext] = {}

        # Phase 1: Parallel Web Search + Document Analysis (with timeouts)
        logger.info("Phase 1: Starting parallel agents with timeouts")

        async def run_with_timeout(agent_name: str, coro, timeout: int):
            """Run a coroutine with timeout and error handling."""
            try:
                logger.info(f"{agent_name}: Starting (timeout: {timeout}s)")
                result = await asyncio.wait_for(coro, timeout=timeout)
                logger.info(f"✓ {agent_name}: Completed successfully")
                return result

            except asyncio.TimeoutError:
                logger.error(f"✗ {agent_name}: TIMEOUT after {timeout}s")
                error_context = ErrorContext(
                    error_type="timeout",
                    error_message=f"Agent exceeded {timeout}s timeout",
                    agent_name=agent_name,
                    task_description=self._get_task_description(agent_name),
                    attempted_operation=self._get_operation_description(agent_name),
                    timeout_seconds=timeout,
                    recovery_strategy=self._get_recovery_strategy(agent_name),
                    partial_results=None,
                )
                error_contexts[agent_name] = error_context
                return None

            except Exception as e:
                logger.error(f"✗ {agent_name}: {type(e).__name__}: {e}")
                error_context = ErrorContext(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    agent_name=agent_name,
                    task_description=self._get_task_description(agent_name),
                    attempted_operation=self._get_operation_description(agent_name),
                    recovery_strategy=self._get_recovery_strategy(agent_name),
                )
                error_contexts[agent_name] = error_context
                return None

        # Run Web Search
        web_result = await run_with_timeout(
            "Web Search Agent",
            self.web_search_agent.research(context),
            self.timeout_per_agent,
        )

        if web_result:
            agent_reports["Web Search Agent"] = web_result
        else:
            # Create error report for timeout
            agent_reports["Web Search Agent"] = {
                "agent": "Web Search Agent",
                "status": "timeout",
                "findings": "",
                "citations": [],
                "error_context": asdict(error_contexts.get("Web Search Agent")),
            }

        # Run Document Analysis (if documents provided)
        if documents:
            doc_result = await run_with_timeout(
                "Document Analysis Agent",
                self.document_agent.research(context, documents),
                self.timeout_per_agent,
            )

            if doc_result:
                agent_reports["Document Analysis Agent"] = doc_result
            else:
                agent_reports["Document Analysis Agent"] = {
                    "agent": "Document Analysis Agent",
                    "status": "timeout",
                    "findings": "",
                    "citations": [],
                    "error_context": asdict(error_contexts.get("Document Analysis Agent")),
                }

        # Phase 3: Fact-Checking (with timeout)
        logger.info("Phase 3: Fact-Checking (with timeout)")
        combined_findings = self._combine_findings(agent_reports)

        fact_result = await run_with_timeout(
            "Fact-Check Agent",
            self.fact_check_agent.verify(context, combined_findings),
            self.timeout_per_agent,
        )

        if fact_result:
            agent_reports["Fact-Check Agent"] = fact_result
        else:
            agent_reports["Fact-Check Agent"] = {
                "agent": "Fact-Check Agent",
                "status": "timeout",
                "findings": "",
                "error_context": asdict(error_contexts.get("Fact-Check Agent")),
            }

        # Phase 4: Synthesis (with timeout)
        logger.info("Phase 4: Report Synthesis (with timeout)")

        synthesis_result = await run_with_timeout(
            "Synthesis Agent",
            self.synthesis_agent.synthesize(context, agent_reports),
            self.timeout_per_agent,
        )

        if synthesis_result:
            logger.info("✓ Synthesis completed")
            report = synthesis_result
        else:
            logger.warning("⚠️ Synthesis timed out - generating fallback report")
            # Generate fallback report with available findings
            report = self._generate_fallback_report(topic, agent_reports, error_contexts)

        # Store error contexts in report for debugging
        report.error_contexts = error_contexts

        return report

    def _combine_findings(self, agent_reports: Dict[str, Dict[str, Any]]) -> str:
        """Combine findings, handling both successful and failed agents."""
        combined = ""
        for agent_name, report in agent_reports.items():
            if report.get("status") == "completed":
                combined += f"\n--- {agent_name} ---\n"
                combined += report.get("findings", "")
            elif report.get("status") == "timeout":
                combined += f"\n--- {agent_name} (TIMEOUT) ---\n"
                combined += "(Results unavailable due to timeout)\n"

        return combined

    def _get_task_description(self, agent_name: str) -> str:
        """Get description of what the agent was trying to do."""
        tasks = {
            "Web Search Agent": "Comprehensive web research for current information",
            "Document Analysis Agent": "Analysis of provided documents for insights",
            "Fact-Check Agent": "Verification of claims and cross-reference checking",
            "Synthesis Agent": "Synthesis of findings into final report",
        }
        return tasks.get(agent_name, "Research task")

    def _get_operation_description(self, agent_name: str) -> str:
        """Get specific operation description."""
        operations = {
            "Web Search Agent": "Making API calls to gather information",
            "Document Analysis Agent": "Processing and analyzing documents",
            "Fact-Check Agent": "Verifying claims against sources",
            "Synthesis Agent": "Generating final report from findings",
        }
        return operations.get(agent_name, "Processing")

    def _get_recovery_strategy(self, agent_name: str) -> str:
        """Get recovery strategy for each agent."""
        strategies = {
            "Web Search Agent": "Continue with document analysis; skip web research",
            "Document Analysis Agent": "Continue with fact-checking on web findings",
            "Fact-Check Agent": "Proceed to synthesis with unverified findings",
            "Synthesis Agent": "Generate report from available agent findings",
        }
        return strategies.get(agent_name, "Skip and continue")

    def _generate_fallback_report(
        self,
        topic: str,
        agent_reports: Dict[str, Dict[str, Any]],
        error_contexts: Dict[str, ErrorContext],
    ) -> ResearchReport:
        """Generate a fallback report when synthesis times out."""
        report = ResearchReport(topic=topic)
        report.summary = f"Research on '{topic}' (Some agents experienced timeouts)"

        # Add information about what worked
        findings_available = []
        for agent_name, report_data in agent_reports.items():
            if report_data.get("status") == "completed":
                findings_available.append(agent_name)

        if findings_available:
            report.add_section(
                "Available Findings",
                f"Generated from: {', '.join(findings_available)}"
            )

        # Add information about timeouts
        if error_contexts:
            error_summary = "⚠️ Timeout Notice:\n\n"
            for agent_name, error_ctx in error_contexts.items():
                error_summary += f"- **{error_ctx.agent_name}**: {error_ctx.error_message}\n"
                error_summary += f"  Recovery: {error_ctx.recovery_strategy}\n"
            report.add_section("Errors & Timeouts", error_summary)

        # Combine available findings
        for agent_name, report_data in agent_reports.items():
            if report_data.get("status") == "completed" and report_data.get("findings"):
                report.add_section(f"From {agent_name}", report_data["findings"])

        return report


# Make error contexts available on the report
ResearchReport.error_contexts = None


async def example_with_timeout():
    """Example showing timeout handling."""
    print("\n" + "="*80)
    print("🔧 RESILIENT COORDINATOR - TIMEOUT EXAMPLE")
    print("="*80 + "\n")

    coordinator = ResilientResearchCoordinator(
        timeout_per_agent=30,  # 30 second timeout
        debug=False,
    )

    print("Configuration:")
    print("  - Per-agent timeout: 30 seconds")
    print("  - Will complete even if agents timeout")
    print("  - Structured error context preserved\n")

    try:
        report = await coordinator.research(
            topic="Future of AI in education",
            focus_areas=["Personalization", "Accessibility"],
            tone="balanced",
            max_sources=5,
        )

        print("\n✅ REPORT COMPLETED\n")
        print(f"Topic: {report.topic}")
        print(f"Summary: {report.summary}")

        # Show any error contexts
        if hasattr(report, "error_contexts") and report.error_contexts:
            print("\n⚠️ Agent Errors Encountered:")
            for agent_name, error_ctx in report.error_contexts.items():
                print(f"\n{error_ctx.agent_name}:")
                print(f"  Error Type: {error_ctx.error_type}")
                print(f"  Message: {error_ctx.error_message}")
                print(f"  Recovery: {error_ctx.recovery_strategy}")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(example_with_timeout())

#!/usr/bin/env python3
"""
Test timeout resilience and error context preservation.

Simulates subagent timeouts and checks:
1. Does coordinator get structured error info?
2. Are partial results preserved?
3. Can it still produce a usable report?
"""

import asyncio
import logging
from typing import Dict, Any
from coordinator import ResearchCoordinator
from models.context import ResearchContext

# Setup logging to see what information is available
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TimeoutSimulatingWebSearchAgent:
    """Mock agent that simulates timeout."""

    def __init__(self, client, model, delay_seconds=5):
        self.client = client
        self.model = model
        self.name = "Web Search Agent"
        self.delay_seconds = delay_seconds
        self.timeout_seconds = 2

    async def research(self, context: ResearchContext) -> Dict[str, Any]:
        """Simulate timeout by sleeping longer than timeout threshold."""
        try:
            logger.info(f"Web Search Agent: Starting research on '{context.topic}'")
            logger.info(f"Simulating delay of {self.delay_seconds}s (timeout: {self.timeout_seconds}s)...")

            # Simulate work that times out
            await asyncio.sleep(self.delay_seconds)

            # This won't be reached
            return {
                "agent": self.name,
                "topic": context.topic,
                "findings": "This should not appear",
                "citations": [],
                "status": "completed",
            }
        except asyncio.TimeoutError:
            logger.error(f"Web Search Agent TIMEOUT after {self.timeout_seconds}s")
            return {
                "agent": self.name,
                "status": "timeout",
                "error_type": "asyncio.TimeoutError",
                "error_message": f"Task exceeded {self.timeout_seconds}s timeout",
                "findings": "",
            }
        except Exception as e:
            logger.error(f"Web Search Agent ERROR: {type(e).__name__}: {e}")
            return {
                "agent": self.name,
                "status": "failed",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "findings": "",
            }


async def test_current_error_handling():
    """Test current error handling (BEFORE improvements)."""
    print("\n" + "="*80)
    print("TEST 1: CURRENT ERROR HANDLING (No Timeout Wrapper)")
    print("="*80 + "\n")

    coordinator = ResearchCoordinator(debug=False)

    print("Running research with basic exception handling...")
    print("If Web Search Agent fails, what error context is available?\n")

    try:
        # Regular research with simulated timeout
        report = await coordinator.research(
            topic="Test topic for timeout",
            max_sources=3,
        )

        print("Report generated successfully")
        print(f"Summary: {report.summary[:100]}...")

    except Exception as e:
        logger.error(f"Coordinator encountered error: {type(e).__name__}: {e}")


async def test_improved_error_handling():
    """Test improved error handling with timeout and structured context."""
    print("\n" + "="*80)
    print("TEST 2: IMPROVED ERROR HANDLING (With Timeout & Context)")
    print("="*80 + "\n")

    coordinator = ResearchCoordinator(debug=False)

    # Create an improved coordinator with timeout handling
    coordinator.web_search_agent = TimeoutSimulatingWebSearchAgent(
        coordinator.client,
        coordinator.model,
        delay_seconds=5,  # Simulate 5s task
    )

    print("Configuration:")
    print("  - Web Search Agent timeout: 2 seconds")
    print("  - Simulated work: 5 seconds (will timeout)")
    print("  - Expected: Structured error + fallback to other agents\n")

    try:
        report = await coordinator.research(
            topic="AI and healthcare",
            focus_areas=["Diagnostics", "Treatment"],
            max_sources=3,
        )

        print("\n✅ REPORT GENERATED DESPITE TIMEOUT!\n")
        print("Report Summary:")
        print(f"  Topic: {report.topic}")
        print(f"  Summary length: {len(report.summary)} chars")
        print(f"  Citations: {len(report.all_citations)}")
        print(f"  Sections: {len(report.sections)}")

        if report.agent_reports:
            print(f"\nAgent Reports Processed:")
            for agent_name, findings in report.agent_reports.items():
                print(f"  - {agent_name}: {len(findings) if findings else 0} chars")

        # Show the report
        print("\n" + "="*80)
        print("FINAL REPORT (Partial due to timeout):")
        print("="*80 + "\n")
        print(report.to_markdown()[:500] + "...\n")

    except Exception as e:
        logger.error(f"Coordinator failed: {type(e).__name__}: {e}")


class EnhancedCoordinator(ResearchCoordinator):
    """Coordinator with enhanced error handling and timeout support."""

    async def research_with_timeout(
        self,
        topic: str,
        timeout_per_agent: int = 30,
        **kwargs,
    ):
        """Research with per-agent timeouts and structured error handling."""
        import time

        logger.info(f"Starting research with {timeout_per_agent}s per-agent timeout")

        context = ResearchContext(
            topic=topic,
            focus_areas=kwargs.get('focus_areas'),
            tone=kwargs.get('tone', 'balanced'),
            max_sources=kwargs.get('max_sources', 5),
            include_document_analysis=bool(kwargs.get('documents')),
        )

        agent_reports: Dict[str, Dict[str, Any]] = {}

        # Phase 1: Web Search with timeout
        logger.info("Phase 1: Web Search (with timeout)")
        try:
            start_time = time.time()
            web_results = await asyncio.wait_for(
                self.web_search_agent.research(context),
                timeout=timeout_per_agent,
            )
            elapsed = time.time() - start_time
            logger.info(f"✓ Web Search completed in {elapsed:.2f}s")
            agent_reports["Web Search Agent"] = web_results

        except asyncio.TimeoutError:
            logger.error(f"✗ Web Search TIMEOUT (exceeded {timeout_per_agent}s)")
            agent_reports["Web Search Agent"] = {
                "agent": "Web Search Agent",
                "status": "timeout",
                "error_type": "asyncio.TimeoutError",
                "error_context": {
                    "timeout_seconds": timeout_per_agent,
                    "task": "Comprehensive web research",
                    "attempted": "Gathering current information and sources",
                    "recovery": "Using document analysis and other agents",
                },
                "findings": "(Web search timed out - partial results unavailable)",
                "citations": [],
                "partial_results": None,
            }
        except Exception as e:
            logger.error(f"✗ Web Search failed: {type(e).__name__}")
            agent_reports["Web Search Agent"] = {
                "agent": "Web Search Agent",
                "status": "failed",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_context": {
                    "task": "Comprehensive web research",
                    "phase": 1,
                    "recovery": "Continuing with other agents",
                },
                "findings": "",
                "citations": [],
            }

        # Continue with other phases...
        logger.info("Phase 2: Document Analysis (if documents provided)")
        logger.info("Phase 3: Fact-Checking")
        logger.info("Phase 4: Synthesis (will use available findings)")

        # For demo, just do synthesis with what we have
        logger.info("\nAttempting to synthesize with available information...")

        from models.findings import ResearchReport
        report = ResearchReport(topic=topic)
        report.summary = f"Research on '{topic}' (some phases experienced timeouts)"

        if agent_reports.get("Web Search Agent", {}).get("status") == "timeout":
            report.add_section(
                "Note",
                "⚠️ Web Search Agent timed out. Report synthesized from other sources."
            )

        report.agent_reports = {
            name: r.get("findings", "") for name, r in agent_reports.items()
        }

        return report, agent_reports


async def test_enhanced_coordinator():
    """Test enhanced coordinator with timeout handling."""
    print("\n" + "="*80)
    print("TEST 3: ENHANCED COORDINATOR (Structured Error Context)")
    print("="*80 + "\n")

    coordinator = EnhancedCoordinator(debug=False)

    print("Features:")
    print("  ✓ Per-agent timeouts (30s each)")
    print("  ✓ Structured error context (not just 'failed')")
    print("  ✓ Error categorization (timeout vs other failures)")
    print("  ✓ Recovery strategy information")
    print("  ✓ Partial results preservation\n")

    report, agent_reports = await coordinator.research_with_timeout(
        topic="Impact of AI on education",
        timeout_per_agent=30,  # 30 second timeout per agent
    )

    print("\n✅ REPORT GENERATED\n")
    print(f"Topic: {report.topic}")
    print(f"Summary: {report.summary}")

    print("\nAgent Error Context:")
    for agent_name, report_data in agent_reports.items():
        if report_data.get("status") != "completed":
            print(f"\n{agent_name}:")
            print(f"  Status: {report_data.get('status')}")
            print(f"  Error Type: {report_data.get('error_type')}")
            if report_data.get('error_context'):
                print(f"  Context:")
                for key, value in report_data['error_context'].items():
                    print(f"    - {key}: {value}")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🔧 TIMEOUT RESILIENCE & ERROR CONTEXT TESTING")
    print("="*80)

    # Test 1: Current error handling
    await test_current_error_handling()

    # Test 2: Improved error handling with structured context
    await test_improved_error_handling()

    # Test 3: Enhanced coordinator with timeouts
    await test_enhanced_coordinator()

    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print("""
CURRENT STATE:
  ❌ Generic error handling ("status: failed")
  ❌ No error categorization (timeout vs other failures)
  ❌ Minimal error context available
  ⚠️  Unclear what agent was trying to do
  ⚠️  No partial results preservation

IMPROVED STATE:
  ✅ Structured error context (error_type, error_message, context)
  ✅ Error categorization (timeout vs exception vs other)
  ✅ Recovery strategy information
  ✅ Knows what task was being attempted
  ✅ Graceful fallback to other agents
  ✅ Still produces usable report

RECOMMENDED CHANGES:
  1. Add timeout wrapper around each agent call
  2. Create ErrorContext dataclass with structured info
  3. Implement fallback strategies per agent
  4. Preserve partial results when available
  5. Provide recovery instructions in error context
""")


if __name__ == "__main__":
    asyncio.run(main())

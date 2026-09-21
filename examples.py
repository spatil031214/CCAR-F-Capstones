#!/usr/bin/env python3
"""
Example usage patterns for the Research Coordinator.

Run with: python examples.py
"""

import asyncio
import json
from coordinator import ResearchCoordinator


async def example_basic_research():
    """Simple research on a topic."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Research")
    print("=" * 80)

    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="What is machine learning?",
    )

    print("\nTopic:", report.topic)
    print("Summary:", report.summary)
    print("Citations:", len(report.all_citations))


async def example_focused_research():
    """Research with specific focus areas."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Focused Research with Areas")
    print("=" * 80)

    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="Impact of artificial intelligence on healthcare",
        focus_areas=[
            "Diagnostic accuracy",
            "Administrative efficiency",
            "Ethical considerations",
            "Patient privacy",
        ],
        tone="academic",
        max_sources=8,
    )

    print("\nTopic:", report.topic)
    print("Focus areas configured: 4")
    print("Final citations:", len(report.all_citations))
    print("\nReport sections:")
    for section_name in report.sections.keys():
        print(f"  - {section_name}")


async def example_academic_tone():
    """Research with academic tone."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Academic Research Report")
    print("=" * 80)

    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="Quantum computing principles and applications",
        tone="academic",
        max_sources=10,
    )

    # Export as markdown
    markdown = report.to_markdown()
    print(f"\nMarkdown report length: {len(markdown)} characters")
    print("First 500 characters:")
    print(markdown[:500])


async def example_json_export():
    """Research and export as JSON."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: JSON Export")
    print("=" * 80)

    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="Climate change mitigation strategies",
        focus_areas=["Renewable energy", "Carbon capture"],
        tone="balanced",
    )

    # Export to JSON
    report_json = report.to_dict()
    print("\nJSON structure keys:")
    print(json.dumps(list(report_json.keys()), indent=2))

    print("\nSample citation:")
    if report_json["citations"]:
        print(json.dumps(report_json["citations"][0], indent=2))


async def example_with_documents():
    """Research with document analysis."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Document Analysis")
    print("=" * 80)

    # Create sample documents
    documents = [
        {
            "path": "doc1.txt",
            "name": "Company Policy Document",
            "content": """
            Company AI Policy

            Our company is committed to responsible AI development. All AI systems
            must undergo ethics review before deployment. Teams must consider
            potential biases and ensure fairness in decision-making systems.
            """,
        },
        {
            "path": "doc2.txt",
            "name": "Industry Guidelines",
            "content": """
            AI Safety Guidelines

            Key principles for AI development:
            1. Transparency: Users should understand AI decisions
            2. Accountability: Clear responsibility chains
            3. Safety: Extensive testing before deployment
            4. Privacy: Protect user data
            """,
        },
    ]

    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="Best practices for responsible AI implementation",
        documents=documents,
        tone="technical",
    )

    print("\nTopic:", report.topic)
    print("Documents analyzed: 2")
    print("Total citations:", len(report.all_citations))
    print("Agent reports generated:")
    for agent_name in report.agent_reports.keys():
        print(f"  - {agent_name}")


async def example_multiple_topics():
    """Research multiple related topics."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Multiple Related Topics")
    print("=" * 80)

    coordinator = ResearchCoordinator()
    topics = [
        "Deep learning architectures",
        "Transformers in NLP",
        "Scaling language models",
    ]

    all_reports = []
    for topic in topics:
        print(f"\nResearching: {topic}")
        report = await coordinator.research(
            topic=topic,
            max_sources=3,
        )
        all_reports.append(report)
        print(f"  ✓ Completed ({len(report.all_citations)} citations)")

    print(f"\nProcessed {len(all_reports)} topics")
    total_citations = sum(len(r.all_citations) for r in all_reports)
    print(f"Total unique citations: {total_citations}")


async def example_business_research():
    """Business-focused research."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Business Research")
    print("=" * 80)

    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="Market trends in software development in 2026",
        focus_areas=[
            "Technology adoption",
            "Developer tools",
            "Remote work trends",
            "Skills in demand",
        ],
        tone="business",
        max_sources=8,
    )

    print("\nTopic:", report.topic)
    print("Tone: business")
    print("Focus areas: 4")
    print("Citations:", len(report.all_citations))

    # Show sample citations
    if report.all_citations:
        print("\nSample citations:")
        for i, citation in enumerate(report.all_citations[:3], 1):
            print(f"  {i}. {citation.title}")
            print(f"     URL: {citation.url}")
            print(f"     Confidence: {citation.confidence:.0%}")


async def example_technical_deep_dive():
    """Technical deep-dive research."""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Technical Deep Dive")
    print("=" * 80)

    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="Python async/await implementation details",
        tone="technical",
        focus_areas=[
            "Event loop mechanics",
            "Coroutine lifecycle",
            "Performance optimization",
        ],
        max_sources=6,
    )

    print("\nTopic:", report.topic)
    print("Tone: technical")
    print("Summary length:", len(report.summary), "characters")
    print("Report sections:", len(report.sections))
    print("Total citations:", len(report.all_citations))

    # Show comprehensive report structure
    print("\nReport structure:")
    print(f"  Summary: {len(report.summary)} chars")
    for section_name, section_content in report.sections.items():
        print(f"  Section '{section_name}': {len(section_content)} chars")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("RESEARCH COORDINATOR - EXAMPLE USAGE PATTERNS")
    print("=" * 80)

    examples = [
        ("Basic Research", example_basic_research),
        ("Focused Research", example_focused_research),
        ("Academic Tone", example_academic_tone),
        ("JSON Export", example_json_export),
        ("Document Analysis", example_with_documents),
        ("Multiple Topics", example_multiple_topics),
        ("Business Research", example_business_research),
        ("Technical Deep Dive", example_technical_deep_dive),
    ]

    print("\nRunning examples (select which to run):\n")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")

    print("\nNote: Examples require OPENAI_API_KEY environment variable")
    print("Run: python examples.py [example_number] or 'all'")

    # For demonstration, run a quick example
    print("\nRunning quick demonstration...\n")
    await example_basic_research()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

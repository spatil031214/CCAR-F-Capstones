"""Tests for the Research Coordinator."""

import pytest
import asyncio
from coordinator import ResearchCoordinator
from models.context import ResearchContext
from models.findings import Citation, Finding, ResearchReport


@pytest.mark.asyncio
async def test_coordinator_initialization():
    """Test coordinator initialization."""
    coordinator = ResearchCoordinator()
    assert coordinator.model == "gpt-4-turbo"
    assert coordinator.client is not None


@pytest.mark.asyncio
async def test_research_context_creation():
    """Test research context creation and serialization."""
    context = ResearchContext(
        topic="Test topic",
        focus_areas=["Area 1", "Area 2"],
        tone="academic",
        max_sources=5,
    )

    assert context.topic == "Test topic"
    assert len(context.focus_areas) == 2
    assert context.tone == "academic"

    # Test serialization
    prompt = context.to_prompt()
    assert "Test topic" in prompt
    assert "Area 1" in prompt
    assert "academic" in prompt


@pytest.mark.asyncio
async def test_citation_creation():
    """Test citation object creation."""
    citation = Citation(
        url="https://example.com",
        title="Example Article",
        confidence=0.95,
        source_type="web",
    )

    assert citation.url == "https://example.com"
    assert citation.title == "Example Article"
    assert citation.confidence == 0.95

    # Test markdown formatting
    markdown = citation.to_markdown()
    assert "Example Article" in markdown
    assert "https://example.com" in markdown


@pytest.mark.asyncio
async def test_finding_with_citations():
    """Test finding creation with citations."""
    citations = [
        Citation(url="https://example1.com", title="Source 1"),
        Citation(url="https://example2.com", title="Source 2"),
    ]

    finding = Finding(
        content="This is a finding",
        citations=citations,
        agent="Test Agent",
        confidence=0.85,
    )

    assert finding.content == "This is a finding"
    assert len(finding.citations) == 2
    assert finding.agent == "Test Agent"


@pytest.mark.asyncio
async def test_research_report_creation():
    """Test research report creation."""
    report = ResearchReport(topic="Test Research")

    assert report.topic == "Test Research"
    assert len(report.sections) == 0
    assert len(report.findings) == 0

    # Add sections
    report.add_section("Introduction", "Test content")
    assert "Introduction" in report.sections
    assert report.sections["Introduction"] == "Test content"

    # Add findings
    citations = [Citation(url="https://example.com", title="Example")]
    finding = Finding(content="Test finding", citations=citations)
    report.add_finding(finding)

    assert len(report.findings) == 1
    assert len(report.all_citations) == 1


@pytest.mark.asyncio
async def test_research_report_markdown_export():
    """Test research report markdown export."""
    report = ResearchReport(topic="Test Research")
    report.summary = "Test summary"
    report.add_section("Section 1", "Content 1")

    citations = [
        Citation(
            url="https://example.com",
            title="Example Source",
            confidence=0.95,
        )
    ]
    finding = Finding(content="Finding 1", citations=citations)
    report.add_finding(finding)

    markdown = report.to_markdown()

    # Check markdown format
    assert "# Test Research" in markdown
    assert "Test summary" in markdown
    assert "## Section 1" in markdown
    assert "Content 1" in markdown
    assert "## Sources" in markdown
    assert "Example Source" in markdown


@pytest.mark.asyncio
async def test_research_report_json_export():
    """Test research report JSON export."""
    report = ResearchReport(topic="Test Research")
    report.summary = "Test summary"

    citations = [Citation(url="https://example.com", title="Example")]
    report.all_citations = citations

    report_dict = report.to_dict()

    assert report_dict["topic"] == "Test Research"
    assert report_dict["summary"] == "Test summary"
    assert len(report_dict["citations"]) == 1
    assert isinstance(report_dict["citations"][0], dict)


@pytest.mark.asyncio
async def test_context_passing():
    """Test explicit context passing between components."""
    context = ResearchContext(
        topic="AI Ethics",
        focus_areas=["Bias", "Transparency"],
        tone="academic",
        previous_findings={"web_search": "Some findings"},
    )

    # Simulate passing context to an agent
    context_dict = context.to_dict()
    assert context_dict["topic"] == "AI Ethics"
    assert "web_search" in context_dict["previous_findings"]

    # Create new context from dict
    context2 = ResearchContext(**context_dict)
    assert context2.topic == context.topic
    assert context2.focus_areas == context.focus_areas


def test_citation_deduplication():
    """Test citation deduplication logic."""
    from utils.citations import deduplicate_citations

    citations = [
        Citation(url="https://a.com", title="A"),
        Citation(url="https://b.com", title="B"),
        Citation(url="https://a.com", title="A Duplicate"),  # Duplicate URL
    ]

    deduped = deduplicate_citations(citations)
    assert len(deduped) == 2

    urls = [c.url for c in deduped]
    assert urls.count("https://a.com") == 1


def test_context_serialization():
    """Test context to/from dict serialization."""
    original = ResearchContext(
        topic="Test",
        focus_areas=["A", "B"],
        tone="technical",
        max_sources=10,
    )

    # Serialize
    context_dict = original.to_dict()

    # Deserialize (without timestamp)
    context_dict.pop("timestamp")  # Remove timestamp for testing
    restored = ResearchContext(**context_dict)

    assert restored.topic == original.topic
    assert restored.focus_areas == original.focus_areas
    assert restored.tone == original.tone
    assert restored.max_sources == original.max_sources


@pytest.mark.asyncio
async def test_research_context_prompt_generation():
    """Test context to prompt conversion."""
    context = ResearchContext(
        topic="Machine Learning",
        focus_areas=["Deep Learning", "Algorithms"],
        tone="technical",
        max_sources=5,
        previous_findings={"finding1": "value1"},
    )

    prompt = context.to_prompt()

    # Verify prompt contains expected content
    assert "Machine Learning" in prompt
    assert "Deep Learning" in prompt
    assert "technical" in prompt
    assert "5" in prompt
    assert "finding1" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

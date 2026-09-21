from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Citation:
    """A source citation for a claim."""

    url: str
    title: str
    accessed_date: Optional[str] = None
    confidence: float = 0.8  # 0.0 to 1.0
    source_type: str = "web"  # web, document, verified, etc.
    snippet: str = ""  # Brief excerpt from source

    def to_markdown(self) -> str:
        """Format citation as markdown."""
        return f"[{self.title}]({self.url})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "accessed_date": self.accessed_date,
            "confidence": self.confidence,
            "source_type": self.source_type,
            "snippet": self.snippet,
        }


@dataclass
class Finding:
    """A single research finding with citations."""

    content: str
    citations: List[Citation] = field(default_factory=list)
    agent: str = ""  # Which agent produced this finding
    confidence: float = 0.8
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "citations": [c.to_dict() for c in self.citations],
            "agent": self.agent,
            "confidence": self.confidence,
            "verified": self.verified,
        }


@dataclass
class ResearchReport:
    """Final research report with all findings and synthesis."""

    topic: str
    summary: str = ""
    sections: Dict[str, str] = field(default_factory=dict)  # Section name -> content
    findings: List[Finding] = field(default_factory=list)
    all_citations: List[Citation] = field(default_factory=list)
    agent_reports: Dict[str, str] = field(default_factory=dict)  # Agent name -> detailed report
    generated_at: datetime = field(default_factory=datetime.now)

    def add_section(self, name: str, content: str):
        """Add a section to the report."""
        self.sections[name] = content

    def add_finding(self, finding: Finding):
        """Add a finding and its citations."""
        self.findings.append(finding)
        for citation in finding.citations:
            if citation not in self.all_citations:
                self.all_citations.append(citation)

    def to_markdown(self) -> str:
        """Convert report to markdown with citations."""
        markdown = f"# {self.topic}\n\n"
        markdown += f"{self.summary}\n\n"

        if self.sections:
            for section_name, content in self.sections.items():
                markdown += f"## {section_name}\n\n"
                markdown += f"{content}\n\n"

        # Bibliography
        if self.all_citations:
            markdown += "## Sources\n\n"
            for i, citation in enumerate(self.all_citations, 1):
                markdown += f"{i}. [{citation.title}]({citation.url})\n"
                if citation.confidence < 1.0:
                    markdown += f"   - Confidence: {citation.confidence:.0%}\n"
                if citation.accessed_date:
                    markdown += f"   - Accessed: {citation.accessed_date}\n"

        return markdown

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "topic": self.topic,
            "summary": self.summary,
            "sections": self.sections,
            "findings": [f.to_dict() for f in self.findings],
            "citations": [c.to_dict() for c in self.all_citations],
            "agent_reports": self.agent_reports,
            "generated_at": self.generated_at.isoformat(),
        }

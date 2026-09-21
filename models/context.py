from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ResearchContext:
    """Explicit context passed to each subagent."""

    topic: str
    focus_areas: List[str] = field(default_factory=list)
    tone: str = "balanced"  # academic, business, technical, balanced
    max_sources: int = 5
    previous_findings: Dict[str, Any] = field(default_factory=dict)
    include_document_analysis: bool = False
    document_paths: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_prompt(self) -> str:
        """Convert context to a prompt string for the agent."""
        prompt = f"Research Topic: {self.topic}\n"

        if self.focus_areas:
            prompt += f"\nFocus Areas:\n"
            for area in self.focus_areas:
                prompt += f"  - {area}\n"

        if self.previous_findings:
            prompt += f"\nPrevious Findings to Consider:\n"
            for key, value in self.previous_findings.items():
                prompt += f"  - {key}: {value}\n"

        prompt += f"\nTone: {self.tone}\n"
        prompt += f"Max Sources: {self.max_sources}\n"

        return prompt

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "topic": self.topic,
            "focus_areas": self.focus_areas,
            "tone": self.tone,
            "max_sources": self.max_sources,
            "previous_findings": self.previous_findings,
            "include_document_analysis": self.include_document_analysis,
            "document_paths": self.document_paths,
            "timestamp": self.timestamp.isoformat(),
        }

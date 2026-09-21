"""Citation extraction and formatting utilities."""

import re
from typing import List, Dict, Optional
from datetime import datetime
from models.findings import Citation


def extract_citations_from_web_search(search_results: List[dict]) -> List[Citation]:
    """
    Extract citations from web search results.

    Args:
        search_results: List of web search result objects from API

    Returns:
        List of Citation objects
    """
    citations = []

    for i, result in enumerate(search_results):
        # Web search results typically have: url, title, snippet, type
        citation = Citation(
            url=result.get("url", ""),
            title=result.get("title", f"Result {i+1}"),
            snippet=result.get("snippet", ""),
            source_type="web",
            confidence=0.9,  # Web results are high confidence
            accessed_date=datetime.now().strftime("%Y-%m-%d"),
        )
        citations.append(citation)

    return citations


def extract_citations_from_markdown(text: str) -> List[Citation]:
    """
    Extract markdown-style citations from text.

    Looks for patterns like [text](url) and {url | title}

    Args:
        text: Markdown text potentially containing citations

    Returns:
        List of extracted Citation objects
    """
    citations = []
    seen_urls = set()

    # Pattern 1: [title](url) markdown links
    markdown_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    for match in re.finditer(markdown_pattern, text):
        title, url = match.groups()
        if url not in seen_urls:
            citations.append(
                Citation(
                    url=url,
                    title=title,
                    source_type="text",
                    confidence=0.7,
                    accessed_date=datetime.now().strftime("%Y-%m-%d"),
                )
            )
            seen_urls.add(url)

    # Pattern 2: {url | title} style citations
    custom_pattern = r"\{([^|]+)\|([^}]+)\}"
    for match in re.finditer(custom_pattern, text):
        url, title = match.groups()
        url = url.strip()
        title = title.strip()
        if url not in seen_urls:
            citations.append(
                Citation(
                    url=url,
                    title=title,
                    source_type="text",
                    confidence=0.7,
                    accessed_date=datetime.now().strftime("%Y-%m-%d"),
                )
            )
            seen_urls.add(url)

    return citations


def format_inline_citation(citation: Citation, index: int) -> str:
    """Format a citation as an inline markdown reference."""
    return f"[{index}]"


def format_bibliography(citations: List[Citation]) -> str:
    """
    Format citations as a bibliography section.

    Args:
        citations: List of Citation objects

    Returns:
        Formatted bibliography markdown
    """
    if not citations:
        return ""

    bib = "## References\n\n"

    for i, citation in enumerate(citations, 1):
        bib += f"{i}. [{citation.title}]({citation.url})\n"

        if citation.accessed_date:
            bib += f"   - Accessed: {citation.accessed_date}\n"

        if citation.confidence < 1.0:
            confidence_pct = int(citation.confidence * 100)
            bib += f"   - Confidence: {confidence_pct}%\n"

        if citation.snippet:
            # Truncate long snippets
            snippet = citation.snippet[:100]
            if len(citation.snippet) > 100:
                snippet += "..."
            bib += f"   - Snippet: {snippet}\n"

        bib += "\n"

    return bib


def add_citations_to_text(
    text: str,
    citations: List[Citation],
    inline: bool = True,
) -> str:
    """
    Add citations to text.

    Args:
        text: Original text
        citations: List of citations to add
        inline: Whether to add inline citations or use superscripts

    Returns:
        Text with citations added
    """
    result = text

    if inline:
        result += "\n\n" + format_bibliography(citations)

    return result


def deduplicate_citations(citations: List[Citation]) -> List[Citation]:
    """Remove duplicate citations by URL."""
    seen = {}
    result = []

    for citation in citations:
        if citation.url not in seen:
            seen[citation.url] = True
            result.append(citation)

    return result

#!/usr/bin/env python3
"""
Research Coordinator Entry Point

Example usage:
    python main.py "What are the latest trends in artificial intelligence?"
    python main.py "Machine learning in healthcare" --tone academic --max-sources 10
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from coordinator import ResearchCoordinator

# Load environment variables from .env file
load_dotenv()


async def run_research(
    topic: str,
    focus_areas: list = None,
    tone: str = "balanced",
    documents_dir: str = None,
    max_sources: int = 5,
    output_format: str = "markdown",
):
    """Run research on a topic and return results."""

    # Initialize coordinator
    coordinator = ResearchCoordinator(
        api_key=os.getenv("OPENAI_API_KEY"),
        debug=True,
    )

    # Load documents if provided
    documents = None
    if documents_dir and Path(documents_dir).exists():
        documents = []
        for file_path in Path(documents_dir).glob("**/*.txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                documents.append({
                    "path": str(file_path),
                    "name": file_path.stem,
                    "content": f.read(),
                })
        print(f"Loaded {len(documents)} documents from {documents_dir}")

    # Run research
    print(f"\nResearching: {topic}")
    if focus_areas:
        print(f"Focus areas: {', '.join(focus_areas)}")
    print("-" * 80)

    report = await coordinator.research(
        topic=topic,
        focus_areas=focus_areas,
        tone=tone,
        documents=documents,
        max_sources=max_sources,
    )

    # Output results based on format
    print("\n" + "=" * 80)
    if output_format == "markdown":
        print(report.to_markdown())
    elif output_format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"Unknown format: {output_format}")
    print("=" * 80)

    return report


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research Coordinator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "What is quantum computing?"
  python main.py "Machine learning trends" --focus-areas "Deep Learning" "LLMs"
  python main.py "Climate change solutions" --tone academic --max-sources 10
  python main.py "Healthcare AI" --documents-dir ./medical_docs --output-format json
        """,
    )

    parser.add_argument(
        "topic",
        type=str,
        help="The research topic or question",
    )

    parser.add_argument(
        "--focus-areas",
        nargs="+",
        help="Specific areas to focus research on",
    )

    parser.add_argument(
        "--tone",
        choices=["academic", "business", "technical", "balanced"],
        default="balanced",
        help="Report tone/style (default: balanced)",
    )

    parser.add_argument(
        "--documents-dir",
        type=str,
        help="Directory containing documents to analyze",
    )

    parser.add_argument(
        "--max-sources",
        type=int,
        default=5,
        help="Maximum number of sources to use (default: 5)",
    )

    parser.add_argument(
        "--output-format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    args = parser.parse_args()

    # Run the research
    try:
        report = asyncio.run(
            run_research(
                topic=args.topic,
                focus_areas=args.focus_areas,
                tone=args.tone,
                documents_dir=args.documents_dir,
                max_sources=args.max_sources,
                output_format=args.output_format,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("\n\nResearch interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

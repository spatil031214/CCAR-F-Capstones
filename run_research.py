#!/usr/bin/env python3
"""
Simple research runner with configurable parameters.

Usage:
    python run_research.py "Your topic here" --tone academic --focus-areas "Area 1" "Area 2"
"""

import asyncio
import sys
from coordinator import ResearchCoordinator


async def main():
    # Example research topics you can modify:
    examples = [
        {
            "topic": "Latest developments in quantum computing",
            "tone": "technical",
            "focus_areas": ["Quantum algorithms", "Error correction", "Industry applications"],
            "max_sources": 5,
        },
        {
            "topic": "Impact of AI on job market",
            "tone": "balanced",
            "focus_areas": ["Job displacement", "New opportunities", "Policy implications"],
            "max_sources": 5,
        },
        {
            "topic": "Climate change solutions",
            "tone": "academic",
            "focus_areas": ["Renewable energy", "Carbon capture", "Policy frameworks"],
            "max_sources": 5,
        },
    ]

    print("\n" + "="*80)
    print("🔍 RESEARCH COORDINATOR - SELECT A TOPIC")
    print("="*80)

    print("\nAvailable examples:")
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['topic']}")
        print(f"   Tone: {example['tone']}")
        print(f"   Focus: {', '.join(example['focus_areas'])}")

    print(f"\n{len(examples) + 1}. Enter custom topic")

    while True:
        try:
            choice = input("\nSelect (1-4): ").strip()
            choice = int(choice)

            if 1 <= choice <= len(examples):
                research_config = examples[choice - 1]
                break
            elif choice == len(examples) + 1:
                print("\n📝 Enter your research topic:")
                topic = input("> ").strip()
                if not topic:
                    print("Topic cannot be empty!")
                    continue

                print("📝 Enter focus areas (comma-separated, or press Enter to skip):")
                focus_input = input("> ").strip()
                focus_areas = [f.strip() for f in focus_input.split(",")] if focus_input else None

                print("\nSelect tone (1=academic, 2=business, 3=technical, 4=balanced) [default: 4]:")
                tone_choice = input("> ").strip() or "4"
                tones = ["academic", "business", "technical", "balanced"]
                tone = tones[int(tone_choice) - 1] if tone_choice.isdigit() else "balanced"

                research_config = {
                    "topic": topic,
                    "tone": tone,
                    "focus_areas": focus_areas,
                    "max_sources": 5,
                }
                break
            else:
                print("Invalid choice. Please try again.")
        except (ValueError, IndexError):
            print("Invalid input. Please enter a number.")

    # Display configuration
    print("\n" + "="*80)
    print("📊 RESEARCH CONFIGURATION")
    print("="*80)
    print(f"📌 Topic: {research_config['topic']}")
    print(f"🎯 Tone: {research_config['tone']}")
    if research_config['focus_areas']:
        print(f"📍 Focus areas: {', '.join(research_config['focus_areas'])}")
    else:
        print(f"📍 Focus areas: None specified")
    print(f"📚 Max sources: {research_config['max_sources']}")
    print("="*80)

    print("\n⏳ Starting research... This may take a minute...\n")

    try:
        # Initialize coordinator
        coordinator = ResearchCoordinator(debug=False)

        # Run research
        report = await coordinator.research(
            topic=research_config['topic'],
            focus_areas=research_config['focus_areas'],
            tone=research_config['tone'],
            max_sources=research_config['max_sources'],
        )

        # Display results
        print("\n" + "="*80)
        print("📄 RESEARCH REPORT")
        print("="*80 + "\n")

        print(report.to_markdown())

        print("\n" + "="*80)
        print("✅ RESEARCH COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"📊 Statistics:")
        print(f"   - Citations: {len(report.all_citations)}")
        print(f"   - Report sections: {len(report.sections)}")
        print(f"   - Generated at: {report.generated_at}")
        print("="*80 + "\n")

        # Save report
        filename = f"report_{research_config['topic'].replace(' ', '_')[:30]}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report.to_markdown())
        print(f"💾 Report saved to: {filename}\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during research: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)

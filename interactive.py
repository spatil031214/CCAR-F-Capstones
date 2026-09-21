#!/usr/bin/env python3
"""
Interactive Research Coordinator - Real-time Mode

Provides an interactive interface to run research with custom topics and parameters.
"""

import asyncio
import logging
from coordinator import ResearchCoordinator

# Setup logging to show progress in real-time
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_tone() -> str:
    """Get tone preference from user."""
    print("\nSelect tone for the report:")
    tones = ["academic", "business", "technical", "balanced"]
    for i, tone in enumerate(tones, 1):
        print(f"  {i}. {tone}")

    while True:
        try:
            choice = input("\nEnter your choice (1-4) [default: 4 - balanced]: ").strip()
            if not choice:
                return "balanced"
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(tones):
                return tones[choice_idx]
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number between 1 and 4.")


def get_focus_areas() -> list:
    """Get focus areas from user."""
    print("\nEnter focus areas (comma-separated, or press Enter to skip):")
    print("Example: Deep Learning, Neural Networks, AI Safety")

    user_input = input("\nFocus areas: ").strip()
    if not user_input:
        return None

    focus_areas = [area.strip() for area in user_input.split(",") if area.strip()]
    return focus_areas if focus_areas else None


def get_max_sources() -> int:
    """Get max sources preference from user."""
    while True:
        try:
            user_input = input("\nMaximum sources to use (default: 5): ").strip()
            if not user_input:
                return 5
            max_sources = int(user_input)
            if max_sources > 0:
                return max_sources
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")


async def run_research():
    """Run research with user input."""
    print("\n" + "="*80)
    print("🔍 MULTI-AGENT RESEARCH COORDINATOR - INTERACTIVE MODE")
    print("="*80)

    # Get research topic
    print("\n📝 Enter your research topic:")
    topic = input("> ").strip()

    if not topic:
        print("Error: Topic cannot be empty.")
        return

    # Get optional parameters
    print("\n⚙️  Configure research parameters...")
    tone = get_tone()
    focus_areas = get_focus_areas()
    max_sources = get_max_sources()

    # Display configuration
    print("\n" + "="*80)
    print("📊 RESEARCH CONFIGURATION")
    print("="*80)
    print(f"Topic: {topic}")
    print(f"Tone: {tone}")
    print(f"Focus Areas: {', '.join(focus_areas) if focus_areas else 'None specified'}")
    print(f"Max Sources: {max_sources}")
    print("="*80)

    print("\n⏳ Starting research... This may take a minute...\n")

    try:
        # Initialize coordinator
        coordinator = ResearchCoordinator(debug=False)

        # Run research with real-time output
        report = await coordinator.research(
            topic=topic,
            focus_areas=focus_areas,
            tone=tone,
            max_sources=max_sources,
        )

        # Display results
        print("\n" + "="*80)
        print("📄 RESEARCH REPORT")
        print("="*80 + "\n")

        print(report.to_markdown())

        print("\n" + "="*80)
        print("✅ RESEARCH COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"Citations: {len(report.all_citations)}")
        print(f"Sections: {len(report.sections)}")
        print(f"Generated: {report.generated_at}")

        # Ask to save report
        save_choice = input("\n💾 Save report to file? (y/n) [default: y]: ").strip().lower()
        if save_choice != "n":
            filename = f"report_{topic.replace(' ', '_')[:30]}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report.to_markdown())
            print(f"✅ Report saved to: {filename}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user.")
        return
    except Exception as e:
        print(f"\n❌ Error during research: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    try:
        asyncio.run(run_research())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()

"""Command-line entrypoint for the Blank Business Builder."""

from __future__ import annotations

import argparse
import json
import webbrowser
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .onboarding import OnboardingAssistant


def serialize(obj: Any) -> Any:
    if hasattr(obj, "__dict__"):
        return {
            key: serialize(value)
            for key, value in obj.__dict__.items()
            if not key.startswith("_")
        }
    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]
    return obj


def launch_gui() -> None:
    """Launch the startup walkthrough in default browser."""
    gui_dir = Path(__file__).parent
    walkthrough_file = "startup_walkthrough.html"
    preferred_order = [
        "dark-surreal-wizard.html",
        "business_builder_gui.html",
        "dashboard.html",
        "quantum_features_dashboard.html",
        "sip_phone_dashboard.html",
    ]

    available_html = [
        path.name for path in sorted(gui_dir.glob("*.html"))
        if path.name != walkthrough_file
    ]
    if not available_html:
        print(f"[error] No GUI screens found in {gui_dir}")
        return

    preferred = [name for name in preferred_order if name in available_html]
    remaining = [name for name in available_html if name not in preferred]
    ordered_screens = preferred + remaining

    walkthrough_path = gui_dir / walkthrough_file
    if walkthrough_path.exists():
        query = urlencode({"screens": json.dumps(ordered_screens)})
        webbrowser.open(f"file://{walkthrough_path}?{query}")
        print(
            f"[info] Startup walkthrough launched with {len(ordered_screens)} screen(s): {walkthrough_path}"
        )
        print("[info] Step through screens in order, then open any screen directly.")
        return

    first_screen = gui_dir / ordered_screens[0]
    webbrowser.open(f"file://{first_screen}")
    print(f"[info] Walkthrough file missing; launched first screen instead: {first_screen}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Better Business Builder - Autonomous Passive Income Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch interactive GUI
  bbb --gui

  # Deploy autonomous business (Level 6 agents)
  bbb --autonomous --business "AI Chatbot Integration Service" --duration 24

  # Run CLI onboarding interview
  bbb

  # Export recommendations as JSON
  bbb --json > recommendations.json

Features:
  - Level 6 autonomous agents run business hands-free
  - 32+ curated business ideas across 11 industries
  - Quantum-inspired optimization ranking
  - Autonomous marketing, sales, fulfillment, support
  - Financial projections and business plan generation
  - Beautiful web GUI with real-time monitoring
        """
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the web-based GUI in your browser"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--autonomous",
        action="store_true",
        help="Deploy Level 6 autonomous agents to run business hands-free"
    )
    parser.add_argument(
        "--business",
        type=str,
        help="Business concept to run autonomously (required with --autonomous)"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=24.0,
        help="Hours to run autonomous business (default: 24)"
    )
    parser.add_argument(
        "--founder",
        type=str,
        default="Founder",
        help="Your name (for personalization)"
    )

    args = parser.parse_args()

    if args.gui:
        launch_gui()
        return

    if args.autonomous:
        if not args.business:
            print("[error] --business is required when using --autonomous")
            print("Example: bbb --autonomous --business 'AI Chatbot Integration Service'")
            return

        # Launch autonomous business
        import asyncio
        from .autonomous_business import launch_autonomous_business

        print(f"[info] Deploying Level 6 autonomous agents for: {args.business}")
        print(f"[info] Duration: {args.duration} hours")
        print(f"[info] Founder: {args.founder}")
        print("\n🚀 Launching autonomous business operation...\n")

        metrics = asyncio.run(launch_autonomous_business(
            business_concept=args.business,
            founder_name=args.founder,
            duration_hours=args.duration
        ))

        print("\n" + "="*60)
        print("✅ AUTONOMOUS OPERATION COMPLETE")
        print("="*60)
        print(json.dumps(metrics, indent=2))
        return

    # Run CLI interview
    assistant = OnboardingAssistant()
    result = assistant.run()
    serializable = {key: serialize(value) for key, value in result.items()}

    if args.json:
        print(json.dumps(serializable, indent=2))
    else:
        print("\n=== Onboarding Plan ===")
        for step in serializable["plan"]:
            print(step)
        print("\n=== Recommendation Details ===")
        for entry in serializable["recommendations"]:
            print(json.dumps(entry, indent=2))
        print("\nIRS EIN Portal:\n", serializable["irs_ein_url"])


if __name__ == "__main__":
    main()

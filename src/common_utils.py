
import json
import webbrowser
from pathlib import Path
from urllib.parse import urlencode


def launch_gui(gui_dir: Path) -> None:
    """Launch the startup walkthrough in default browser."""
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

"""
run.py
INTERide — Self-installing launcher.

Just double-click this file (or run: python run.py)
It will automatically install all required packages, then launch the app.
No manual pip install needed.
"""

import sys
import subprocess
import importlib
import os

# ── packages to auto-install ──────────────────────────────────────────────
# format: (import_name, pip_package_name)
REQUIRED: list = [
    ("geopy",           "geopy"),
    ("requests",        "requests"),
    ("PIL",             "Pillow"),
    ("docx",            "python-docx"),
    ("tkintermapview",  "tkintermapview"),
]

def check_and_install() -> None:
    missing: list = []
    for import_name, pip_name in REQUIRED:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("=" * 50)
        print("INTERide — First-time setup")
        print("=" * 50)
        print(f"Installing {len(missing)} missing package(s):")
        for pkg in missing:
            print(f"  • {pkg}")
        print()

        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade"] + missing,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            print("✓ All packages installed successfully!\n")
        except subprocess.CalledProcessError:
            # Try with --user flag if regular install fails (no admin rights)
            print("Retrying with --user flag...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--user", "--upgrade"] + missing,
                )
                print("✓ All packages installed successfully!\n")
            except subprocess.CalledProcessError as e:
                print(f"\n⚠ Could not auto-install some packages: {e}")
                print("Please run manually:  pip install " + " ".join(missing))
                input("\nPress Enter to try launching anyway...")
    else:
        print("✓ All packages ready. Launching INTERide...\n")


def launch() -> None:
    # Make sure we're running from the correct directory
    script_dir: str = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    sys.path.insert(0, script_dir)

    try:
        from app import INTERideApp
        INTERideApp().run()
    except Exception as e:
        print(f"\n✗ Error launching app: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    check_and_install()
    launch()

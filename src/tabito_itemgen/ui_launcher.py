from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def app_path() -> Path:
    return Path(__file__).with_name("ui_app.py")


def main() -> None:
    """Launch the local TABITO item-generation workbench."""
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path())],
        check=True,
    )


if __name__ == "__main__":
    main()

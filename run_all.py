from __future__ import annotations

import subprocess
import sys

def main() -> None:
    # Pass-through args to the Typer CLI entrypoint.
    cmd = [sys.executable, "-m", "sharetracker.cli"] + sys.argv[1:]
    print("Running:", " ".join(cmd))
    raise SystemExit(subprocess.call(cmd))

if __name__ == "__main__":
    main()

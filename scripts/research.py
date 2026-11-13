"""Run research management commands against the isolated local workspace only."""

import argparse
import subprocess
import sys

from dev import ROOT, development_environment


def main():
    commands = {
        "seed": "seed_research_fixture", "import": "import_research_dataset", "replay": "replay_research_run",
        "import-csv": "import_research_csv", "verify-intake": "verify_research_intake",
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=commands)
    arguments, rest = parser.parse_known_args()
    result = subprocess.run(
        [sys.executable, str(ROOT / "backend/manage.py"), commands[arguments.command], *rest],
        cwd=ROOT, env=development_environment(), check=False,
    )
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

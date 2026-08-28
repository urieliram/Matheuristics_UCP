"""Regenerate the LP digests pinned by tests/test_model.py. Run deliberately, never casually."""
import json
from pathlib import Path

from test_model import DIGESTS, lp_digest


def main():
    digests = {option: lp_digest(option) for option in ("Milp", "LR")}
    Path(DIGESTS).write_text(json.dumps(digests, indent=1) + "\n")
    print(json.dumps(digests, indent=1))


if __name__ == "__main__":
    main()

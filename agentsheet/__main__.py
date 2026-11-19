"""Entry point for ``python -m agentsheet`` from a source checkout."""

import sys

from agentsheet.cli import main

if __name__ == "__main__":
    sys.exit(main())

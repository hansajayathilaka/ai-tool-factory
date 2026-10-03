"""Studio commands, run from the repo root: python studio/factory.py <command> ... (see --help)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import factory  # noqa: E402

factory.main()

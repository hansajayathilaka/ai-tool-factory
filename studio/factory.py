"""Studio commands: python factory.py <command> ... (see python factory.py --help)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import factory  # noqa: E402

factory.main()

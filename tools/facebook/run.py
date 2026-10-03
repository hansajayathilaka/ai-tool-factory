"""Run this tool's commands: python run.py <command> ... (see python run.py --help)."""
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR.parent.parent))

from core import cli  # noqa: E402

cli.main(tool_dir=TOOL_DIR)

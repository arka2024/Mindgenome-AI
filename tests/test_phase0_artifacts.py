"""Phase 0 invariant tests. Run: python -m pytest tests/test_phase0_artifacts.py -q"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_phase0.py"


def test_phase0_validator_passes() -> None:
    sys.path.insert(0, str(SCRIPT.parent))
    mod = runpy.run_path(str(SCRIPT))
    assert mod["main"]() == 0

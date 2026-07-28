"""Keep project and legacy source imports stable during test collection."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

# Root enables `src.*`; src remains available for legacy bare imports used by
# executable modules such as `orchestrator`.
for import_root in (SRC_ROOT, PROJECT_ROOT):
    import_path = str(import_root)
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

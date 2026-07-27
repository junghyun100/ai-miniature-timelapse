"""pytest configuration - add source and project roots to Python path."""

import sys
from pathlib import Path

# Support both legacy bare imports like `import orchestrator`
# and package imports like `import src.profile_types`.
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

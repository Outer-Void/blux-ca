"""Package entrypoint for `python -m blux_ca`."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ca

if __name__ == "__main__":
    ca.main()

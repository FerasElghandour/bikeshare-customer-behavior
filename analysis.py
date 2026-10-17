"""Compatibility entry point; implementation lives in src/mobility_customers."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from mobility_customers.analysis import *

if __name__ == "__main__":
    main()

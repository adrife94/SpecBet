"""Permite ejecutar la herramienta con `python -m betting`."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())

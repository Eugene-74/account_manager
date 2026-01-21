"""PyInstaller entry-point.

Keeps package-relative imports working by importing the package module.
"""

from __future__ import annotations

from src.window import main


if __name__ == "__main__":
    main()

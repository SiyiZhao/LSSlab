"""
Mock-generation toolkit entrypoint for LSSlab.

Submodules
----------
cutsky
    Runner and utilities for cutsky-based catalog generation.
    Includes config rendering, n(z) file preparation, and script generation.
"""

from . import cutsky

__all__ = ["cutsky"]

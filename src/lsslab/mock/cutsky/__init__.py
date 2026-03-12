"""
cutsky pipeline package: prepares inputs, configs, and invocations for the external `cutsky` binary.
"""

from .nz import prepare_nz

__all__ = [
    "prepare_nz",
]

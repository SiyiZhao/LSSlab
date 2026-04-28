"""
Normalization and validation helpers for cutsky workflows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

__all__ = [
    "normalize_region",
    "normalize_regions",
    "normalize_region_path_mapping",
    "resolve_workdir_path",
]


def normalize_region(gc: str) -> str:
    """
    Normalize a single galactic-cap designation.

    Accepted values are "N" and "S".
    """
    gc = gc.upper()
    if gc not in {"N", "S"}:
        raise ValueError(f"GC must be 'N' or 'S', got {gc!r}")
    return gc


def normalize_regions(gc: str) -> list[str]:
    """
    Expand a galactic-cap spec into explicit caps.

    Supports combined inputs: "NS", "SN", "BOTH", "ALL".
    """
    gc = gc.upper()
    if gc in {"NS", "SN", "BOTH", "ALL"}:
        return ["N", "S"]
    return [normalize_region(gc)]


def normalize_region_path_mapping(
    mapping: dict[str, str | Path],
    *,
    field_name: str,
    allow_empty: bool = False,
) -> dict[str, Path]:
    """Normalize a region->path mapping to upper-case keys and absolute paths."""
    normalized = {
        str(region).upper(): Path(path).expanduser().resolve()
        for region, path in mapping.items()
    }
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must contain at least one region -> Path mapping.")
    if set(normalized) - {"N", "S"}:
        raise ValueError(f"{field_name} only supports keys 'N' and 'S'.")
    return normalized


def resolve_workdir_path(
    workdir: Path,
    path: str | Path | None = None,
    *,
    kind: Literal["data", "random", "catalog", "DATA", "RANDOM", "LSScat", "nz"],
) -> Path:
    """
    Resolve a cutsky path relative to ``workdir``.

    The default layout follows the module convention:
    ``workdir/DATA``, ``workdir/RANDOM``, and ``workdir/LSScat``.
    When ``path`` is relative, it is also interpreted under ``workdir``.
    """
    default_names = {
        "data": "DATA",
        "DATA": "DATA",
        "random": "RANDOM",
        "RANDOM": "RANDOM",
        "catalog": "LSScat",
        "LSScat": "LSScat",
        "nz": ""
    }
    candidate = Path(default_names[kind]) if path is None else Path(path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (workdir / candidate).resolve()

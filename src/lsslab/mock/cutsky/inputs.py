"""Typed input models for the cutsky workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .normalize import normalize_region_path_mapping
from typing import Iterator

__all__ = [
    "CubicMockInput",
    "CubicRandomInput",
    "CutskyInputs",
]


@dataclass(frozen=True)
class CubicMockInput:
    """Cubic mock input supporting single or multiple snapshots.

    If any of box_path, zmin, zmax is a list, all three must be lists of the same length.

    Attributes:
        boxL: Shared simulation box size.
        box_path: Path(s) to the cubic mock catalog(s).
        zmin: Minimum redshift(s) for cutsky generation.
        zmax: Maximum redshift(s) for cutsky generation.
        script_name: Optional custom script filename(s) for this/these case(s).
    """

    boxL: float
    box_path: Path | list[Path]
    zmin: float | list[float]
    zmax: float | list[float]
    script_name: str | list[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "boxL", float(self.boxL))
        if self.boxL <= 0:
            raise ValueError("boxL must be positive.")

        # Determine if we're in list mode (multiple cases)
        is_list_mode = isinstance(self.box_path, list)

        # Normalize and validate paths and redshift values
        box_path_list = self.box_path if is_list_mode else [self.box_path]
        zmin_list = self.zmin if isinstance(self.zmin, list) else [self.zmin]
        zmax_list = self.zmax if isinstance(self.zmax, list) else [self.zmax]

        # Convert to canonical form
        box_path_list = [Path(p).expanduser().resolve() for p in box_path_list]
        zmin_list = [float(z) for z in zmin_list]
        zmax_list = [float(z) for z in zmax_list]

        # Check consistency
        ncases = len(box_path_list)
        if len(zmin_list) != ncases or len(zmax_list) != ncases:
            raise ValueError(
                f"Inconsistent case counts: box_path has {len(box_path_list)}, "
                f"zmin has {len(zmin_list)}, zmax has {len(zmax_list)}. "
                "All must be the same length when using lists."
            )

        # Validate redshift ordering for each case
        for i, (z_min, z_max) in enumerate(zip(zmin_list, zmax_list)):
            if z_max <= z_min:
                raise ValueError(f"Case {i}: zmax={z_max} must be greater than zmin={z_min}.")

        # Normalize script_name
        script_name_list = None
        if self.script_name is not None:
            script_name_list = self.script_name if isinstance(self.script_name, list) else [self.script_name]
            script_name_list = [str(s) for s in script_name_list]
            if len(script_name_list) != ncases:
                raise ValueError(
                    f"If provided, script_name list must have {ncases} elements, "
                    f"got {len(script_name_list)}."
                )

        # Store normalized values
        # If input was list mode, store as tuple; otherwise store as scalar
        object.__setattr__(
            self, "box_path", tuple(box_path_list) if is_list_mode else box_path_list[0]
        )
        object.__setattr__(
            self, "zmin", tuple(zmin_list) if isinstance(self.zmin, list) else zmin_list[0]
        )
        object.__setattr__(
            self, "zmax", tuple(zmax_list) if isinstance(self.zmax, list) else zmax_list[0]
        )
        if script_name_list is not None:
            object.__setattr__(
                self,
                "script_name",
                tuple(script_name_list) if isinstance(self.script_name, list) else script_name_list[0]
            )

    def iter_cases(self) -> Iterator[tuple[Path, float, float, str | None]]:
        """Iterate over all cases, yielding (box_path, zmin, zmax, script_name) tuples."""
        box_paths = self.box_path if isinstance(self.box_path, (list, tuple)) else [self.box_path]
        zmins = self.zmin if isinstance(self.zmin, (list, tuple)) else [self.zmin]
        zmaxs = self.zmax if isinstance(self.zmax, (list, tuple)) else [self.zmax]
        
        # Handle script_name which may be None, a string, or a list/tuple of strings
        if self.script_name is None:
            script_names = [None] * len(box_paths)
        elif isinstance(self.script_name, (list, tuple)):
            script_names = self.script_name
        else:
            script_names = [self.script_name]

        for box_path, zmin, zmax, script_name in zip(box_paths, zmins, zmaxs, script_names):
            yield box_path, zmin, zmax, script_name

    def num_cases(self) -> int:
        """Return the number of cases (1 if scalar fields, len if list fields)."""
        if isinstance(self.box_path, (list, tuple)):
            return len(self.box_path)
        return 1


@dataclass(frozen=True)
class CubicRandomInput:
    """Input bundle for random-box selection and validation.

    Attributes:
        random_dir: Directory containing pre-generated random box catalogs.
        boxL: Side length of the random box.
        nsample: Reference data sample size used to derive the target random size.
        random_file_scale: Target size of one random file relative to ``nsample``.
        nfiles: Number of random box files required for one workflow run.

    Notes:
        The target number of particles per random file is computed directly
        from ``nsample``. ``random_file_scale`` is used by runner-side n(z)
        scaling only.
    """

    random_dir: Path
    boxL: float
    zmin: float
    zmax: float
    nsample: int | dict[str, int] | None = None
    random_file_scale: float = 1.0
    nfiles: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "random_dir", Path(self.random_dir).expanduser().resolve())
        object.__setattr__(self, "boxL", float(self.boxL))
        object.__setattr__(self, "zmin", float(self.zmin))
        object.__setattr__(self, "zmax", float(self.zmax))
        if self.nsample is None:
            object.__setattr__(self, "nsample", None)
        elif isinstance(self.nsample, dict):
            normalized_nsample = {str(region).upper(): int(value) for region, value in self.nsample.items()}
            if not normalized_nsample:
                raise ValueError("nsample mapping cannot be empty.")
            if set(normalized_nsample) - {"N", "S"}:
                raise ValueError("nsample mapping only supports keys 'N' and 'S'.")
            object.__setattr__(self, "nsample", normalized_nsample)
        else:
            object.__setattr__(self, "nsample", int(self.nsample))
        object.__setattr__(self, "random_file_scale", float(self.random_file_scale))
        object.__setattr__(self, "nfiles", int(self.nfiles))
        if self.boxL <= 0:
            raise ValueError("boxL must be positive.")
        if self.zmax <= self.zmin:
            raise ValueError("zmax must be greater than zmin.")
        if isinstance(self.nsample, dict):
            for region, value in self.nsample.items():
                if value <= 0:
                    raise ValueError(f"nsample for region {region} must be positive.")
        elif self.nsample is not None and self.nsample <= 0:
            raise ValueError("nsample must be positive.")
        if self.random_file_scale <= 0:
            raise ValueError("random_file_scale must be positive.")
        if self.nfiles < 1:
            raise ValueError("nfiles must be at least 1.")


@dataclass(frozen=True)
class CutskyInputs:
    """Full input bundle for a cutsky workflow."""

    mock: CubicMockInput
    random: CubicRandomInput
    footprint_path: Path
    nz_path: dict[str, Path]

    def __post_init__(self) -> None:
        object.__setattr__(self, "footprint_path", Path(self.footprint_path).expanduser().resolve())
        normalized = normalize_region_path_mapping(self.nz_path, field_name="nz_path")
        object.__setattr__(self, "nz_path", normalized)

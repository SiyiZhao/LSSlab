"""Utilities to generate uniform random box catalogs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
import pandas as pd

__all__ = [
    "RandomBoxInfo",
    "RandomBoxSummary",
    "collect_random_box_summary",
    "parse_random_box_filename",
    "prepare_random_boxes",
    "random_box_filename",
    "write_random_catalog",
]


_RANDOM_BOX_PATTERN = re.compile(
    r"^random_boxL(?P<boxsize>\d+(?:\.\d+)?(?:e[+-]?\d+)?)"
    r"_N(?P<num>\d+(?:\.\d+)?(?:e[+-]?\d+)?)"
    r"_seed(?P<seed>-?\d+)\.dat$"
)


@dataclass(frozen=True)
class RandomBoxInfo:
    """Structured metadata parsed from one random-box catalog filename.

    Attributes:
        path: Path to the catalog file.
        boxsize: Side length of the cubic box.
        num: Total number of random points in the catalog.
        seed: Random seed encoded in the filename.

    Notes:
        ``number_density`` is computed as ``num / boxsize**3``.
    """

    path: Path
    boxsize: float
    num: int
    seed: int

    @property
    def number_density(self) -> float:
        return self.num / self.boxsize**3

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "path": str(self.path),
            "boxsize": self.boxsize,
            "num": self.num,
            "seed": self.seed,
            "number_density": self.number_density,
        }


@dataclass(frozen=True)
class RandomBoxSummary:
    """Directory-level snapshot of random-box catalogs grouped by setup.

    Attributes:
        root: Absolute directory used for scanning.
        groups: Mapping from ``(boxsize, num)`` to matched catalog metadata.

    Notes:
        Use :meth:`to_dict` for machine-friendly output and ``str(summary)`` for
        a compact human-readable overview.
    """

    root: Path
    groups: dict[tuple[float, int], list[RandomBoxInfo]]

    def to_dict(self) -> dict[str, dict[str, float | int | list[int] | list[str]]]:
        summary: dict[str, dict[str, float | int | list[int] | list[str]]] = {}
        for (boxsize, num), infos in sorted(self.groups.items()):
            key = f"L={_format_boxsize(boxsize)},N={_format_num(num)}"
            ordered_infos = sorted(infos, key=lambda info: info.seed)
            summary[key] = {
                "boxsize": boxsize,
                "num": num,
                "seeds": [info.seed for info in ordered_infos],
                "number_density": num / boxsize**3,
                "files": [str(info.path) for info in ordered_infos],
            }
        return summary

    def __str__(self) -> str:
        lines = [f"RandomBoxSummary(root={self.root})"]
        for key, value in self.to_dict().items():
            lines.append(
                f"  {key}: seeds={value['seeds']}, "
                f"nbar={value['number_density']:.8g}"
            )
        return "\n".join(lines)


def _format_boxsize(boxsize: float) -> str:
    value = float(boxsize)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def _format_num(num: int) -> str:
    return f"{int(num):.1e}".replace("e+0", "e").replace("e-0", "e-")


def random_box_filename(*, boxsize: float, num: int, seed: int) -> str:
    """Build the canonical random-box filename from physical parameters.

    Args:
        boxsize: Side length of the cubic box.
        num: Number of points stored in the catalog.
        seed: Realization seed used to generate the catalog.

    Returns:
        Canonical filename in the form
        ``random_boxL{boxsize}_N{num}_seed{seed}.dat``.

    Notes:
        The formatting is normalized by internal helpers so that generation and
        parsing share the same naming convention.
    """
    return f"random_boxL{_format_boxsize(boxsize)}_N{_format_num(num)}_seed{int(seed)}.dat"


def parse_random_box_filename(path: str | Path) -> RandomBoxInfo:
    """Parse random-box metadata from a canonical filename.

    Args:
        path: File path or filename to parse.

    Returns:
        A :class:`RandomBoxInfo` object with ``path``, ``boxsize``, ``num``,
        and ``seed``.

    Raises:
        ValueError: If the basename does not match the canonical random-box
            naming pattern.
    """
    path = Path(path)
    match = _RANDOM_BOX_PATTERN.match(path.name)
    if match is None:
        raise ValueError(f"Invalid random box filename: {path.name}")

    boxsize = float(match.group("boxsize"))
    num = int(float(match.group("num")))
    seed = int(match.group("seed"))
    return RandomBoxInfo(
        path=path,
        boxsize=boxsize,
        num=num,
        seed=seed,
    )


def write_random_catalog(
    ofile: str | Path,
    num: int,
    boxsize: float,
    chunk_size: int = int(1e7),
    seed: int = 42,
) -> Path:
    """
    Write a single uniform random catalog into a cubic box.

    Args:
        ofile: Output file path.
        num: Number of random points to generate.
        boxsize: Side length of the cubic box.
        chunk_size: Number of points generated and flushed per iteration.
        seed: Seed for ``numpy.random.default_rng``.

    Returns:
        The output path as a :class:`pathlib.Path`.

    Notes:
        Coordinates are sampled uniformly in ``[0, boxsize)`` for each axis.
        Data are written as space-separated ASCII rows ``x y z`` without header.
        Chunked streaming is used to keep peak memory bounded for large ``num``.
    """

    ofile = Path(ofile)
    ofile.parent.mkdir(parents=True, exist_ok=True)

    num = int(num)
    chunk_size = int(chunk_size)
    rng = np.random.default_rng(seed)
    buf = np.empty((chunk_size, 3), dtype=np.float32)

    with open(ofile, "w", buffering=64 * 1024 * 1024) as f:
        for start in range(0, num, chunk_size):
            n = min(chunk_size, num - start)
            rng.random((n, 3), dtype=np.float32, out=buf[:n])
            buf[:n] *= np.float32(boxsize)
            pd.DataFrame(buf[:n]).to_csv(
                f,
                index=False,
                float_format="%.8g",
                sep=" ",
                header=False,
            )

    return ofile


def prepare_random_boxes(
    output_dir: str | Path,
    *,
    boxsize: float,
    num: int,
    seed: int,
    nran: int = 1,
    chunk_size: int = int(1e7),
) -> list[Path]:
    """
    Prepare one or more random-box realizations in a target directory.

    Args:
        output_dir: Directory where random-box files are placed.
        boxsize: Side length of the cubic box.
        num: Number of points per realization.
        seed: Seed of the first realization.
        nran: Number of realizations to prepare. Realization ``i`` uses
            ``seed + i``.
        chunk_size: Chunk size passed to :func:`write_random_catalog`.

    Returns:
        List of output file paths, ordered by realization seed.

    Raises:
        ValueError: If ``nran < 1``.

    Notes:
        Existing files are reused (not overwritten). This behavior enables
        incremental reruns without regenerating completed realizations.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    num = int(num)
    nran = int(nran)
    if nran < 1:
        raise ValueError("nran must be at least 1.")

    box_paths: list[Path] = []
    for offset in range(nran):
        current_seed = int(seed) + offset
        ofile = output_dir / random_box_filename(
            boxsize=boxsize,
            num=num,
            seed=current_seed,
        )
        if ofile.exists():
            print(f"Random box file {ofile} already exists; skipping generation.")
            box_paths.append(ofile)
            continue

        box_paths.append(
            write_random_catalog(
                ofile=ofile,
                num=num,
                boxsize=boxsize,
                chunk_size=chunk_size,
                seed=current_seed,
            )
        )

    return box_paths


def collect_random_box_summary(workdir: str | Path) -> RandomBoxSummary:
    """
    Scan a directory and summarize random-box catalogs by ``(boxsize, num)``.

    Args:
        workdir: Directory to scan.

    Returns:
        A :class:`RandomBoxSummary` containing grouped file metadata.

    Notes:
        Only files directly under ``workdir`` are considered (non-recursive).
        Files are selected by canonical filename pattern only; file contents are
        not opened or validated.
    """

    scan_dir = Path(workdir).expanduser().resolve()

    groups: dict[tuple[float, int], list[RandomBoxInfo]] = {}
    for path in sorted(scan_dir.iterdir()):
        if not path.is_file():
            continue
        if _RANDOM_BOX_PATTERN.match(path.name) is None:
            continue
        info = parse_random_box_filename(path)
        groups.setdefault((info.boxsize, info.num), []).append(info)

    for infos in groups.values():
        infos.sort(key=lambda info: info.seed)

    return RandomBoxSummary(root=scan_dir, groups=groups)

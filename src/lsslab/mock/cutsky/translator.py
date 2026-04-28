"""
Translate cutsky lightcone mock ASCII files into catalog formats.

This module provides functions to merge multiple cutsky output files,
split random catalogs, and convert them to standard catalog formats.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from .normalize import (
    normalize_region,
    resolve_workdir_path,
)
from .utils import read_cutsky_data


__all__ = [
    "merge_cutsky_catalog",
    "split_random_cutsky_catalogs", 
    "trans_random_cats",
]


def _read_and_merge(workdir: Path, pattern: str) -> pd.DataFrame:
    """
    Read and merge cutsky files matching a glob pattern.

    Parameters
    ----------
    workdir : Path
        Directory to search for files.
    pattern : str
        Glob pattern to match files (e.g., "cutsky_N_*.dat").

    Returns
    -------
    pd.DataFrame
        Merged data from all matching files.

    Raises
    ------
    FileNotFoundError
        If no files match the pattern.
    """
    files = sorted(path for path in workdir.glob(pattern) if path.is_file())
    if not files:
        raise FileNotFoundError(
            f"No files matching '{pattern}' found in {workdir}"
        )
    merged = pd.concat(
        [read_cutsky_data(path, status_select=2) for path in files],
        ignore_index=True,
    )
    print(f"[read] merged {len(files)} files from {workdir}")
    return merged


def _to_hdf5_catalog(
    df: pd.DataFrame,
    output_path: Path | str,
    engine: str = "h5py",
) -> None:
    """
    Convert DataFrame to HDF5 catalog format.

    Parameters
    ----------
    df : pd.DataFrame
        Catalog data with columns: RA, DEC, Z, NZ.
    output_path : Path or str
        Output HDF5 file path.
    engine : str, optional
        HDF5 engine ('h5py' or 'pytables'). Default: 'h5py'.
    """
    output_path = Path(output_path)
    data = {
        "RA": np.asarray(df["RA"], dtype="f8"),
        "DEC": np.asarray(df["DEC"], dtype="f8"),
        "Z": np.asarray(df["Z"], dtype="f8"),
        "NX": np.asarray(df["NZ"], dtype="f8"),  # Note: NZ -> NX in output
    }
    
    # Try to use mpytools if available
    try:
        from mpytools import Catalog
        catalog = Catalog.from_dict(data=data)
        catalog.write(str(output_path))
    except ImportError:
        # Fallback to pandas HDF5 storage
        df_out = pd.DataFrame(data)
        df_out.to_hdf(str(output_path), key="catalog", mode="w", engine=engine)


def merge_cutsky_catalog(
    workdir: str | Path,
    tracer: str = "QSO",
    GC: str = "N",
    output_fn: str | Path | None = None,
    output_dir: str | Path | None = None,
    data_dir: str | Path | None = None,
) -> Path:
    """
    Read all ``cutsky_<GC>_*.dat`` files in ``workdir``, merge them, and save
    the result as a catalog file.

    Parameters
    ----------
    workdir : str or Path
        Directory containing ``cutsky_<GC>_*.dat`` files.
    tracer : str, optional
        Tracer name for output filenames. Default: "QSO".
    GC : str, optional
        Galactic cap: 'N' (NGC) or 'S' (SGC). Default: 'N'.
    output_fn : str or Path, optional
        Output catalog file path. If None, defaults to
        ``<output_dir>/<tracer>_<GC>GC_clustering.dat.h5``.
    output_dir : str or Path, optional
        Output directory; default is ``<workdir>/LSScat``.
    data_dir : str or Path, optional
        Directory containing data-side cutsky outputs. If relative, interpreted
        under ``workdir``. Default is ``DATA``.

    Returns
    -------
    Path
        Path to the saved catalog file.

    Raises
    ------
    FileNotFoundError
        If no matching cutsky files are found.
    """
    workdir = Path(workdir).expanduser().resolve()
    GC = normalize_region(GC)
    data_root = resolve_workdir_path(workdir, data_dir, kind="data")
    merged = _read_and_merge(data_root, f"cutsky_{GC}_*.dat")
    
    if output_fn is None:
        output_dir_path = resolve_workdir_path(workdir, output_dir, kind="catalog")
        output_fn = output_dir_path / f"{tracer}_{GC}GC_clustering.dat.h5"
    else:
        output_fn = Path(output_fn).expanduser().resolve()

    output_fn.parent.mkdir(parents=True, exist_ok=True)
    _to_hdf5_catalog(merged, output_fn)

    print(f"[write] data catalog -> {output_fn}")
    print(f"[size] {len(merged)} rows")
    return output_fn


def split_random_cutsky_catalogs(
    workdir: str | Path,
    tracer: str = "QSO",
    GC: str = "N",
    nsplit: int = 10,
    seed: int = 42,
    output_dir: str | Path | None = None,
    random_dir: str | Path | None = None,
) -> list[Path]:
    """
    Read ``workdir/RANDOM/cutsky_<GC>*.dat``, randomly split into ``nsplit``
    subcatalogs, and save each one.

    Parameters
    ----------
    workdir : str or Path
        Base working directory.
    tracer : str, optional
        Tracer name for output filenames. Default: "QSO".
    GC : str, optional
        Galactic cap: 'N' or 'S'. Default: 'N'.
    nsplit : int, optional
        Number of random splits. Default: 10.
    seed : int, optional
        Random seed for splitting. Default: 42.
    output_dir : str or Path, optional
        Output directory; default is ``<workdir>/LSScat``.
    random_dir : str or Path, optional
        Directory containing random-side cutsky outputs. If relative,
        interpreted under ``workdir``. Default is ``RANDOM``.

    Returns
    -------
    list[Path]
        List of paths to saved catalog files.

    Raises
    ------
    FileNotFoundError
        If no matching random catalog files are found.
    """
    workdir = Path(workdir).expanduser().resolve()
    GC = normalize_region(GC)
    random_root = resolve_workdir_path(workdir, random_dir, kind="random")
    merged = _read_and_merge(random_root, f"cutsky_{GC}*.dat")

    rng = np.random.default_rng(seed)
    shuffled = merged.iloc[rng.permutation(len(merged))].reset_index(drop=True)
    chunks = np.array_split(np.arange(len(shuffled)), nsplit)

    output_dir_path = resolve_workdir_path(workdir, output_dir, kind="catalog")
    output_dir_path.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    for isplit, indices in enumerate(chunks):
        subset = shuffled.iloc[indices].reset_index(drop=True)
        subset_copy = subset.copy()
        subset_copy["NZ"] = subset_copy["NZ"] / nsplit  # Scale weights

        output_fn = output_dir_path / f"{tracer}_{GC}GC_{isplit}_clustering.ran.h5"
        _to_hdf5_catalog(subset_copy, output_fn)

        print(f"[write] random split {isplit} -> {output_fn}")
        print(f"[size] {len(subset)} rows")
        outputs.append(output_fn)

    return outputs


def trans_random_cats(
    workdir: str | Path,
    tracer: str = "QSO",
    GC: str = "N",
    output_dir: str | Path | None = None,
    random_dir: str | Path | None = None,
) -> list[Path]:
    """
    Read ``workdir/RANDOM/cutsky_<GC>*_ran<i>.dat`` files, merge files with
    the same ``<i>``, and save each group as a catalog.

    This function expects random catalog files with naming pattern:
    ``cutsky_<GC>*_ran<i>.dat``, where ``<i>`` is a split index.

    Parameters
    ----------
    workdir : str or Path
        Base working directory.
    tracer : str, optional
        Tracer name for output filenames. Default: "QSO".
    GC : str, optional
        Galactic cap: 'N' or 'S'. Default: 'N'.
    output_dir : str or Path, optional
        Output directory; default is ``<workdir>/LSScat``.
    random_dir : str or Path, optional
        Directory containing random-side cutsky outputs. If relative,
        interpreted under ``workdir``. Default is ``RANDOM``.

    Returns
    -------
    list[Path]
        List of paths to saved catalog files.

    Raises
    ------
    FileNotFoundError
        If no matching random catalog files are found.
    """
    workdir = Path(workdir).expanduser().resolve()
    GC = normalize_region(GC)
    random_dir = resolve_workdir_path(workdir, random_dir, kind="random")
    files = sorted(
        path for path in random_dir.glob(f"cutsky_{GC}*_ran*.dat")
        if path.is_file()
    )
    if not files:
        raise FileNotFoundError(
            f"No files matching 'cutsky_{GC}*_ran*.dat' found in {random_dir}"
        )

    ran_pattern = re.compile(r"_ran(\d+)\.dat$")
    grouped_files: dict[int, list[Path]] = {}
    for path in files:
        match = ran_pattern.search(path.name)
        if match is None:
            continue
        isplit = int(match.group(1))
        grouped_files.setdefault(isplit, []).append(path)

    if not grouped_files:
        raise FileNotFoundError(
            f"No files with suffix '_ran<i>.dat' found in {random_dir}"
        )

    output_dir_path = resolve_workdir_path(workdir, output_dir, kind="catalog")
    output_dir_path.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    for isplit in sorted(grouped_files):
        merged = pd.concat(
            [read_cutsky_data(path, status_select=2) for path in grouped_files[isplit]],
            ignore_index=True,
        )

        output_fn = output_dir_path / f"{tracer}_{GC}GC_{isplit}_clustering.ran.h5"
        _to_hdf5_catalog(merged, output_fn)

        print(f"[read] split {isplit}: {grouped_files[isplit]}")
        print(f"[write] random ran{isplit} -> {output_fn}")
        print(f"[size] {len(merged)} rows")
        outputs.append(output_fn)

    return outputs

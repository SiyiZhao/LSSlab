"""Utilities to generate cutsky random box catalogs (no redshift binning)."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

__all__ = ["write_random_catalog"]


def write_random_catalog(
    ofile: str | Path,
    num: int,
    boxL: float,
    chunk_size: int = int(1e7),
    seed: int = 42,
) -> Path:
    """Write a uniform random catalog inside a box of size ``boxL``.

    Generates ``num`` points with coordinates in ``[0, boxL)`` for each axis and
    streams them to disk in chunks to avoid large memory use.
    """

    ofile = Path(ofile)
    ofile.parent.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(seed)
    chunk_size = int(chunk_size)
    buf = np.empty((chunk_size, 3), dtype=np.float32)

    with open(ofile, "w", buffering=64 * 1024 * 1024) as f:
        for start in range(0, num, chunk_size):
            n = min(chunk_size, num - start)
            rng.random((n, 3), dtype=np.float32, out=buf[:n])
            buf[:n] *= np.float32(boxL)
            pd.DataFrame(buf[:n]).to_csv(
                f,
                index=False,
                float_format="%.8g",
                sep=" ",
                header=False,
            )

    return ofile


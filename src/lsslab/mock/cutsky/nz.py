"""
Utilities to transform DESI-style n(z) files into the format expected by `cutsky`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

__all__ = ["prepare_nz"]


def prepare_nz(
    source: Path | str,
    dest: Path | str,
    times: float = 1.0,
) -> None:
    """
    Transform a standard DESI-format n(z) file into the format required by `cutsky`.

    Parameters
    ----------
    source : str or Path
        Input n(z) file in the standard NERSC format.
    dest : str or Path
        Output path for the converted n(z) file to be consumed by `cutsky`.
    times : float, optional
        Optional scaling factor to apply to n(z) values.
    """

    data = np.loadtxt(source)
    # zmid zlow zhigh n(z) Nbin Vol_bin
    zmid = data[:, 0]
    nz = data[:, 3]
    zlow = data[:, 1]
    zhigh = data[:, 2]
    data_2 = np.column_stack((zmid, nz * times))
    data_out = np.row_stack(([zlow[0], nz[0] * times], data_2, [zhigh[-1], nz[-1] * times]))

    np.savetxt(dest, data_out, header=f"original file {source}\n n(z) times {times}\n zmid n(z)")
    print(f"[write] n(z) file -> {dest}")

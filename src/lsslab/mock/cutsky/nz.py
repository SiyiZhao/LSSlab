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
    Converts 6-column DESI n(z) format to 2-column cutsky format.

    Parameters
    ----------
    source : str or Path
        Input n(z) file in DESI format with columns: zmid zlow zhigh n(z) Nbin Vol_bin
    dest : str or Path
        Output path for the converted n(z) file to be consumed by `cutsky`.
    times : float, optional
        Optional scaling factor to apply to n(z) values. Default: 1.0 (no scaling).

    Returns
    -------
    None

    Side Effects
    -----------
    Creates output file at `dest` with 2-column format: zmid n(z)
    Prints confirmation message to stdout.

    Examples
    --------
    >>> from lsslab.mock.cutsky import prepare_nz
    >>> prepare_nz("input/desi_nz.txt", "output/nz_cutsky.txt")
    [write] n(z) file -> output/nz_cutsky.txt

    With scaling:
    >>> prepare_nz("desi_nz.txt", "nz_cutsky.txt", times=2.0)  # Double the n(z)
    """

    data = np.loadtxt(source)
    zmid = data[:, 0]
    nz = data[:, 3]
    zlow = data[:, 1]
    zhigh = data[:, 2]
    data_2 = np.column_stack((zmid, nz * times))
    data_out = np.row_stack(([zlow[0], nz[0] * times], data_2, [zhigh[-1], nz[-1] * times]))

    np.savetxt(dest, data_out, header=f"original file {source}\n n(z) times {times}\n zmid n(z)")
    print(f"[write] n(z) file -> {dest}")

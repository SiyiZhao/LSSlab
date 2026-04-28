"""
Utility functions for reading and processing cutsky catalog data.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from lsslab.tools.random_box import RandomBoxInfo, RandomBoxSummary


__all__ = [
    "RandomBoxValidationResult",
    "read_cutsky_data",
    "validate_random_box_catalogs",
]


@dataclass(frozen=True)
class RandomBoxValidationResult:
    """Outcome of random-box validation for one region."""

    selected_infos: list[RandomBoxInfo]
    failed_checks: list[str]


def _suggest_minimum_random_num(*, threshold: float, boxsize: float) -> tuple[int, str]:
    n_min = int(math.floor(threshold * boxsize**3)) + 1
    if n_min <= 0:
        return n_min, "0.0e+00"

    exponent = int(math.floor(math.log10(n_min)))
    coeff = n_min / (10**exponent)
    coeff_ceil = math.ceil(coeff * 10) / 10

    if coeff_ceil >= 10.0:
        coeff_ceil = 1.0
        exponent += 1

    sign = "+" if exponent >= 0 else "-"
    return n_min, f"{coeff_ceil:.1f}e{sign}{abs(exponent)}"


def validate_random_box_catalogs(
    *,
    summary: RandomBoxSummary,
    cap: str,
    boxL: float,
    target_num: int,
    density_threshold: float,
    nfiles_required: int,
) -> RandomBoxValidationResult:
    """Validate and select random-box catalogs for one region."""

    target_boxsize = float(boxL)
    target_num = int(target_num)
    density_threshold = float(density_threshold)
    nfiles_required = int(nfiles_required)

    target_infos: Sequence[RandomBoxInfo] = summary.groups.get((target_boxsize, target_num), [])
    selected_infos = sorted(target_infos, key=lambda info: info.seed)[:nfiles_required]
    selected_density_sum = sum(info.number_density for info in selected_infos)
    required_density_sum = density_threshold * float(nfiles_required)

    failed_checks: list[str] = []
    if selected_density_sum <= required_density_sum:
        suggest_n_min, suggest_n_min_sci = _suggest_minimum_random_num(
            threshold=density_threshold,
            boxsize=target_boxsize,
        )
        failed_checks.append(
            f"[{cap}] Density check failed: "
            f"sum_density={selected_density_sum:.8g} <= required_sum={required_density_sum:.8g} "
            f"(per-file threshold={density_threshold:.8g}); "
            f"suggest N_min per file={suggest_n_min_sci} ({suggest_n_min})"
        )

    if len(target_infos) < nfiles_required:
        failed_checks.append(
            f"[{cap}] File count check failed: "
            f"available={len(target_infos)} < required={nfiles_required}"
        )

    return RandomBoxValidationResult(
        selected_infos=list(selected_infos),
        failed_checks=failed_checks,
    )


def read_cutsky_data(
    filepath: str | Path,
    status_select: int | None = None,
) -> pd.DataFrame:
    """
    Read a cutsky ASCII data file into a pandas DataFrame.

    The cutsky output format contains whitespace-separated columns:
    RA, DEC, Z, Z_COSMO, NZ, STATUS, RAN_NUM_0_1.

    Parameters
    ----------
    filepath : str or Path
        Path to the cutsky .dat file.
    status_select : int or None, optional
        If provided, select rows with STATUS equal to this value. For `cutsky` standard output, use `status_select=2` to select objects that pass the n(z) cut. If None, no filtering is applied.

    Returns
    -------
    pd.DataFrame
        If ``status_select`` is provided, returns columns ``RA``, ``DEC``,
        ``Z``, ``NZ`` for matching rows only. Otherwise returns all rows with
        columns ``RA``, ``DEC``, ``Z``, ``NZ``, ``STATUS``.
    """
    filepath = Path(filepath)

    # The input file uses a commented header line, so we read with explicit
    # column names and keep only the columns needed downstream.
    df = pd.read_csv(
        filepath,
        sep=r"\s+",
        comment="#",
        header=None,
        names=["RA", "DEC", "Z", "Z_COSMO", "NZ", "STATUS", "RAN_NUM_0_1"],
        dtype={
            "RA": np.float64,
            "DEC": np.float64,
            "Z": np.float64,
            "NZ": np.float64,
            "STATUS": np.int64,
        },
        usecols=["RA", "DEC", "Z", "NZ", "STATUS"],
    )

    if status_select is not None:
        return df.loc[df["STATUS"] == status_select, ["RA", "DEC", "Z", "NZ"]].reset_index(drop=True)
    else:
        return df[["RA", "DEC", "Z", "NZ", "STATUS"]].reset_index(drop=True)

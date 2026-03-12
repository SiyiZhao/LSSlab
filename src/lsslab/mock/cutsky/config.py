"""
Config rendering helpers for the external `cutsky` binary.
"""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "cutsky_cfg",
]


def cutsky_cfg(
    box_path: str,
    boxsize: float,
    lc_out_path: str,
    Omega_m: float = 0.315192,
    Omega_l: float | None = None,
    w_DE_EOS: float = -1.0,
    footprint_path: str = "/global/homes/s/siyizhao/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply",
    galactic_cap: str = "N",
    nz_path: str = "/global/homes/s/siyizhao/projects/LSSlab/examples/data/example_nz.txt",
    zmin: float = 0.405,
    zmax: float = 0.6,
    write_to: str | None = None,
) -> str:
    """
    Write the cutsky configuration file and return its content.

    If `write_to` is provided, the file is written there. Otherwise only the content string is returned.

    Parameters
    ----------
    box_path : str
        Path to the input catalog.
    boxsize : float
        Size of the simulation box in Mpc/h.
    lc_out_path : str
        Path to save the output lightcone catalog.
    Omega_m : float, optional
        Matter density parameter. Defaults to 0.315192 (DESI value).
    Omega_l : float, optional
        Dark energy density parameter. If None, it is set to 1 - Omega_m. Defaults to None.
    w_DE_EOS : float, optional
        Dark energy equation of state parameter. Defaults to -1.0.
    footprint_path : str, optional
        Path to the footprint file. Defaults to "/global/homes/s/siyizhao/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply".
    galactic_cap : str, optional
        Galactic cap to use ("N" or "S"). Defaults to "N".
    nz_path : str, optional but recommended
        Path to the n(z) file.
    zmin : float, optional but recommended
        Minimum redshift. Defaults to 0.405.
    zmax : float, optional but recommended
        Maximum redshift. Defaults to 0.6.
    write_to : str or None, optional
        If provided, write the configuration to this path. Defaults to None.
    Returns
    -------
    str
        The rendered configuration content, regardless of whether it was written.
    """

    if Omega_l is None:
        Omega_l = 1 - Omega_m

    conf_content = f"""# Configuration file for cutsky (default: `cutsky.conf').
INPUT          = '{box_path}'
INPUT_FORMAT   = 0
COMMENT        = '#'
BOX_SIZE       = {boxsize}
OMEGA_M        = {Omega_m}
OMEGA_LAMBDA   = {Omega_l}
DE_EOS_W       = {w_DE_EOS}
FOOTPRINT_TRIM = '{footprint_path}'
GALACTIC_CAP   = ['{galactic_cap}']
NZ_FILE        = '{nz_path}'
ZMIN           = {zmin}
ZMAX           = {zmax}
RAND_SEED      = [42]
OUTPUT         = ['{lc_out_path}']
"""

    if write_to:
        outp = Path(write_to)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(conf_content, encoding="utf-8")
        print(f"[write] -> {write_to}")

    return conf_content


if __name__ == "__main__":
    raise SystemExit(
        "This module no longer provides a CLI. Use cutsky_cfg() programmatically."
    )

"""
Shell script to call the external `cutsky` binary.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["cutsky_script"]


LSSLAB_ROOT = Path(__file__).resolve().parents[4]


def cutsky_script(
    workdir: Path | str,
    box_path: Path | str,
    boxL: float = 2000.0,
    footprint: Path | str = "/global/homes/s/siyizhao/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply",
    galactic_cap: str = "N",
    nz_path: Path | str = LSSLAB_ROOT / "examples/data/example_nz.txt",
    zmin: float = 0.4,
    zmax: float = 0.6,
    suffix: str = "",
    rewrite_cat: bool = True,
    prep_exe: Path | str | None = None,
    write_to: Path | str | None = None,
    make_executable: bool = False,
) -> str:
    """
    Return the shell script content to call `cutsky` with the given config.

    If `write_to` is provided, the script is also written to that path.

    Parameters
    ----------
    workdir : str or Path
        Working directory for cutsky operations (created if missing).
    box_path : str or Path
        Path to the input simulation box catalog (e.g., ASCII or h5).
    boxL : float, optional
        Size of the simulation box in Mpc/h. Default: 2000.0.
    footprint : str or Path, optional
        Path to the footprint polygon file (PLY format). Default: DESI Y3 footprint.
    galactic_cap : str, optional
        Galactic cap to use: \"N\" (NGC) or \"S\" (SGC). Default: \"N\".
    nz_path : str or Path, optional
        Path to the n(z) file. Default: example file.
    zmin : float, optional
        Minimum redshift. Default: 0.4.
    zmax : float, optional
        Maximum redshift. Default: 0.6.
    rewrite_cat : bool, optional
        If True, add --rewrite_cat flag to prep_cutsky. Default: True.
    prep_exe : str or Path, optional
        Path to prep_cutsky.py executable. If None, defaults to
        ``${LSSLAB_ROOT}/scripts/prep_cutsky.py``.
    write_to : str or Path, optional
        If provided, write the script to this file. Default: None.
    make_executable : bool, optional
        If True, add execute permissions to the output file. Default: False.

    Returns
    -------
    str
        The shell script content (always returned).

    Examples
    --------
    >>> from lsslab.mock.cutsky import cutsky_script
    >>> script = cutsky_script(
    ...     workdir=\"outputs\",
    ...     box_path=\"box.dat.h5\",
    ...     boxL=6000.0,
    ...     galactic_cap=\"N\",
    ...     nz_path=\"nz_N.txt\",
    ...     zmin=0.8,
    ...     zmax=3.5,
    ...     write_to=\"run_cutsky.sh\",
    ...     make_executable=True,
    ... )
    """

    prep_exe = prep_exe or (LSSLAB_ROOT / "scripts" / "prep_cutsky.py")
    rewrite_flag = " --rewrite_cat" if rewrite_cat else ""

    scripts = f"""#!/bin/bash
set -euo pipefail

source ~/envs/lsslab_extra/bin/activate
PREP_EXE={prep_exe}

workdir={workdir}
footprint={footprint}
GC={galactic_cap}
nz={nz_path}
zmin={zmin}
zmax={zmax}
suffix={suffix}
cat={box_path}
boxL={boxL}

mkdir -p $workdir
python $PREP_EXE --catalog_path $cat --boxsize $boxL{rewrite_flag} --workdir $workdir --footprint $footprint --galactic_cap $GC --nz_path $nz --zmin $zmin --zmax $zmax --suffix $suffix
echo "\nRunning cutsky..."
~/lib/cutsky/CUTSKY -c $workdir/cutsky_${{GC}}_${{zmin}}_${{zmax}}_${{suffix}}.conf > $workdir/cutsky_${{GC}}_${{zmin}}_${{zmax}}_${{suffix}}.log 2>&1
echo "Done."
"""
    if write_to is not None:
        outp = Path(write_to)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(scripts, encoding="utf-8")
        print(f"[write] -> {write_to}")
        if make_executable:
            outp.chmod(outp.stat().st_mode | 0o111)
            print(f"[chmod] Made {write_to} executable")

    return scripts

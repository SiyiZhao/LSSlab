"""
Shell script helpers for cutsky generation and post-processing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .normalize import resolve_workdir_path

__all__ = ["cutsky_script", "translate_script", "write_job_list"]


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
    suffix: str | None = None,
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
        If True, run script to prepare the format of input cubic mock catalog. Default: True.
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
    prep_setup = f"PREP_EXE={prep_exe}\n" if rewrite_cat else ""
    prep_run = (
        "python $PREP_EXE --catalog_path $mock_path --boxsize $boxL"
        " --workdir $workdir --zmin $zmin --zmax $zmax\n"
        if rewrite_cat
        else ""
    )
    suffix_setup = f"suffix={suffix}\n" if suffix is not None else ""
    suffix = f"_{suffix}" if suffix is not None else ""

    scripts = f"""#!/bin/bash
set -euo pipefail

source ~/envs/lsslab_extra/bin/activate
{prep_setup}

workdir={workdir}
footprint={footprint}
GC={galactic_cap}
nz={nz_path}
zmin={zmin}
zmax={zmax}
{suffix_setup}
mock_path={box_path}
boxL={boxL}

mkdir -p $workdir
{prep_run}echo "\nRunning cutsky..."
~/lib/cutsky/CUTSKY -c $workdir/cutsky_${{GC}}_${{zmin}}_${{zmax}}{suffix}.conf > $workdir/cutsky_${{GC}}_${{zmin}}_${{zmax}}{suffix}.log 2>&1
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


def translate_script(
    workdir: Path | str,
    data_dir: Path | str | None = None,
    random_dir: Path | str | None = None,
    tracer: str = "QSO",
    GC: str = "NS",
    output: Path | str | None = None,
    output_dir: Path | str | None = None,
    with_randoms: bool = False,
    randoms_only: bool = False,
    translate_exe: Path | str | None = None,
    write_to: Path | str | None = None,
    make_executable: bool = False,
) -> str:
    """
    Return the shell script content to post-process cutsky outputs.

    The generated script calls ``scripts/post_cutsky.py`` to merge raw
    cutsky ASCII files and convert them to the final catalog format.
    """

    workdir = Path(workdir).expanduser().resolve()
    translate_exe = translate_exe or (LSSLAB_ROOT / "scripts" / "post_cutsky.py")
    data_dir = resolve_workdir_path(workdir, data_dir, kind="data")
    random_dir = resolve_workdir_path(workdir, random_dir, kind="random")

    output_arg = f" --output {output}" if output is not None else ""
    output_dir_arg = f" --output-dir {output_dir}" if output_dir is not None else ""
    with_randoms_flag = " --with-randoms" if with_randoms else ""

    commands: list[str] = []
    if not randoms_only:
        commands.append(
            "python $TRANSLATE_EXE"
            f" --workdir {workdir}"
            f" --tracer {tracer}"
            f" --GC {GC}"
            f"{output_arg}"
            f"{output_dir_arg}"
            f" --data-dir {data_dir}"
            f" --random-dir {random_dir}"
                f"{with_randoms_flag}"
        )

    if randoms_only:
        commands.append(
            "python $TRANSLATE_EXE"
            f" --workdir {workdir}"
            f" --tracer {tracer}"
            f" --GC {GC}"
            f"{output_dir_arg}"
            f" --data-dir {data_dir}"
            f" --random-dir {random_dir}"
            " --randoms-only"
        )

    scripts = f"""#!/bin/bash
set -euo pipefail

source ~/envs/lsslab_extra/bin/activate
TRANSLATE_EXE={translate_exe}

{chr(10).join(commands)}
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


def write_job_list(
    scripts: Sequence[Path | str],
    output_path: Path | str,
    *,
    make_executable: bool = False,
) -> Path:
    """
    Write a jobs file compatible with ``jobfork_omp``.

    Each line has the format ``bash <script_path>``.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    normalized = [Path(script) for script in scripts]
    with output_path.open("w", encoding="utf-8") as handle:
        for script in normalized:
            handle.write(f"bash {script}\n")

    print(f"[write] job list -> {output_path}")
    print(
        "[guide] run `export OMP_NUM_THREADS="
        f"{len(normalized)}; ~/lib/jobfork/jobfork_omp {output_path} > {output_path}.log 2>&1` "
        "to execute the jobs"
    )

    if make_executable:
        output_path.chmod(output_path.stat().st_mode | 0o111)

    return output_path

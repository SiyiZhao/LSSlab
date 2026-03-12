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
    galactic_cap: str = "N",
    nz_path: Path | str = LSSLAB_ROOT / "examples/data/example_nz.txt",
    zmin: float = 0.405,
    zmax: float = 0.6,
    write_to: Path | str | None = None,
    make_executable: bool = False,
) -> str:
    """
    Return the shell script content to call `cutsky` with the given config. If `write_to` is provided, the script is also written to that path.

    Parameters
    ----------
    """

    scripts = f"""#!/bin/bash
set -euo pipefail

source ~/envs/lsslab_extra/bin/activate
cd {LSSLAB_ROOT}/scripts

workdir={workdir}
GC={galactic_cap}
nz={nz_path}
zmin={zmin}
zmax={zmax}
cat={box_path}

mkdir -p $workdir
python prep_cutsky.py --catalog_path $cat --rewrite_cat --workdir $workdir --galactic_cap $GC --nz_path $nz --zmin $zmin --zmax $zmax
echo "\nRunning cutsky..."
~/lib/cutsky/CUTSKY -c $workdir/cutsky_${{GC}}_${{zmin}}_${{zmax}}.conf > $workdir/cutsky_${{GC}}_${{zmin}}_${{zmax}}.log 2>&1
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

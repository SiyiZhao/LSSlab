"""
Generate runnable shell scripts that invoke prep_cutsky + cutsky.

These utilities only write scripts; they do not execute cutsky.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .script import cutsky_script
from .random import write_random_catalog

__all__ = ["CutskyRunner"]


class CutskyRunner:
    """
    Generate cutsky runner scripts with shared defaults.

    Pass a single case or a list of cases; each case must include `box_path`,
    `galactic_cap`, `zmin`, and `zmax`. Optionally override `nz_path`,
    `footprint_path`, `workdir`, `boxL`, and output script name per case. For
    `galactic_cap`, you may pass a single value ("N" or "S"), "NS"/"SN", or a
    list/tuple of caps, and the runner will emit one script per cap.
    """

    def __init__(
        self,
        *,
        workdir: Path,
        footprint_path: Path,
        nz_path: Path | Mapping[str, Path],
        boxL: float,
        nz_path_random: Path | Mapping[str, Path] | None = None,
        boxL_random: float | None = None,
    ) -> None:
        self.workdir = workdir
        self.footprint_path = footprint_path
        self.nz_path = nz_path
        self.boxL = boxL
        self.nz_path_random = nz_path_random or nz_path
        self.boxL_random = boxL_random or boxL

    def _normalize_cases(
        self, cases: Sequence[Mapping[str, Any]] | Mapping[str, Any]
    ) -> list[Mapping[str, Any]]:
        if isinstance(cases, Mapping):
            return [cases]
        return list(cases)

    def generate_data(
        self,
        cases: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        *,
        make_executable: bool = True,
        rewrite_cat: bool = True,
        prep_exe: Path | str | None = None,
    ) -> list[Path]:
        """
        Write runner scripts for data catalogs; return script paths.
        """
        
        wd = self.workdir
        wd.mkdir(parents=True, exist_ok=True)
        caps = self.nz_path.keys()
        
        scripts: list[Path] = []
        for case in self._normalize_cases(cases):
            box_path = Path(case["box_path"])
            zmin = case["zmin"]
            zmax = case["zmax"]
            
            for cap in caps:
                script_name = case.get("script_name", f"run_cutsky_{cap}_{zmin}_{zmax}.sh")
                script_path = wd / script_name

                cutsky_script(
                    workdir=wd,
                    box_path=box_path,
                    boxL=self.boxL,
                    footprint=self.footprint_path,
                    galactic_cap=cap,
                    nz_path=self.nz_path[cap],
                    zmin=zmin,
                    zmax=zmax,
                    rewrite_cat=rewrite_cat,
                    prep_exe=prep_exe,
                    write_to=script_path,
                    make_executable=make_executable,
                )

                scripts.append(script_path)

        return scripts


    # === Random catalog related methods ===

    def generate_random(
        self,
        cases: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        *,
        make_executable: bool = True,
        rewrite_cat: bool = False,
        nz_path: Path | str | None = None,
        prep_exe: Path | str | None = None,
    ) -> list[Path]:
        """Write runner scripts for random catalogs; return script paths.
        """
        
        nz_path = nz_path or self.nz_path_random
        wd = self.workdir / "RANDOM"
        wd.mkdir(parents=True, exist_ok=True)
        caps = nz_path.keys()
        
        scripts: list[Path] = []
        for case in self._normalize_cases(cases):
            box_path = Path(case["box_path"])
            zmin = case["zmin"]
            zmax = case["zmax"]
            
            for cap in caps:
                script_name = case.get("script_name", f"run_cutsky_{cap}_{zmin}_{zmax}.sh")
                script_path = wd / script_name

                cutsky_script(
                    workdir=wd,
                    box_path=box_path,
                    boxL=self.boxL_random,
                    footprint=self.footprint_path,
                    galactic_cap=cap,
                    nz_path=nz_path[cap],
                    zmin=zmin,
                    zmax=zmax,
                    rewrite_cat=rewrite_cat,
                    prep_exe=prep_exe,
                    write_to=script_path,
                    make_executable=make_executable,
                )

                scripts.append(script_path)

        return scripts


    def prepare_random_box(
        self,
        *,
        num: int,
        seed: int,
        boxL_random: float | None = None,
    ) -> list[Path]:
        # raise NotImplementedError("This method is totally independent with the pipeline except the path to the random box. We have not implemented it in the pipeline.")

        odir = self.workdir / "RANDOM"
        odir.mkdir(parents=True, exist_ok=True)
        boxL_random = boxL_random or self.boxL_random
        num = int(num)
        num_formatted = f"{num:.1e}".replace('e+0', 'e').replace('e-0', 'e-')
        ofile=odir / f"random_boxL{int(boxL_random)}_N{num_formatted}_seed{seed}.dat"
        if ofile.exists():
            print(f"Random box file {ofile} already exists; skipping generation.")
            return ofile
        
        box_path = write_random_catalog(
            ofile=ofile,
            num=num,
            boxL=boxL_random,
            seed=seed,
        )
        self.boxL_random = boxL_random
        
        return box_path

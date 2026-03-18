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
    Creates shell scripts for running cutsky on both data and random catalogs.
    Supports multiple galactic caps with separate n(z) files per cap.

    Attributes
    ----------
    workdir : Path
        Base working directory for all generated scripts and outputs.
    footprint_path : Path
        Path to the footprint polygon file (PLY format).
    nz_path : Mapping[str, Path]
        Mapping of galactic caps to n(z) file paths (e.g., {"N": path_n, "S": path_s}).
        Caps are inferred from keys.
    boxL : float
        Default box size in Mpc/h for data catalogs.
    nz_path_random : Mapping[str, Path], optional
        Separate n(z) paths for random catalogs; defaults to nz_path.
    boxL_random : float, optional
        Separate box size for random catalogs; defaults to boxL.
    """

    def __init__(
        self,
        *,
        workdir: Path,
        footprint_path: Path,
        nz_path: Mapping[str, Path],
        boxL: float,
        nz_path_random: Mapping[str, Path] | None = None,
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

        Parameters
        ----------
        cases : dict or list of dict
            Each case dict must contain:
            - ``box_path`` (str): Path to the input catalog.
            - ``zmin`` (float): Minimum redshift.
            - ``zmax`` (float): Maximum redshift.
            Optional:
            - ``script_name`` (str): Custom script filename; defaults to
              f"run_cutsky_{cap}_{zmin}_{zmax}.sh" per cap.
        make_executable : bool, optional
            If True, add execute permissions to generated scripts. Default: True.
        rewrite_cat : bool, optional
            If True, call prep_cutsky with --rewrite_cat flag. Default: True.
        prep_exe : Path or str, optional
            Path to prep_cutsky.py executable; defaults to ``scripts/prep_cutsky.py``.

        Returns
        -------
        list[Path]
            Paths to all generated shell scripts (one per case per cap).
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
        """
        Write runner scripts for random catalogs; return script paths.

        Similar to :meth:`generate_data`, but uses random box files and defaults to
        nz_path_random and boxL_random. Scripts are written under ``workdir/RANDOM``.

        Parameters
        ----------
        cases : dict or list of dict
            Same structure as :meth:`generate_data`.
        make_executable : bool, optional
            If True, add execute permissions. Default: True.
        rewrite_cat : bool, optional
            If True, rewrite random box format. Default: False.
        nz_path : Path or str, optional
            Override the runner's nz_path_random; defaults to runner setting.
        prep_exe : Path or str, optional
            Path to prep_cutsky.py; defaults to ``scripts/prep_cutsky.py``.

        Returns
        -------
        list[Path]
            Paths to generated random catalog scripts.
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
    ) -> Path:
        """
        Generate a uniform random box catalog.

        Creates a file with uniformly distributed random points in a cubic box
        of size boxL_random. The file is stored under ``workdir/RANDOM`` with a
        filename encoding the box size, point count, and seed.

        Parameters
        ----------
        num : int
            Number of random points to generate.
        seed : int
            Random seed for reproducibility.
        boxL_random : float, optional
            Box size; defaults to runner's boxL_random.

        Returns
        -------
        Path
            Path to the generated random box file.
            If the file already exists, it is not regenerated.

        Examples
        --------
        >>> box_path = runner.prepare_random_box(num=int(3e8), seed=42)
        >>> print(box_path)
        outputs/RANDOM/random_boxL6000_N3e8_seed42.dat
        """

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

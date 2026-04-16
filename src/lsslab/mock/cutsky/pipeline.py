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
        Optional override for random-catalog n(z) paths; defaults to nz_path.
        In most workflows this should be left unset so data and random use the
        same n(z), while higher random counts are obtained by generating
        multiple random realizations with different seeds.
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
        box_paths: Sequence[Path] | Path,
        make_executable: bool = True,
        rewrite_cat: bool = False,
        nz_path: Mapping[str, Path] | None = None,
        prep_exe: Path | str | None = None,
    ) -> list[Path]:
        """
        Write runner scripts for random catalogs; return script paths.

        Similar to :meth:`generate_data`, but uses random box files and defaults to
        nz_path_random and boxL_random. Scripts are written under ``workdir/RANDOM``.

        Parameters
        ----------
        cases : dict or list of dict
            Same structure as :meth:`generate_data`, except ``box_path`` is not
            included here and is supplied separately via ``box_paths``.
        box_paths : Path or sequence of Path
            One or more random box catalogs to turn into random lightcones.
            The index in this sequence is used as the default realization id in
            generated filenames.
        make_executable : bool, optional
            If True, add execute permissions. Default: True.
        rewrite_cat : bool, optional
            If True, rewrite random box format. Default: False.
        nz_path : Mapping[str, Path], optional
            Override the runner's random-catalog n(z) paths; defaults to the
            runner setting. In most workflows this should match the data n(z),
            and larger total random counts should come from multiple seeds
            rather than a rescaled n(z).
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
        if isinstance(box_paths, Path):
            normalized_box_paths = [box_paths]
        else:
            normalized_box_paths = [Path(box_path) for box_path in box_paths]
        
        scripts: list[Path] = []
        for case in self._normalize_cases(cases):
            zmin = case["zmin"]
            zmax = case["zmax"]
            for case_id, box_path in enumerate(normalized_box_paths):
                for cap in caps:
                    script_name = case.get(
                        "script_name",
                        f"run_cutsky_ran{case_id}_{cap}_{zmin}_{zmax}.sh",
                    )
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


    def prepare_random_boxes(
        self,
        *,
        num: int,
        seed: int,
        nran: int = 1,
        boxL_random: float | None = None,
    ) -> list[Path]:
        """
        Generate one or more uniform random box catalogs.

        Creates ``nran`` files with uniformly distributed random points in a cubic
        box of size ``boxL_random``. The files are stored under ``workdir/RANDOM``
        with filenames encoding the box size, point count, and seed.

        Parameters
        ----------
        num : int
            Number of random points to generate for each box.
        seed : int
            Starting random seed for reproducibility.
        nran : int, optional
            Number of random boxes to generate. Seeds are assigned as
            ``seed + i`` for ``i = 0, ..., nran - 1``. Default is 1.
        boxL_random : float, optional
            Box size; defaults to runner's boxL_random.

        Returns
        -------
        list[Path]
            Paths to the generated random box files. Existing files are reused
            and not regenerated.

        Examples
        --------
        >>> box_paths = runner.prepare_random_boxes(num=int(3e7), seed=42, nran=2)
        >>> print(box_paths[0])
        outputs/RANDOM/random_boxL6000_N3e7_seed42.dat
        """

        odir = self.workdir / "RANDOM"
        odir.mkdir(parents=True, exist_ok=True)
        boxL_random = boxL_random or self.boxL_random
        num = int(num)
        nran = int(nran)
        if nran < 1:
            raise ValueError("nran must be at least 1.")
        num_formatted = f"{num:.1e}".replace('e+0', 'e').replace('e-0', 'e-')

        self.boxL_random = boxL_random

        box_paths: list[Path] = []
        for offset in range(nran):
            current_seed = seed + offset
            ofile = odir / f"random_boxL{int(boxL_random)}_N{num_formatted}_seed{current_seed}.dat"
            if ofile.exists():
                print(f"Random box file {ofile} already exists; skipping generation.")
                box_paths.append(ofile)
                continue

            box_path = write_random_catalog(
                ofile=ofile,
                num=num,
                boxL=boxL_random,
                seed=current_seed,
            )
            box_paths.append(box_path)

        return box_paths

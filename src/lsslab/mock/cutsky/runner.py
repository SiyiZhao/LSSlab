"""Core orchestration for cutsky data and random box workflows."""

from __future__ import annotations

from pathlib import Path
import warnings

import numpy as np

from .config import cutsky_cfg
from .inputs import CutskyInputs, CubicMockInput, CubicRandomInput
from .normalize import normalize_region_path_mapping, resolve_workdir_path
from .script import cutsky_script, translate_script, write_job_list
from .nz import prepare_nz as prepare_nz_file
from .utils import validate_random_box_catalogs
from lsslab.tools.random_box import collect_random_box_summary

__all__ = [
    "CubicMockInput",
    "CubicRandomInput",
    "CutskyInputs",
    "CutskyRunner",
]


class CutskyRunner:
    """Generate shell scripts for cutsky data and random box workflows.
    
    Core functionality:
    - runner_for_mocks(): Generate .sh scripts for each mock catalog snapshot
    - runner_for_randoms(): Validate random boxes and generate .sh scripts for each realization
    """

    def __init__(self, *, workdir: Path, inputs: CutskyInputs) -> None:
        self.workdir = Path(workdir).expanduser().resolve()
        self.inputs = inputs
        self._prepared_data_nz_path: dict[str, Path] | None = None
        self._prepared_random_nz_path: dict[str, Path] | None = None

    @property
    def mock(self) -> CubicMockInput:
        return self.inputs.mock

    @property
    def random(self) -> CubicRandomInput:
        return self.inputs.random

    @property
    def footprint_path(self) -> Path:
        return self.inputs.footprint_path

    @property
    def nz_path(self) -> dict[str, Path]:
        return self.inputs.nz_path

    def prepare_nz(self) -> tuple[dict[str, Path], dict[str, Path]]:
        """Prepare cutsky-format n(z) files for data and random workflows.

        Always writes per-region data n(z) files with ``times=1``. If
        ``random_file_scale != 1``, it additionally writes per-region random n(z)
        files scaled by ``times=random_file_scale``.
        """

        nz_dir = resolve_workdir_path(self.workdir, kind="nz").expanduser().resolve()
        nz_dir.mkdir(parents=True, exist_ok=True)

        data_mapping: dict[str, Path] = {}
        random_mapping: dict[str, Path] = {}
        scale = float(self.random.random_file_scale)

        for region, source in self.nz_path.items():
            region_upper = str(region).upper()
            source_path = Path(source).expanduser().resolve()
            data_dest = (nz_dir / f"nz_{region_upper}.txt").expanduser().resolve()
            prepare_nz_file(source_path, data_dest, times=1.0)
            data_mapping[region_upper] = data_dest

            if scale != 1.0:
                random_dest = (nz_dir / f"nz_{region_upper}_x{scale:g}.txt").expanduser().resolve()
                prepare_nz_file(source_path, random_dest, times=scale)
                random_mapping[region_upper] = random_dest
            else:
                random_mapping[region_upper] = data_dest

        # Update default mapping to prepared data n(z) for downstream calls.
        self.inputs.nz_path.clear()
        self.inputs.nz_path.update(data_mapping)
        self._prepared_data_nz_path = dict(data_mapping)
        self._prepared_random_nz_path = dict(random_mapping)

        return data_mapping, random_mapping

    def _compute_nbar_threshold(
        self,
        *,
        zmin: float,
        zmax: float,
        margin: float = 1.1,
    ) -> float:
        """Compute density threshold from data n(z) files.

        Reads ``self._prepared_data_nz_path`` if available, otherwise falls back
        to ``self.nz_path``. The expected n(z) file format is fixed: column 1 is
        redshift and column 2 is n(z).
        Returns ``margin * max(n(z))`` over ``[zmin, zmax]`` across all caps.
        """
        mapping = self._prepared_data_nz_path or self.nz_path
        if not mapping:
            raise ValueError("data n(z) mapping is empty.")
        maxima: list[float] = []
        for path in mapping.values():
            data = np.loadtxt(path)
            values = np.atleast_2d(data)
            if values.shape[1] < 2:
                raise ValueError(
                    f"n(z) file {path} must have at least 2 columns: redshift and n(z)."
                )
            redshift = values[:, 0]
            nz_values = values[:, 1]
            mask = (redshift >= zmin) & (redshift <= zmax)
            if not np.any(mask):
                raise ValueError(
                    f"n(z) file {path} has no samples inside z-range [{zmin}, {zmax}]."
                )
            maxima.append(float(np.max(nz_values[mask])))
        return max(maxima) * float(margin)

    def runner_for_mock(
        self,
        *,
        make_executable: bool = False,
        rewrite_cat: bool = True,
        prep_exe: Path | str | None = None,
        nz_path: dict[str, Path] | None = None,
    ) -> tuple[list[Path], Path | None]:
        """Generate .sh scripts for each mock catalog snapshot.
        
        For each (box_path, zmin, zmax) case and each galactic cap, generates
        a cutsky runner script. If multiple scripts are generated, also creates
        a jobs.sh file listing all scripts.
        
        Parameters
        ----------
        make_executable : bool
            Whether to make generated .sh scripts executable.
        rewrite_cat : bool
            Whether to rewrite the cutsky catalog (passed to cutsky_script).
        prep_exe : Path | str | None
            Path to the prep executable if needed.
        
        Returns
        -------
        scripts : list[Path]
            List of generated .sh script paths.
        jobs_path : Path | None
            Path to the jobs.sh file if multiple scripts were generated, else None.
        """
        wd = resolve_workdir_path(self.workdir, kind="data")
        wd.mkdir(parents=True, exist_ok=True)

        mapping = nz_path or self._prepared_data_nz_path or self.nz_path

        scripts: list[Path] = []
        for box_path, zmin, zmax, script_name in self.mock.iter_cases():
            # When prep_cutsky rewrites the catalog, subsequent cutsky configs/scripts
            # should point to the rewritten DATA catalog path.
            effective_box_path = (
                (wd / f"box_{zmin}_{zmax}.dat").expanduser().resolve()
                if rewrite_cat
                else Path(box_path).expanduser().resolve()
            )
            for cap, nz_file in mapping.items():
                script_filename = script_name or f"run_{cap}_{zmin}_{zmax}.sh"
                script_path = (wd / script_filename).expanduser().resolve()
                conf_path = (wd / f"cutsky_{cap}_{zmin}_{zmax}.conf").expanduser().resolve()
                out_path = (wd / f"cutsky_{cap}_{zmin}_{zmax}.dat").expanduser().resolve()
                cap_nz_file = Path(nz_file).expanduser().resolve()

                cutsky_cfg(
                    box_path=str(effective_box_path),
                    boxsize=self.mock.boxL,
                    lc_out_path=str(out_path),
                    footprint_path=str(self.footprint_path),
                    galactic_cap=cap,
                    nz_path=str(cap_nz_file),
                    zmin=zmin,
                    zmax=zmax,
                    write_to=str(conf_path),
                )
                
                cutsky_script(
                    workdir=wd,
                    box_path=effective_box_path,
                    boxL=self.mock.boxL,
                    footprint=self.footprint_path,
                    galactic_cap=cap,
                    nz_path=cap_nz_file,
                    zmin=zmin,
                    zmax=zmax,
                    rewrite_cat=rewrite_cat,
                    prep_exe=prep_exe,
                    write_to=script_path,
                    make_executable=make_executable,
                )
                scripts.append(script_path)

        # Generate jobs.sh if multiple scripts
        jobs_path = None
        if len(scripts) > 1:
            jobs_path = write_job_list(scripts, (wd / "jobs.sh").expanduser().resolve(), make_executable=False)

        return scripts, jobs_path

    def runner_for_random(
        self,
        *,
        make_executable: bool = False,
        nz_path: dict[str, Path] | None = None,
    ) -> tuple[list[Path], list[Path], Path | None]:
        """Validate random box catalogs and generate .sh scripts for each realization.
        
        First validates that the configured random box parameters (boxL, target_num)
        have sufficient catalogs using two checks:
        1. Density check: target_density > 1.1 * max(n(z))
        2. File count check: available files >= nfiles required
        
        If validation passes, generates .sh scripts for each selected random box
        realization. If multiple scripts are generated, also creates a jobs.sh file.
        
        Parameters
        ----------
        make_executable : bool
            Whether to make generated .sh scripts executable.
        
        Returns
        -------
        selected_boxes : list[Path]
            List of selected random box catalog paths.
        scripts : list[Path]
            List of generated .sh script paths.
        jobs_path : Path | None
            Path to the jobs.sh file if multiple scripts were generated, else None.
        
        Raises
        ------
        ValueError
            If density or file count validation fails.
        """
        input_random_dir = self.random.random_dir
        output_random_dir = resolve_workdir_path(self.workdir, kind="random").expanduser().resolve()
        output_random_dir.mkdir(parents=True, exist_ok=True)

        # Collect available random boxes in the directory
        summary = collect_random_box_summary(input_random_dir)

        mapping = nz_path or self._prepared_random_nz_path or self.nz_path
        mapping = normalize_region_path_mapping(
            mapping,
            field_name="random nz_path",
            allow_empty=True,
        )

        if not isinstance(self.random.nsample, dict) and {"N", "S"}.issubset(set(mapping)):
            warnings.warn(
                "using same random boxes for NGC and SGC, diff seed not implenmented",
                RuntimeWarning,
                stacklevel=2,
            )

        zmin, zmax = self.random.zmin, self.random.zmax
        target_boxsize = float(self.random.boxL)
        failed_checks: list[str] = []
        selected_boxes: list[Path] = []
        required_density = self._compute_nbar_threshold(
            zmin=zmin,
            zmax=zmax,
            margin=1.1,
        )

        # Generate scripts for each selected random box using random z-range.
        scripts: list[Path] = []
        for cap, nz_file in mapping.items():
            if self.random.nsample is None:
                raise ValueError("nsample is not set.")
            if isinstance(self.random.nsample, dict):
                if cap not in self.random.nsample:
                    raise ValueError(f"Missing nsample for region {cap}.")
                target_num = int(self.random.nsample[cap])
            else:
                target_num = int(self.random.nsample)

            validation = validate_random_box_catalogs(
                summary=summary,
                cap=cap,
                boxL=target_boxsize,
                target_num=target_num,
                density_threshold=required_density,
                nfiles_required=self.random.nfiles,
            )

            if validation.failed_checks:
                failed_checks.extend(validation.failed_checks)
                continue

            selected_cap_boxes = [Path(info.path).expanduser().resolve() for info in validation.selected_infos]
            selected_cap_seeds = [info.seed for info in validation.selected_infos]
            selected_boxes.extend(selected_cap_boxes)

            print(
                f"Selected {len(selected_cap_boxes)} random box files for {cap} realization generation. "
                f"boxL={target_boxsize:g}, nsample={target_num}, seeds={selected_cap_seeds}"
            )

            for real_id, box_path in enumerate(selected_cap_boxes):
                suffix = f"ran{real_id}"
                conf_path = (output_random_dir / f"cutsky_{cap}_{zmin}_{zmax}_{suffix}.conf").expanduser().resolve()
                out_path = (output_random_dir / f"cutsky_{cap}_{zmin}_{zmax}_{suffix}.dat").expanduser().resolve()
                script_path = (output_random_dir / f"run_{suffix}_{cap}_{zmin}_{zmax}.sh").expanduser().resolve()

                cutsky_cfg(
                    box_path=str(box_path),
                    boxsize=self.random.boxL,
                    lc_out_path=str(out_path),
                    footprint_path=str(self.footprint_path),
                    galactic_cap=cap,
                    nz_path=str(nz_file),
                    zmin=zmin,
                    zmax=zmax,
                    write_to=str(conf_path),
                )

                cutsky_script(
                    workdir=output_random_dir,
                    box_path=box_path,
                    boxL=self.random.boxL,
                    footprint=self.footprint_path,
                    galactic_cap=cap,
                    nz_path=nz_file,
                    zmin=zmin,
                    zmax=zmax,
                    suffix=suffix,
                    rewrite_cat=False,
                    write_to=script_path,
                    make_executable=make_executable,
                )
                scripts.append(script_path)

        if failed_checks:
            print(summary)
            details = "\n".join(f"  - {item}" for item in failed_checks)
            raise ValueError(
                f"Random box validation failed for boxsize={target_boxsize}:\n"
                f"  z-range = [{zmin}, {zmax}]\n"
                f"{details}"
            )

        # Generate jobs.sh if multiple scripts
        jobs_path = None
        if len(scripts) > 1:
            jobs_path = write_job_list(
                scripts,
                (output_random_dir / "jobs.sh").expanduser().resolve(),
                make_executable=False,
            )

        return selected_boxes, scripts, jobs_path

    def generate_translation(
        self,
        *,
        tracer: str = "QSO",
        GC: str = "NS",
        output: Path | str | None = None,
        output_dir: Path | str | None = None,
        with_randoms: bool = True,
        randoms_only: bool = False,
        translate_exe: Path | str | None = None,
        script_name: str = "run_translate_lcmock.sh",
        make_executable: bool = False,
    ) -> Path:
        """Generate the shell script that runs translate_lcmock after cutsky finishes."""

        wd = self.workdir.expanduser().resolve()
        wd.mkdir(parents=True, exist_ok=True)
        script_path = (wd / script_name).expanduser().resolve()

        translate_script(
            workdir=wd,
            data_dir=resolve_workdir_path(self.workdir, kind="data"),
            random_dir=resolve_workdir_path(self.workdir, kind="random"),
            tracer=tracer,
            GC=GC,
            output=output,
            output_dir=output_dir,
            with_randoms=with_randoms,
            randoms_only=randoms_only,
            translate_exe=translate_exe,
            write_to=script_path,
            make_executable=make_executable,
        )
        return script_path

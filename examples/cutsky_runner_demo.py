from __future__ import annotations

from pathlib import Path

from lsslab.mock.cutsky import (
    CutskyInputs,
    CutskyRunner,
    CubicMockInput,
    CubicRandomInput,
)


def set_zbins(tracer: str) -> tuple[dict[str, tuple[float, float]], float, float]:
    """Return redshift bins and global z-range for the selected tracer."""
    if tracer == "LRG":
        zbins = {
            "0p500": (0.4, 0.6),
            "0p725": (0.6, 0.8),
            "0p950": (0.8, 1.1),
        }
        return zbins, 0.4, 1.1
    raise NotImplementedError(f"Unsupported tracer: {tracer}")


def main() -> None:
    """Build inputs and generate DATA/RANDOM cutsky scripts for the demo."""
    tracer = "LRG"
    workdir = Path(__file__).parent / "data" / f"demo_cutsky_runner_{tracer}"
    workdir.mkdir(parents=True, exist_ok=True)

    # cutsky settings
    footprint = Path("~/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply").expanduser()
    # Region-specific differences are defined here only.
    nz_source = {
        "N": Path(f"/global/cfs/cdirs/desi/survey/catalogs/DA2/LSS/loa-v1/LSScats/v2/PIP/{tracer}_NGC_nz.txt"),
        "S": Path(f"/global/cfs/cdirs/desi/survey/catalogs/DA2/LSS/loa-v1/LSScats/v2/PIP/{tracer}_SGC_nz.txt")
    }
    random_n = {"N": int(2.3e8), "S": int(1.5e8)}

    # mock settings
    mock_dir = Path(
        f"/pscratch/sd/s/siyizhao/desi-dr2-hod/loa-v2_HODv4/"
        f"mocks_base-A/Abacus_pngbase_c302_ph000/{tracer}"
    )
    file_name = f"{tracer}_hodMAP_realspace_clustering.dat.h5"
    zbins, zmin_all, zmax_all = set_zbins(tracer)
    input_mock = CubicMockInput(
        boxL=2000.0,
        box_path=[mock_dir / tag / file_name for tag in zbins],
        zmin=[zmin for zmin, _ in zbins.values()],
        zmax=[zmax for _, zmax in zbins.values()],
    )
    
    # random settings
    input_random = CubicRandomInput(
        random_dir=Path("/pscratch/sd/s/siyizhao/random_boxes"),
        boxL=6000.0,
        nsample=random_n,
        nfiles=10, # number of random files to generate per region
        random_file_scale=1,
        zmin=zmin_all,
        zmax=zmax_all,
    )

    ###################### RUNNER DEMO ######################
    runner = CutskyRunner(
        workdir=workdir,
        inputs=CutskyInputs(
            mock=input_mock,
            random=input_random,
            footprint_path=footprint,
            nz_path=nz_source,
        ),
    )
    runner.prepare_nz()
    runner.runner_for_mock()
    runner.runner_for_random()


if __name__ == "__main__":
    main()

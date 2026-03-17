from pathlib import Path

from lsslab.mock.cutsky import CutskyRunner


def main() -> None:
    here = Path(__file__).parent
    workdir = here / "data" / "demo_CutskyRunner"

    runner = CutskyRunner(
        workdir=workdir,
        footprint_path=Path("~/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply").expanduser(),
        nz_path=here / "data" / "example_nz.txt",
        boxL=2000.0,
    )
    mock_dir = Path("/pscratch/sd/s/siyizhao/desi-dr2-hod/loa-v2_HODv4/mocks_base-A/Abacus_pngbase_c302_ph000/QSO")
    file_name = "QSO_hodMAP_realspace_clustering.dat.h5"
    cases = [
        {
            "box_path": mock_dir / "0p950" / file_name,
            "galactic_cap": "N",
            "zmin": 0.8,
            "zmax": 1.1,
        },
        {
            "box_path": mock_dir / "1p250" / file_name,
            "galactic_cap": ["N", "S"],
            "zmin": 1.1,
            "zmax": 1.4,
        },
    ]

    scripts = runner.generate(cases)


if __name__ == "__main__":
    main()

from pathlib import Path

from lsslab.mock.cutsky import CutskyRunner


def main() -> None:
    here = Path(__file__).parent
    workdir = here / "data" / "demo_CutskyRunner"

    runner = CutskyRunner(
        workdir=workdir,
        footprint_path=Path("~/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply").expanduser(),
        nz_path={"N": workdir / "QSO_NGC_nz.txt", "S": workdir / "QSO_SGC_nz.txt"},
        boxL=2000.0,
        boxL_random=6000.0,
    )
    
    # generate scripts to run cutsky for realspace mocks
    mock_dir = Path("/pscratch/sd/s/siyizhao/desi-dr2-hod/loa-v2_HODv4/mocks_base-A/Abacus_pngbase_c302_ph000/QSO")
    file_name = "QSO_hodMAP_realspace_clustering.dat.h5"
    cases = [
        {
            "box_path": mock_dir / "0p950" / file_name,
            "zmin": 0.8,
            "zmax": 1.1,
        },
        {
            "box_path": mock_dir / "1p250" / file_name,
            "zmin": 1.1,
            "zmax": 1.4,
        },
    ]
    runner.generate_data(cases)
    
    # generate scripts to run cutsky for random catalogs
    # keep the same n(z) as data, and increase the total random count via nran
    random_cases = [
        {
            "zmin": 0.8,
            "zmax": 3.5,
        },
    ]
    box_paths = runner.prepare_random_boxes(num=3.1e8, seed=4242, nran=2)
    runner.generate_random(
        random_cases,
        box_paths=box_paths,
        nz_path={"N": workdir / "QSO_NGC_nz.txt"},
    )
    
    box_paths = runner.prepare_random_boxes(num=2.4e8, seed=34242, nran=2)
    runner.generate_random(
        random_cases,
        box_paths=box_paths,
        nz_path={"S": workdir / "QSO_SGC_nz.txt"},
    )
    

if __name__ == "__main__":
    main()

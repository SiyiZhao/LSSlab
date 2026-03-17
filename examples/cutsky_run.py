from pathlib import Path

from lsslab.mock.cutsky import cutsky_script


def main() -> None:
    here = Path(__file__).parent
    workdir = here / "data" / "demo_cutsky"
    script_path = workdir / "run_cutsky_demo.sh"

    script_body = cutsky_script(
        workdir=workdir,
        box_path="/pscratch/sd/s/siyizhao/desi-dr2-hod/loa-v2_HODv4/mocks_base-A/Abacus_pngbase_c302_ph000/QSO/0p950/QSO_hodMAP_realspace_clustering.dat.h5",
        box_L=2000.0,
        footprint="/global/homes/s/siyizhao/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply",
        galactic_cap="N",
        nz_path=workdir / "example_nz.txt",
        zmin=0.8,
        zmax=1.1,
        write_to=script_path,
        make_executable=True,
    )

    print("\nPreview:\n")
    print(script_body)


if __name__ == "__main__":
    main()

from pathlib import Path

from lsslab.mock.cutsky import cutsky_cfg


def main() -> None:
    here = Path(__file__).parent
    config_path = here / "data" / "example_cutsky.conf"

    content = cutsky_cfg(
        box_path="/path/to/fort.301",
        boxsize=2000.0,
        lc_out_path=here / "data" / "lightcone.fits",
        footprint_path="/global/homes/s/siyizhao/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply",
        nz_path=str(here / "data" / "example_nz.txt"),
        galactic_cap="N",
        zmin=0.405,
        zmax=0.6,
        write_to=config_path,
    )
    print("\nThe content is:\n", content)


if __name__ == "__main__":
    main()

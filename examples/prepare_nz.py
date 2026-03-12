"""Minimal example: convert DESI-format n(z) to cutsky-ready format."""

from pathlib import Path

from lsslab.mock.cutsky import prepare_nz


def main() -> None:
    # Replace these with your actual paths
    source = Path("/global/cfs/cdirs/desi/survey/catalogs/DA2/LSS/loa-v1/LSScats/v2/PIP/QSO_NGC_nz.txt")
    here = Path(__file__).parent
    workdir = here / "data" / "demo_cutsky"

    dest = workdir / "example_nz.txt"
    prepare_nz(source, dest)

    # Optional scaling with `times`
    dest = workdir / "example_nz_times_10.txt"
    prepare_nz(source, dest, times=10)


if __name__ == "__main__":
    main()

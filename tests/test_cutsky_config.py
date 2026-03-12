from pathlib import Path

from lsslab.mock.cutsky import cutsky_cfg


def test_cutsky_cfg_writes_file_and_matches_content(tmp_path: Path) -> None:
    target = tmp_path / "cutsky.conf"
    content = cutsky_cfg(
        box_path="box.dat",
        boxsize=500.0,
        lc_out_path="lc.fits",
        Omega_m=0.3,
        Omega_l=None,
        w_DE_EOS=-0.9,
        footprint_path="footprint.ply",
        galactic_cap="B",
        nz_path="nz.txt",
        zmin=0.2,
        zmax=1.1,
        write_to=target,
    )

    assert target.exists()
    assert target.read_text() == content
    assert "OMEGA_LAMBDA   = 0.7" in content
    assert "GALACTIC_CAP   = ['B']" in content

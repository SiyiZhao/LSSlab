import numpy as np

from lsslab.mock.cutsky import prepare_nz


def test_prepare_nz_scales_and_extends(tmp_path):
    # Construct a minimal DESI-style n(z) table: zmid, zlow, zhigh, n(z), Nbin, Vol_bin
    data = np.array(
        [
            [0.10, 0.05, 0.15, 10.0, 0.0, 0.0],
            [0.20, 0.15, 0.25, 20.0, 0.0, 0.0],
        ]
    )
    source = tmp_path / "nz_input.txt"
    dest = tmp_path / "nz_output.txt"
    np.savetxt(source, data)

    prepare_nz(source, dest, times=2.0)

    out = np.loadtxt(dest)
    expected = np.array(
        [
            [0.05, 20.0],
            [0.10, 20.0],
            [0.20, 40.0],
            [0.25, 40.0],
        ]
    )

    assert np.allclose(out, expected)

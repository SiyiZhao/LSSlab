from __future__ import annotations

from lsslab.mock.cutsky.utils import read_cutsky_data, validate_random_box_catalogs
from lsslab.tools.random_box import collect_random_box_summary, random_box_filename


def test_read_cutsky_data_filters_requested_status(tmp_path) -> None:
    """read_cutsky_data should ignore commented headers and filter STATUS."""
    data_file = tmp_path / "cutsky_N_0.dat"
    data_file.write_text(
        "# RA(1) DEC(2) Z(3) Z_COSMO(4) NZ(5) STATUS(6) RAN_NUM_0_1(7)\n"
        "199.96126 44.432209 0.82320231 0.82326251 2.770452e-05 0 0.37454012\n"
        "109.99100 44.408356 0.82202643 0.82371473 2.7691778e-05 2 0.79654300\n"
        "199.92833 48.396423 0.90870106 0.90459925 3.0247858e-05 2 0.95071429\n"
        "201.50000 40.100000 0.70000000 0.70100000 1.2345678e-05 1 0.12345678\n"
    )

    df = read_cutsky_data(data_file, status_select=2)

    assert list(df.columns) == ["RA", "DEC", "Z", "NZ"]
    assert len(df) == 2
    assert df.to_dict(orient="records") == [
        {
            "RA": 109.991,
            "DEC": 44.408356,
            "Z": 0.82202643,
            "NZ": 2.7691778e-05,
        },
        {
            "RA": 199.92833,
            "DEC": 48.396423,
            "Z": 0.90870106,
            "NZ": 3.0247858e-05,
        },
    ]


def test_read_cutsky_data_returns_status_when_not_filtered(tmp_path) -> None:
    """read_cutsky_data should keep STATUS when no selection is requested."""
    data_file = tmp_path / "cutsky_N_0.dat"
    data_file.write_text(
        "# RA(1) DEC(2) Z(3) Z_COSMO(4) NZ(5) STATUS(6) RAN_NUM_0_1(7)\n"
        "199.96126 44.432209 0.82320231 0.82326251 2.770452e-05 0 0.37454012\n"
        "109.99100 44.408356 0.82202643 0.82371473 2.7691778e-05 2 0.79654300\n"
    )

    df = read_cutsky_data(data_file)

    assert list(df.columns) == ["RA", "DEC", "Z", "NZ", "STATUS"]
    assert df.to_dict(orient="records") == [
        {
            "RA": 199.96126,
            "DEC": 44.432209,
            "Z": 0.82320231,
            "NZ": 2.770452e-05,
            "STATUS": 0,
        },
        {
            "RA": 109.991,
            "DEC": 44.408356,
            "Z": 0.82202643,
            "NZ": 2.7691778e-05,
            "STATUS": 2,
        },
    ]


def test_validate_random_box_catalogs_selects_smallest_seeds(tmp_path) -> None:
    for seed in [12, 10, 14]:
        (tmp_path / random_box_filename(boxsize=1000.0, num=50, seed=seed)).write_text("")

    summary = collect_random_box_summary(tmp_path)
    result = validate_random_box_catalogs(
        summary=summary,
        cap="N",
        boxL=1000.0,
        target_num=50,
        density_threshold=4.0e-8,
        nfiles_required=2,
    )

    assert [info.seed for info in result.selected_infos] == [10, 12]
    assert result.failed_checks == []


def test_validate_random_box_catalogs_reports_density_failure(tmp_path) -> None:
    for seed in [10, 12]:
        (tmp_path / random_box_filename(boxsize=1000.0, num=50, seed=seed)).write_text("")

    summary = collect_random_box_summary(tmp_path)
    result = validate_random_box_catalogs(
        summary=summary,
        cap="N",
        boxL=1000.0,
        target_num=50,
        density_threshold=0.2,
        nfiles_required=2,
    )

    assert [info.seed for info in result.selected_infos] == [10, 12]
    assert result.failed_checks and "suggest N_min per file=" in result.failed_checks[0]
    assert "2.1e+8" in result.failed_checks[0]

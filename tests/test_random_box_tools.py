from __future__ import annotations

from lsslab.tools import (
    collect_random_box_summary,
    parse_random_box_filename,
    prepare_random_boxes,
    random_box_filename,
    write_random_catalog,
)


def test_random_box_filename_uses_generation_parameters() -> None:
    assert (
        random_box_filename(boxsize=1000.0, num=50, seed=42)
        == "random_boxL1000_N5.0e1_seed42.dat"
    )
    assert (
        random_box_filename(boxsize=1000.5, num=50, seed=42)
        == "random_boxL1000.5_N5.0e1_seed42.dat"
    )


def test_write_random_catalog_from_tools(tmp_path) -> None:
    output_file = tmp_path / "random.dat"

    result = write_random_catalog(
        ofile=output_file,
        num=20,
        boxsize=100.0,
        seed=7,
    )

    assert result == output_file
    lines = output_file.read_text().strip().split("\n")
    assert len(lines) == 20
    for line in lines:
        x, y, z = map(float, line.split())
        assert 0 <= x <= 100.0
        assert 0 <= y <= 100.0
        assert 0 <= z <= 100.0


def test_prepare_random_boxes_from_tools(tmp_path) -> None:
    result = prepare_random_boxes(
        tmp_path,
        boxsize=1000.0,
        num=10,
        seed=3,
        nran=2,
    )

    assert [path.name for path in result] == [
        "random_boxL1000_N1.0e1_seed3.dat",
        "random_boxL1000_N1.0e1_seed4.dat",
    ]
    assert all(path.exists() for path in result)


def test_parse_random_box_filename() -> None:
    info = parse_random_box_filename("random_boxL6000_N3.0e7_seed42.dat")

    assert info.boxsize == 6000.0
    assert info.num == int(3e7)
    assert info.seed == 42
    assert info.number_density == int(3e7) / 6000.0**3


def test_collect_random_box_summary_from_workdir(tmp_path) -> None:
    for seed in [10, 12]:
        (tmp_path / random_box_filename(boxsize=1000.0, num=50, seed=seed)).write_text("")
    (tmp_path / random_box_filename(boxsize=500.0, num=20, seed=3)).write_text("")
    (tmp_path / "ignore_me.txt").write_text("")

    summary = collect_random_box_summary(tmp_path)
    summary_dict = summary.to_dict()

    assert set(summary_dict) == {"L=1000,N=5.0e1", "L=500,N=2.0e1"}
    assert summary_dict["L=1000,N=5.0e1"]["seeds"] == [10, 12]
    assert summary_dict["L=500,N=2.0e1"]["seeds"] == [3]
    assert summary_dict["L=1000,N=5.0e1"]["number_density"] == 50 / 1000.0**3
    assert "L=1000,N=5.0e1" in str(summary)

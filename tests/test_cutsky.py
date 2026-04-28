"""Tests for CutskyRunner main workflow and script generation."""

import tempfile
from pathlib import Path

import pytest

from lsslab.mock.cutsky import CutskyInputs, CutskyRunner, CubicMockInput, CubicRandomInput
from lsslab.tools.random_box import random_box_filename


@pytest.fixture
def temp_workdir():
    """Create a temporary working directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files(temp_workdir):
    """Create minimal sample files for testing."""
    # Create dummy footprint file
    footprint = temp_workdir / "footprint.ply"
    footprint.write_text(
        """ply
format ascii 1.0
element vertex 4
property float x
property float y
property float z
end_header
0.0 0.0 0.0
1.0 0.0 0.0
1.0 1.0 0.0
0.0 1.0 0.0
"""
    )

    # Create dummy n(z) file
    nz_n = temp_workdir / "nz_N.txt"
    nz_n.write_text(
        """0.2 0.1 0.3 1.0e-9
0.5 0.4 0.6 2.0e-9
0.8 0.7 0.9 1.5e-9
"""
    )

    nz_s = temp_workdir / "nz_S.txt"
    nz_s.write_text(
        """0.2 0.1 0.3 1.0e-9
0.5 0.4 0.6 2.0e-9
0.8 0.7 0.9 1.5e-9
"""
    )

    # Create dummy box file
    box_file = temp_workdir / "box.dat"
    box_file.write_text("x y z\n0.0 0.0 0.0\n100.0 100.0 100.0\n")

    box_file2 = temp_workdir / "box2.dat"
    box_file2.write_text("x y z\n1.0 1.0 1.0\n2.0 2.0 2.0\n")

    return {
        "footprint": footprint,
        "nz_N": nz_n,
        "nz_S": nz_s,
        "box": box_file,
        "box2": box_file2,
    }


def test_runner_initialization_scalar_mock(temp_workdir, sample_files):
    """Test CutskyRunner initialization with scalar mock input."""
    mock_input = CubicMockInput(
        boxL=1000.0,
        box_path=sample_files["box"],
        zmin=0.8,
        zmax=1.1,
    )
    random_input = CubicRandomInput(
        random_dir=temp_workdir / "RANDOM",
        boxL=1000.0,
        zmin=0.8,
        zmax=1.1,
        nsample=25,
        random_file_scale=1.0,
        nfiles=2,
    )
    inputs = CutskyInputs(
        mock=mock_input,
        random=random_input,
        footprint_path=sample_files["footprint"],
        nz_path={"N": sample_files["nz_N"], "S": sample_files["nz_S"]},
    )
    runner = CutskyRunner(workdir=temp_workdir, inputs=inputs)

    assert runner.workdir == temp_workdir
    assert runner.mock.boxL == 1000.0
    assert runner.mock.box_path == sample_files["box"]
    assert runner.mock.num_cases() == 1
    assert runner.footprint_path == sample_files["footprint"]


def test_runner_initialization_list_mock(temp_workdir, sample_files):
    """Test CutskyRunner initialization with list mock input (multiple cases)."""
    mock_input = CubicMockInput(
        boxL=1000.0,
        box_path=[sample_files["box"], sample_files["box2"]],
        zmin=[0.8, 1.1],
        zmax=[1.1, 1.4],
    )
    random_input = CubicRandomInput(
        random_dir=temp_workdir / "RANDOM",
        boxL=1000.0,
        zmin=0.8,
        zmax=1.4,
        nsample=25,
        random_file_scale=1.0,
        nfiles=2,
    )
    inputs = CutskyInputs(
        mock=mock_input,
        random=random_input,
        footprint_path=sample_files["footprint"],
        nz_path={"N": sample_files["nz_N"], "S": sample_files["nz_S"]},
    )
    runner = CutskyRunner(workdir=temp_workdir, inputs=inputs)

    assert runner.workdir == temp_workdir
    assert runner.mock.boxL == 1000.0
    assert runner.mock.box_path == (sample_files["box"], sample_files["box2"])
    assert runner.mock.num_cases() == 2
    assert runner.footprint_path == sample_files["footprint"]


def _make_runner(temp_workdir: Path, sample_files: dict[str, Path], *, nsample: int | dict[str, int]) -> CutskyRunner:
    mock_input = CubicMockInput(
        boxL=1000.0,
        box_path=sample_files["box"],
        zmin=0.8,
        zmax=1.1,
    )
    random_input = CubicRandomInput(
        random_dir=temp_workdir / "RANDOM",
        boxL=1000.0,
        zmin=0.8,
        zmax=1.1,
        nsample=nsample,
        random_file_scale=1.0,
        nfiles=2,
    )
    inputs = CutskyInputs(
        mock=mock_input,
        random=random_input,
        footprint_path=sample_files["footprint"],
        nz_path={"N": sample_files["nz_N"], "S": sample_files["nz_S"]},
    )
    return CutskyRunner(workdir=temp_workdir, inputs=inputs)


def _make_random_boxes(random_dir: Path, *, boxL: float, num: int, seeds: list[int]) -> list[Path]:
    random_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for seed in seeds:
        path = random_dir / random_box_filename(boxsize=boxL, num=num, seed=seed)
        path.write_text("", encoding="utf-8")
        paths.append(path.resolve())
    return sorted(paths)


def test_runner_for_mock_generates_scripts_and_jobs(temp_workdir, sample_files):
    runner = _make_runner(temp_workdir, sample_files, nsample=25)
    runner.prepare_nz()

    scripts, jobs_path = runner.runner_for_mock(rewrite_cat=False)

    assert len(scripts) == 2
    assert jobs_path is not None
    assert jobs_path.exists()
    assert len(jobs_path.read_text().splitlines()) == 2
    assert all(path.exists() for path in scripts)


def test_runner_for_random_uses_validation_and_generates_scripts(temp_workdir, sample_files):
    runner = _make_runner(temp_workdir, sample_files, nsample={"N": 25, "S": 30})
    runner.prepare_nz()
    expected_n = _make_random_boxes(runner.random.random_dir, boxL=1000.0, num=25, seeds=[11, 12])
    expected_s = _make_random_boxes(runner.random.random_dir, boxL=1000.0, num=30, seeds=[21, 22])
    expected_boxes = expected_n + expected_s

    selected_boxes, scripts, jobs_path = runner.runner_for_random()

    assert selected_boxes == expected_boxes
    assert len(scripts) == 4
    assert jobs_path is not None
    assert jobs_path.exists()
    assert len(jobs_path.read_text().splitlines()) == 4
    assert all(path.exists() for path in scripts)


def test_runner_for_random_reports_validation_failure(temp_workdir, sample_files):
    runner = _make_runner(temp_workdir, sample_files, nsample=25)
    runner.prepare_nz()
    _make_random_boxes(runner.random.random_dir, boxL=1000.0, num=25, seeds=[11])

    with pytest.warns(RuntimeWarning, match="using same random boxes for NGC and SGC"):
        with pytest.raises(ValueError, match="Random box validation failed") as exc_info:
            runner.runner_for_random()

    message = str(exc_info.value)
    assert "[N] File count check failed" in message
    assert "required=2" in message


def test_generate_translation_writes_post_cutsky_script(temp_workdir, sample_files):
    runner = _make_runner(temp_workdir, sample_files, nsample={"N": 25, "S": 25})

    script_path = runner.generate_translation(tracer="LRG", with_randoms=True)

    assert script_path.exists()
    content = script_path.read_text()
    assert "scripts/post_cutsky.py" in content
    assert "--workdir" in content
    assert "--data-dir" in content
    assert "--random-dir" in content
    assert "--tracer LRG" in content

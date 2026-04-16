"""
Basic integration tests for the cutsky pipeline.

These tests validate the main workflow of the CutskyRunner and core functions.
"""

import tempfile
from pathlib import Path

import pytest

from lsslab.mock.cutsky import (
    CutskyRunner,
    write_random_catalog,
)


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
        """0.2 0.1 0.3 100.0
0.5 0.4 0.6 200.0
0.8 0.7 0.9 150.0
"""
    )

    nz_s = temp_workdir / "nz_S.txt"
    nz_s.write_text(
        """0.2 0.1 0.3 100.0
0.5 0.4 0.6 200.0
0.8 0.7 0.9 150.0
"""
    )

    # Create dummy box file
    box_file = temp_workdir / "box.dat"
    box_file.write_text("x y z\n0.0 0.0 0.0\n100.0 100.0 100.0\n")

    return {
        "footprint": footprint,
        "nz_N": nz_n,
        "nz_S": nz_s,
        "box": box_file,
    }


class TestWriteRandomCatalog:
    """Test random catalog generation."""

    def test_write_random_catalog_basic(self, temp_workdir):
        """Test basic random catalog generation."""
        output_file = temp_workdir / "random.dat"
        
        result = write_random_catalog(
            ofile=output_file,
            num=100,
            boxL=1000.0,
            seed=42,
        )
        
        # Check that file was created
        assert result.exists()
        assert output_file.exists()
        
        # Check file content
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 100
        
        # Check that coordinates are within bounds
        for line in lines:
            x, y, z = map(float, line.split())
            assert 0 <= x <= 1000.0
            assert 0 <= y <= 1000.0
            assert 0 <= z <= 1000.0

    def test_write_random_catalog_reproducible(self, temp_workdir):
        """Test that same seed produces same output."""
        file1 = temp_workdir / "random1.dat"
        file2 = temp_workdir / "random2.dat"
        
        write_random_catalog(ofile=file1, num=50, boxL=500.0, seed=123)
        write_random_catalog(ofile=file2, num=50, boxL=500.0, seed=123)
        
        # Files should have identical content
        assert file1.read_text() == file2.read_text()


class TestCutskyRunner:
    """Test CutskyRunner orchestrator."""

    def test_runner_initialization(self, temp_workdir, sample_files):
        """Test CutskyRunner can be initialized."""
        runner = CutskyRunner(
            workdir=temp_workdir,
            footprint_path=sample_files["footprint"],
            nz_path={
                "N": sample_files["nz_N"],
                "S": sample_files["nz_S"],
            },
            boxL=6000.0,
        )
        
        assert runner.workdir == temp_workdir
        assert runner.footprint_path == sample_files["footprint"]
        assert runner.boxL == 6000.0

    def test_runner_prepare_random_boxes(self, temp_workdir, sample_files):
        """Test prepare_random_boxes method."""
        runner = CutskyRunner(
            workdir=temp_workdir,
            footprint_path=sample_files["footprint"],
            nz_path={
                "N": sample_files["nz_N"],
                "S": sample_files["nz_S"],
            },
            boxL=1000.0,
        )
        
        result = runner.prepare_random_boxes(num=50, seed=42, nran=3)
        
        assert len(result) == 3
        assert [path.name for path in result] == [
            "random_boxL1000_N5.0e1_seed42.dat",
            "random_boxL1000_N5.0e1_seed43.dat",
            "random_boxL1000_N5.0e1_seed44.dat",
        ]

        for path in result:
            assert path.exists()
            assert path.parent.name == "RANDOM"
            lines = path.read_text().strip().split("\n")
            assert len(lines) == 50

    def test_runner_prepare_random_boxes_skip_existing(self, temp_workdir, sample_files):
        """Test that prepare_random_boxes skips existing files."""
        runner = CutskyRunner(
            workdir=temp_workdir,
            footprint_path=sample_files["footprint"],
            nz_path={
                "N": sample_files["nz_N"],
                "S": sample_files["nz_S"],
            },
            boxL=1000.0,
        )
        
        # First call
        result1 = runner.prepare_random_boxes(num=50, seed=42, nran=2)
        mtimes1 = [path.stat().st_mtime for path in result1]
        
        # Second call should skip
        import time
        time.sleep(0.1)  # Ensure time difference
        result2 = runner.prepare_random_boxes(num=50, seed=42, nran=2)
        mtimes2 = [path.stat().st_mtime for path in result2]
        
        assert mtimes1 == mtimes2
        assert result1 == result2

    def test_runner_prepare_random_boxes_rejects_invalid_nran(self, temp_workdir, sample_files):
        """Test prepare_random_boxes validates nran."""
        runner = CutskyRunner(
            workdir=temp_workdir,
            footprint_path=sample_files["footprint"],
            nz_path={
                "N": sample_files["nz_N"],
                "S": sample_files["nz_S"],
            },
            boxL=1000.0,
        )

        with pytest.raises(ValueError, match="nran must be at least 1"):
            runner.prepare_random_boxes(num=50, seed=42, nran=0)


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_pipeline_initialization(self, temp_workdir, sample_files):
        """Test complete pipeline can be set up."""
        runner = CutskyRunner(
            workdir=temp_workdir,
            footprint_path=sample_files["footprint"],
            nz_path={
                "N": sample_files["nz_N"],
                "S": sample_files["nz_S"],
            },
            boxL=6000.0,
            boxL_random=6000.0,
        )
        
        box_paths = runner.prepare_random_boxes(num=100, seed=42, nran=2)
        
        assert len(box_paths) == 2
        assert all(box_path.exists() for box_path in box_paths)

        random_cases = [
            {
                "zmin": 0.8,
                "zmax": 1.1,
            },
        ]
        random_scripts = runner.generate_random(random_cases, box_paths=box_paths)

        assert len(random_scripts) == 4
        assert len(set(random_scripts)) == 4
        assert all(script.exists() for script in random_scripts)
        assert all(script.parent == temp_workdir / "RANDOM" for script in random_scripts)
        assert {script.name for script in random_scripts} == {
            "run_cutsky_ran0_N_0.8_1.1.sh",
            "run_cutsky_ran0_S_0.8_1.1.sh",
            "run_cutsky_ran1_N_0.8_1.1.sh",
            "run_cutsky_ran1_S_0.8_1.1.sh",
        }

        assert (temp_workdir / "RANDOM").exists()

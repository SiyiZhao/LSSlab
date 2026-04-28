"""Tests for CubicMockInput and CubicRandomInput data classes."""

from pathlib import Path

import pytest

from lsslab.mock.cutsky import CubicMockInput, CubicRandomInput


def test_cubic_mock_input_scalar():
    """Test CubicMockInput with scalar fields (single case)."""
    mock = CubicMockInput(
        boxL=1000.0,
        box_path=Path("/tmp/box.dat"),
        zmin=0.8,
        zmax=1.1,
    )
    assert mock.boxL == 1000.0
    assert mock.box_path == Path("/tmp/box.dat")
    assert mock.zmin == 0.8
    assert mock.zmax == 1.1
    assert mock.num_cases() == 1

    cases = list(mock.iter_cases())
    assert len(cases) == 1
    bp, zmin, zmax, sn = cases[0]
    assert bp == Path("/tmp/box.dat")
    assert zmin == 0.8
    assert zmax == 1.1
    assert sn is None


def test_cubic_mock_input_list():
    """Test CubicMockInput with list fields (multiple cases)."""
    mock = CubicMockInput(
        boxL=1000.0,
        box_path=[Path("/tmp/box1.dat"), Path("/tmp/box2.dat")],
        zmin=[0.8, 1.1],
        zmax=[1.1, 1.4],
    )
    assert mock.boxL == 1000.0
    assert mock.box_path == (Path("/tmp/box1.dat"), Path("/tmp/box2.dat"))
    assert mock.zmin == (0.8, 1.1)
    assert mock.zmax == (1.1, 1.4)
    assert mock.num_cases() == 2

    cases = list(mock.iter_cases())
    assert len(cases) == 2

    bp0, z0min, z0max, sn0 = cases[0]
    assert bp0 == Path("/tmp/box1.dat")
    assert z0min == 0.8
    assert z0max == 1.1
    assert sn0 is None

    bp1, z1min, z1max, sn1 = cases[1]
    assert bp1 == Path("/tmp/box2.dat")
    assert z1min == 1.1
    assert z1max == 1.4
    assert sn1 is None


def test_cubic_mock_input_list_with_script_names():
    """Test CubicMockInput with list fields including script names."""
    mock = CubicMockInput(
        boxL=1000.0,
        box_path=[Path("/tmp/box1.dat"), Path("/tmp/box2.dat")],
        zmin=[0.8, 1.1],
        zmax=[1.1, 1.4],
        script_name=["script1.sh", "script2.sh"],
    )
    assert mock.num_cases() == 2
    assert mock.script_name == ("script1.sh", "script2.sh")

    cases = list(mock.iter_cases())
    assert len(cases) == 2

    _, _, _, sn0 = cases[0]
    assert sn0 == "script1.sh"

    _, _, _, sn1 = cases[1]
    assert sn1 == "script2.sh"


def test_cubic_mock_input_validation_zmin_zmax():
    """Test that CubicMockInput validates zmin < zmax."""
    with pytest.raises(ValueError, match="must be greater than zmin"):
        CubicMockInput(
            boxL=1000.0,
            box_path=Path("/tmp/box.dat"),
            zmin=1.1,
            zmax=0.8,
        )


def test_cubic_mock_input_validation_boxL():
    """Test that CubicMockInput validates boxL > 0."""
    with pytest.raises(ValueError, match="boxL must be positive"):
        CubicMockInput(
            boxL=-1000.0,
            box_path=Path("/tmp/box.dat"),
            zmin=0.8,
            zmax=1.1,
        )


def test_cubic_mock_input_validation_inconsistent_lists():
    """Test that CubicMockInput validates consistent list lengths."""
    with pytest.raises(ValueError, match="Inconsistent case counts"):
        CubicMockInput(
            boxL=1000.0,
            box_path=[Path("/tmp/box1.dat"), Path("/tmp/box2.dat")],
            zmin=[0.8],  # Only 1 element, but box_path has 2
            zmax=[1.1, 1.4],
        )

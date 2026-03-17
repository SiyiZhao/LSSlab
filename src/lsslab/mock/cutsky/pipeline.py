"""
Generate runnable shell scripts that invoke prep_cutsky + cutsky.

These utilities only write scripts; they do not execute cutsky.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .script import cutsky_script

__all__ = ["CutskyRunner"]


class CutskyRunner:
    """
    Generate cutsky runner scripts with shared defaults.

    Pass a single case or a list of cases; each case must include `box_path`,
    `galactic_cap`, `zmin`, and `zmax`. Optionally override `nz_path`,
    `footprint_path`, `workdir`, `boxL`, and output script name per case. For
    `galactic_cap`, you may pass a single value ("N" or "S"), "NS"/"SN", or a
    list/tuple of caps, and the runner will emit one script per cap.
    """

    def __init__(
        self,
        *,
        workdir: Path,
        footprint_path: Path,
        nz_path: Path,
        boxL: float,
    ) -> None:
        self.workdir = workdir
        self.footprint_path = footprint_path
        self.nz_path = nz_path
        self.boxL = boxL

    def _normalize_cases(
        self, cases: Sequence[Mapping[str, Any]] | Mapping[str, Any]
    ) -> list[Mapping[str, Any]]:
        if isinstance(cases, Mapping):
            return [cases]
        return list(cases)

    def _normalize_caps(self, cap_value: Any) -> list[str]:
        if isinstance(cap_value, str):
            if cap_value in {"NS", "SN"}:
                return ["N", "S"]
            return [cap_value]
        if isinstance(cap_value, Sequence):
            return list(cap_value)
        raise TypeError("galactic_cap must be str or a sequence of str")

    def generate(
        self,
        cases: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        *,
        make_executable: bool = True,
    ) -> list[Path]:
        """
        Write runner scripts for one or more cases; return script paths.
        """

        scripts: list[Path] = []
        for case in self._normalize_cases(cases):
            caps = self._normalize_caps(case["galactic_cap"])
            zmin = case["zmin"]
            zmax = case["zmax"]
            box_path = Path(case["box_path"])

            boxL = case.get("boxL", self.boxL)
            footprint = Path(case.get("footprint_path", self.footprint_path))
            nz_path = Path(case.get("nz_path", self.nz_path))
            wd = Path(case.get("workdir", self.workdir))
            wd.mkdir(parents=True, exist_ok=True)

            for cap in caps:
                script_name = case.get("script_name", f"run_cutsky_{cap}_{zmin}_{zmax}.sh")
                script_path = wd / script_name

                cutsky_script(
                    workdir=wd,
                    box_path=box_path,
                    boxL=boxL,
                    footprint=footprint,
                    galactic_cap=cap,
                    nz_path=nz_path,
                    zmin=zmin,
                    zmax=zmax,
                    write_to=script_path,
                    make_executable=make_executable,
                )

                scripts.append(script_path)

        return scripts

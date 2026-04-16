"""
Cutsky pipeline package: prepares inputs, configs, and invocations for the external `cutsky` binary.

This module provides a complete pipeline for generating cutsky-based mock catalogs:

- **prepare_nz**: Transform DESI-format n(z) files to cutsky format
- **cutsky_cfg**: Render cutsky configuration files
- **cutsky_script**: Generate shell scripts to run cutsky
- **CutskyRunner**: High-level tool for data and random catalog generation
- **write_random_catalog**: Generate uniform random box catalogs

Typical workflow
----------------
1. Prepare n(z) files using :func:`prepare_nz`
2. Create a :class:`CutskyRunner` with shared settings (workdir, footprint, nz_path, boxL)
3. Call :meth:`CutskyRunner.generate_data` to create data catalog scripts
4. Call :meth:`CutskyRunner.prepare_random_boxes` to generate one or more random box files with different seeds
5. Call :meth:`CutskyRunner.generate_random` to create random catalog scripts
6. Execute the generated shell scripts to run cutsky

For most use cases, do not scale the random n(z) separately. To make the
random sample several times larger than the data sample, generate multiple
random realizations with different seeds instead.

See Also
--------
Complete working example: ``examples/cutsky_runner_demo.py`` and ``examples/prepare_nz.py``.
"""

from .nz import prepare_nz
from .config import cutsky_cfg
from .script import cutsky_script
from .pipeline import CutskyRunner
from .random import write_random_catalog

__all__ = [
    "prepare_nz",
    "cutsky_cfg",
    "cutsky_script",
    "CutskyRunner",
    "write_random_catalog",
]

# Changelog

## [0.2.0] - 2026-04-15

### Changed
- Replaced `prepare_random_box` with `prepare_random_boxes` to support `nran` random-box realizations with shared `num` and different seeds.
- Updated the random-catalog workflow to prefer using the same `n(z)` as data and increasing random counts via multiple random seeds instead of scaled `n(z)` files.
- Updated `generate_random` to accept `box_paths` directly and encode realization indices in filenames to avoid overwriting multi-seed random outputs.
- Refreshed examples, tests, and docs to follow the new multi-seed random workflow.
- Added `tests/conftest.py` so `pytest` can import the `src/` layout package without manually setting `PYTHONPATH`.
- Updated the release workflow to publish wheel-only artifacts for now, matching the current PyPI release practice while `sdist` remains skipped.

## [0.1.0] - 2026-03-18

### Added
- Core `mock.cutsky` module for cutsky mock pipeline (pipeline, config, script, random, nz)
- Comprehensive test suite for cutsky functionality
- Example usage and documentation

### Published
- Released on PyPI: https://pypi.org/project/LSSlab/0.1.0/

## [0.0.1] - Initial release

Initial scaffold with project structure and framework only. No core functionality implemented.

### Published
- Released on PyPI: https://pypi.org/project/LSSlab/0.0.1/

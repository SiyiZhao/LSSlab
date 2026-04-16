# Mock Module

## Scope
- Tools to generate mock galaxy catalogs.
- Includes cut-sky/lightcone construction from periodic simulation boxes.

## Layout

- `lsslab.mock.__init__`: package entrypoint; exports cutsky submodule
- `lsslab.mock.cutsky`: core routines to turn box catalogs into lightcone mocks
  - `nz.py`: N(z) file transformation
  - `config.py`: configuration rendering
  - `script.py`: shell script generation
  - `pipeline.py`: CutskyRunner orchestrator
  - `random.py`: random catalog utilities

## Cutsky Pipeline

Generates light-cone mock catalogs using the external [cutsky](https://github.com/cheng-zhao/cutsky) binary.

**Features**:
- Multi-galactic-cap support (NGC, SGC)
- N(z) file transformation and validation
- Automatic shell script generation
- Uniform random box generation with multiple seeds via `nran`

Recommended random-catalog workflow:
- Use the same n(z) for data and random catalogs.
- If you want randoms to be several times denser than the data sample, generate
  multiple random realizations with different seeds instead of scaling n(z).

**Quick Start**: See `examples/cutsky_runner_demo.py` for a complete working example.

## Future Improvements

### Cutsky Pipeline (Planned)

1. **Decouple config generation from data format conversion**
   - Currently: config and data prep are tightly coupled in `cutsky_script` by an extra script `scripts/prep_cutsky.py`, which use `mockfactory` to transfer the data format, but config prep is able to be included in our pipeline, no extra dependent, and random catalog do not need data format transfer.
   - Goal: separate concerns for better composability and testing

2. **Cache data transformations in memory instead of disk**
   - Currently: the ASCII files of box catalogs that would be input to `cutsky` are written to disk
   - Goal: buffer data and random boxes in memory when possible to reduce I/O overhead
   - Benefit: significant speedup

3. **Parallel processing**
   - Random box generation: parallelize across multiple seeds or chunks
   - Multi-snapshot cutsky: process multiple snapshots concurrently
   - Use case: streamlined processing of many random realizations and multi-snapshot simulations

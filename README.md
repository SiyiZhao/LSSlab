# LSSlab

LSSlab is a Python toolkit collection for the analysis of Cosmological Large-Scale Structure (LSS).

*Let our Universe be a big Lab!* 

## Installation

Install from PyPI:

```bash
pip install LSSlab
```

Alternatively, install from a local clone with `uv`:

```bash
git clone https://github.com/SiyiZhao/LSSlab.git
cd LSSlab
uv sync
```

### Scripts with extra deps

Some helper scripts in `scripts/` may require additional packages (e.g., cutsky prep). Keep those dependencies in a separate environment. See `docs/extra-deps.md` for notes.

## Usage

```python
import lsslab

print(lsslab.__version__)
```

## Development

Set up the project environment with `uv`:

```bash
uv sync
```

Run the test suite in the project environment:

```bash
uv run pytest
```

Build the wheel:

```bash
uv build --wheel
```

Recommended pre-release smoke test from a clean environment:

```bash
python -m venv /tmp/lsslab-wheel-test
source /tmp/lsslab-wheel-test/bin/activate
python -m pip install dist/lsslab-*.whl
python -c "import lsslab; import lsslab.mock.cutsky"
deactivate
```

Release a new version by updating the version metadata, committing the release
files, and pushing a version tag:

```bash
uv version --bump patch
git add pyproject.toml uv.lock CHANGELOG.md
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## License

BSD-3-Clause (see LICENSE)

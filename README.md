# LSSlab

Lightweight scaffolding for the LSSlab Python package.

## Installation (local dev)

```
python -m pip install -e .
```

### Recommended: isolated env

```
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest
```

## Usage

```python
import lsslab

print(lsslab.__version__)
```

## Development

- Tooling (one-time): `pip install --upgrade build twine`
- Build: `python -m build`
- Check artifacts: `python -m twine check dist/*`

## License

BSD-3-Clause (see LICENSE)

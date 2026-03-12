# LSSlab

Lightweight scaffolding for the LSSlab Python package.

## Installation (local dev)

```
pip install -e .
```

### Recommended: isolated env

```
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
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

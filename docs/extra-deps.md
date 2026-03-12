# Extra Dependencies

Some helper scripts under `scripts/` may require packages not installed with the core `lsslab` (for example, mockfactory or environment-specific DESI tooling). Keep these in a separate environment so the base install stays lightweight. Document any script-specific requirements here as they arise.

## Suggested extra environment

Create a dedicated venv (example path `~/envs/lsslab_extra`) for script-only dependencies:

```
python -m venv ~/envs/lsslab_extra
source ~/envs/lsslab_extra/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Activate this env whenever running helper scripts that need extra packages (e.g., `scripts/prep_cutsky.py`). It would be write into the functions of generating bash scripts if needed.

### mockfactory

```
python -m pip install git+https://github.com/cosmodesi/mockfactory
```

## Extra binary dependencies

LSSlab assume the extra libaries are available in `~/lib/`.

### cutsky

[cutsky](https://github.com/SiyiZhao/cutsky/) can be easily downloaded and compiled by

```
git clone https://github.com/SiyiZhao/cutsky.git
cd cutsky
make
```
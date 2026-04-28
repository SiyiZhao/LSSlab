#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prepare the input catalog in the required format.

Usage
-----
$ python prep_cutsky.py

Author: Siyi Zhao
"""
import numpy as np

try:
    from mpytools import Catalog
except ImportError:
    raise ImportError(
        "mpytools is required for `LSSlab/scripts/prep_cutsky.py`. Please install it via `python -m pip install git+https://github.com/cosmodesi/mpytools`, or consider `uv add https://github.com/cosmodesi/mpytools.git."
    )

__all__ = [
    "prep_cat_in_ASCII_format",
]

def prep_cat_in_ASCII_format(
    input_path: str,
    output_path: str,
    boxsize: float | None = None,
) -> None:
    """Prepare the input catalog in ASCII format required by cutsky.

    Args:
        input_path (str): Path to the input catalog file.
        output_path (str): Path to save the formatted ASCII catalog.
        boxsize (float | None, optional): Size of the simulation box in Mpc/h. If provided, apply periodic wrapping. Defaults to None.
    """
    cat=Catalog.read(input_path)
    x = cat['X']
    y = cat['Y']
    z = cat['Z']
    vx = cat['VX']
    vy = cat['VY']
    vz = cat['VZ']
    # If boxsize is provided, apply periodic wrapping
    if boxsize is not None:
        x = x % boxsize
        y = y % boxsize
        z = z % boxsize
    # Prepare the output in the required format
    formatted_data = np.column_stack((x, y, z, vx, vy, vz))
    header = "X Y Z VX VY VZ"
    np.savetxt(output_path, formatted_data, header=header, comments='#', fmt='%.6f')
    print(f"[write] Formatted catalog -> {output_path}")


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Prepare cutsky configuration and input catalog.")
    parser.add_argument('--catalog_path', type=str, required=True, help='Path to the input catalog file.')
    parser.add_argument('--boxsize', type=float, default=2000.0, help='Size of the simulation box in Mpc/h.')
    parser.add_argument('--workdir', type=str, default='works/test_prep_cutsky', help='Working directory to save outputs.')
    parser.add_argument('--zmin', type=float, default=2.8, help='Minimum redshift.')
    parser.add_argument('--zmax', type=float, default=3.5, help='Maximum redshift.')
    return parser.parse_args()

if __name__ == "__main__":
    import os
    
    args = parse_args()
    catalog_path = args.catalog_path
    boxsize = args.boxsize
    WORKDIR = args.workdir
    os.makedirs(WORKDIR, exist_ok=True)
    zmin = args.zmin
    zmax = args.zmax
    box_path = WORKDIR + f'/box_{zmin}_{zmax}.dat'

    prep_cat_in_ASCII_format(
        input_path=catalog_path,
        output_path=box_path,
        boxsize=boxsize,
    )
        
    
    print(f"Done preparing input catalog. Just run:")
    
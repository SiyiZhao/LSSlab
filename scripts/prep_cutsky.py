#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prepare cutsky configuration file and the input catalog in the required format.

Usage
-----
$ source ~/envs/lsslab_extra/bin/activate
$ python prep_cutsky.py

Author: Siyi Zhao
"""
import numpy as np

from lsslab.mock.cutsky import cutsky_cfg

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
    from mockfactory import Catalog

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
    parser.add_argument('--rewrite_cat', action='store_true', help='Whether to rewrite the input catalog in ASCII format.')
    parser.add_argument('--workdir', type=str, default='works/test_prep_cutsky', help='Working directory to save outputs.')
    parser.add_argument('--footprint', type=str, default='/global/homes/s/siyizhao/lib/cutsky/scripts/Y3_dark_circle.dat_final_res7.ply', help='Path to the footprint file.')
    parser.add_argument('--galactic_cap', type=str, choices=['N', 'S'], default='N', help="Galactic cap to use ('N' or 'S').")
    parser.add_argument('--nz_path', type=str, default='/global/homes/s/siyizhao/projects/fihobi/data/nz/QSO_NGC_nz_v2.txt', help='Path to the n(z) file.')
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
    footprint_path = args.footprint
    galactic_cap = args.galactic_cap  # 'N' or 'S'
    nz_path = args.nz_path
    zmin = args.zmin
    zmax = args.zmax
    box_path = WORKDIR + f'/box_{zmin}_{zmax}.dat'
    lc_path = WORKDIR + f'/cutsky_{galactic_cap}_{zmin}_{zmax}.dat'
    write_to = WORKDIR + f'/cutsky_{galactic_cap}_{zmin}_{zmax}.conf'

    if args.rewrite_cat:
        prep_cat_in_ASCII_format(
            input_path=catalog_path,
            output_path=box_path,
            boxsize=boxsize,
        )
    else:
        box_path = catalog_path  # use the original catalog path
        
    cutsky_cfg(
        box_path=box_path,
        boxsize=boxsize,
        lc_out_path=lc_path,
        footprint_path=footprint_path,
        galactic_cap=galactic_cap,
        nz_path=nz_path,
        zmin=zmin,
        zmax=zmax,
        write_to=write_to,
    )
    
    print(f"Done preparing cutsky configuration and input catalog. Just run:")
    print(f"~/lib/cutsky/CUTSKY -c {write_to} > {WORKDIR}/lc_test.log 2>&1")
    
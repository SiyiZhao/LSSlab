#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Post-process cutsky outputs into final catalogs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running this script from source tree without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lsslab.mock.cutsky.normalize import normalize_regions
from lsslab.mock.cutsky.translator import merge_cutsky_catalog, trans_random_cats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Translate cutsky DATA/RANDOM outputs into LSScat catalogs.",
    )
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--tracer", type=str, default="QSO")
    parser.add_argument("--GC", type=str, default="NS")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--random-dir", type=Path, default=None)
    parser.add_argument("--with-randoms", action="store_true")
    parser.add_argument("--randoms-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    workdir = args.workdir.expanduser().resolve()
    caps = normalize_regions(args.GC)

    if args.output is not None and len(caps) != 1:
        raise ValueError("--output can only be used with a single GC (N or S).")

    for cap in caps:
        if not args.randoms_only:
            merge_cutsky_catalog(
                workdir=workdir,
                tracer=args.tracer,
                GC=cap,
                output_fn=args.output,
                output_dir=args.output_dir,
                data_dir=args.data_dir,
            )

        if args.with_randoms or args.randoms_only:
            trans_random_cats(
                workdir=workdir,
                tracer=args.tracer,
                GC=cap,
                output_dir=args.output_dir,
                random_dir=args.random_dir,
            )


if __name__ == "__main__":
    main()

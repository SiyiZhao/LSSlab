from pathlib import Path

from lsslab.tools import (
    collect_random_box_summary,
    prepare_random_boxes,
)


def main() -> None:
    workdir = Path("/pscratch/sd/s/siyizhao/random_boxes")

    box_paths = prepare_random_boxes(
        workdir,
        boxsize=6000.0,
        num=int(1.5e8),
        seed=1,
        nran=10,
    )

    print("Generated random box catalogs:")
    for path in box_paths:
        print(path)

    print("\nSummary:")
    summary = collect_random_box_summary(workdir)
    print(summary)

    print("\nSummary dict:")
    print(summary.to_dict())


if __name__ == "__main__":
    main()

# Cutsky Runner Workflow

`lsslab.mock.cutsky` 负责生成 cutsky 执行脚本，并在后处理阶段调用 `scripts/post_cutsky.py`。

## 输入模型

- `CubicMockInput(box_path, boxL, zmin, zmax[, script_name])`
- `CubicRandomInput(random_dir, boxL, zmin, zmax, nsample, random_file_scale, nfiles)`
- `CutskyInputs(mock, random, footprint_path, nz_path={"N": path_n, "S": path_s})`

其中：

- `nsample` 可以是单值或按区域的字典（`{"N": ..., "S": ...}`）。
- `random_file_scale` 只用于随机侧 `n(z)` 文件缩放，不参与随机盒子目标数推导。

## 主流程

推荐按下面顺序调用：

1. `prepare_nz()`
2. `runner_for_mock()`
3. `runner_for_random()`
4. `generate_translation()`

```python
from pathlib import Path

from lsslab.mock.cutsky import CutskyInputs, CutskyRunner, CubicMockInput, CubicRandomInput

runner = CutskyRunner(
    workdir=Path("outputs"),
    inputs=CutskyInputs(
        mock=CubicMockInput(
            box_path=Path("box.dat"),
            boxL=6000.0,
            zmin=0.8,
            zmax=1.1,
        ),
        random=CubicRandomInput(
            random_dir=Path("outputs/RANDOM"),
            boxL=6000.0,
            zmin=0.8,
            zmax=1.1,
            nsample={"N": 230000000, "S": 150000000},
            random_file_scale=1.0,
            nfiles=10,
        ),
        footprint_path=Path("footprint.ply"),
        nz_path={"N": Path("nz_N.txt"), "S": Path("nz_S.txt")},
    ),
)

runner.prepare_nz()
data_scripts, data_jobs = runner.runner_for_mock(rewrite_cat=True)
selected_random_boxes, random_scripts, random_jobs = runner.runner_for_random()
translate_script = runner.generate_translation(tracer="LRG", with_randoms=True)
```

## 随机盒子校验

`runner_for_random()` 内部调用 `utils.validate_random_box_catalogs(...)`，按区域进行统一校验：

- 输入参数包含 `boxL`, `target_num`, `density_threshold`, `nfiles_required` 等。
- `target_num` 直接来自 `nsample`（单值或按区域字典）。
- 两个检查条件：
  - 密度检查：`sum(selected.number_density) > density_threshold * nfiles_required`
  - 文件数量检查：`available >= nfiles_required`
- 若密度不足，错误中会附带建议 `N_min`（科学计数法，一位小数，指数不做零填充）。

## 目录输出约定

- `workdir/DATA/`：data 侧 `conf/sh/log/dat` 与可选 `jobs.sh`
- `workdir/RANDOM/`：random 侧 `conf/sh/log/dat` 与可选 `jobs.sh`
- `workdir/LSScat/`：post-translation 输出目录

## 相关示例

- 端到端示例：`examples/cutsky_runner_demo.py`
- 后处理入口：`scripts/post_cutsky.py`

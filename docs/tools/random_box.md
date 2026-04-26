# `lsslab.tools.random_box` 设计说明

## 模块定位

`lsslab.tools.random_box` 是 LSSlab 中面向随机盒子 catalog 的基础工具模块，负责统一处理：

- 标准文件命名
- 文件名解析
- 单文件生成
- 多 realization 批量生成
- 目录级汇总

它关注的是“随机盒子文件与元信息管理”，不是下游科学分析流程。

## 核心设计思路

核心约定是把参数与文件身份绑定：

- `boxsize + num + seed -> filename`
- `filename -> boxsize + num + seed`

标准文件名格式：

```text
random_boxL{boxsize}_N{num}_seed{seed}.dat
```

这一约定带来三个直接收益：

- 文件名天然携带关键元信息
- 目录扫描时无需读取大文件内容
- 生成逻辑与解析逻辑共享同一规则，降低不一致风险

## 接口用途

- `random_box_filename(...)`：生成标准随机盒子文件名。
- `parse_random_box_filename(...)`：从标准文件名恢复 `boxsize/num/seed`，返回 `RandomBoxInfo`。
- `write_random_catalog(...)`：写出单个随机盒子数据文件。
- `prepare_random_boxes(...)`：按起始 `seed` 批量准备多个随机盒子 realization。
- `collect_random_box_summary(...)`：扫描目录并按 `(boxsize, num)` 聚合现有文件，返回 `RandomBoxSummary`。


详细参数、返回值、异常和边界行为，请以源码函数 docstring 为准。

## 数据结构（dataclass）

- `RandomBoxInfo`：表示单个随机盒子文件的元信息对象，包含 `path`、`boxsize`、`num` 和 `seed`。
	主要用于文件名解析后的结构化承载，也可通过 `number_density` 快速获得该文件对应的数密度。
- `RandomBoxSummary`：表示一次目录扫描得到的分组汇总对象，核心字段是 `root` 和按 `(boxsize, num)` 分组的 `groups`。
	主要用于把“目录里已有的随机盒子状态”整理为可读、可序列化的快照，供上层 workflow 直接消费。

## 模块边界

该模块负责“随机盒子文件层”的通用能力，不负责：

- cutsky 配置构建
- 几何投影/物理建模
- 下游 catalog 翻译
- 文件内容完整性校验

因此它适合作为上层 workflow（如 cutsky pipeline）可复用的基础组件。

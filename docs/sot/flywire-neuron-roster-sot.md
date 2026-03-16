# FlyWire Neuron Roster SoT

> Scope: `FlyWire official route（FlyWire 官方路线）` 下的 `neuron roster（神经元名录）`、`graph scope（运行图范围）` 与 `neuropil truth validation（神经纤维区真值校验）` 契约。
> Status: active
> Last updated: 2026-03-17

## 1. Purpose

本文件是本仓库关于 `FlyWire 783 / public` 神经元名录与运行图范围的单一事实来源文档。

它回答 3 个问题：

1. 哪个文件是官方根名录。
2. 当前训练/运行图的节点范围是什么。
3. `node_neuropil_occupancy.parquet（节点级神经纤维区占据表）` 应该和什么口径做正式校验。

## 2. Canonical Sources

### 2.1 Official canonical neuron roster

官方根名录是：

- `data/raw/flywire_783_neuropil_release/proofread_root_ids_783.npy`

这份文件定义了 `FlyWire 783` 官方 `proofread neuron roster（校对神经元名录）`。

### 2.2 Official raw neuropil truth

官方神经纤维区真值根文件是：

- `data/raw/flywire_783_neuropil_release/flywire_synapses_783.feather`
- `data/raw/flywire_783_neuropil_release/per_neuron_neuropil_count_pre_783.feather`
- `data/raw/flywire_783_neuropil_release/per_neuron_neuropil_count_post_783.feather`

### 2.3 Annotation-derived roster

`search_annotations（注释表查询）` 返回的注释表名录不是官方校对名录本身，它只是注释表范围。

当前全量 snapshot 导出链：

- `src/fruitfly/snapshot/exporter.py`
- `_load_full_annotations(...)`
- `_normalize_annotation_nodes(...)`

使用 `search_annotations(...)` 结果生成节点名录。

因此：

- `annotation roster（注释表名录）` 不是 canonical roster
- 它只能作为 metadata overlay（元数据覆盖层）或派生运行范围来源

### 2.4 Frozen annotation enrichment

正式导出链使用本地冻结的 annotation enrichment（注释元数据覆盖层）：

- `data/derived/flywire_783_annotation_enrichment_release/annotation_enrichment_783.parquet`

这份文件的来源可以是一次性 `search_annotations(..., materialization=783)` 冻结，但它本身是项目内的版本化 derived source（派生来源层），不是在线查询结果。

因此：

- 正式 full snapshot/export 不再默认实时依赖 `search_annotations`
- 缺失 frozen annotation enrichment 时，proofread-scoped full export 应直接失败
- `search_annotations` 只用于更新/重建这份 frozen enrichment，不再参与正式导出时的 roster 决策

## 3. Current Operational Graph

当前训练/运行图节点范围定义为：

- `outputs/compiled/flywire_public_full_v783/node_index.parquet`

这是当前 `operational graph（运行图）` 的正式节点范围。

它是项目运行切片，不是官方根名录本身。

## 4. Current Measured Differences

2026-03-17 本地实测：

- `proofread_root_ids_783.npy`：`139,255`
- 当前 `node_index.parquet`：`139,244`
- 当前 `search_annotations(..., materialization=783)` 注释表名录：`139,244`

与 `proofread roster` 对比：

- 当前图 `graph_only_root_count = 15`
- 当前图 `proofread_only_root_count = 26`

进一步实测表明：

- 当前图里相对 `proofread roster` 多出来的 `15` 个 root，全部来自 `annotation roster`
- `proofread roster` 里缺失的 `26` 个 root，全部不在 `annotation roster` 中

即：

- `graph_only_roots_not_in_annotation = []`
- `proofread_only_roots_present_in_annotation = []`

这说明当前 `15 / 26` 差异的主因是：

**当前 snapshot/export 链使用了 annotation-derived roster，而不是 proofread roster。**

## 5. Formal Validation Contract

正式 `neuropil truth validation` 分为两层：

### 5.1 Graph-scoped validation

比较对象：

- `outputs/compiled/flywire_public_full_v783/node_neuropil_occupancy.parquet`
- 官方 `per_neuron_neuropil_count_*_783.feather` 在当前 `node_index.parquet` 范围内的投影

这是当前运行图范围内的正式正确性校验。

### 5.2 Proofread roster alignment

比较对象：

- 当前 `node_index.parquet`
- 官方 `proofread_root_ids_783.npy`

这是名录对齐状态，不等同于 `node_neuropil_occupancy` 正确性。

因此：

- `graph-scoped validation passed`
  不等于
- `proofread roster alignment passed`

两者必须分开表达。

## 6. Current Runtime Interpretation

当前 UI / API 应按以下语义解释：

- `validation_passed = true`
  - 表示当前运行图范围内的官方 neuropil 计数一致
- `roster_alignment_passed = false`
  - 表示当前运行图名录尚未完全等于官方 proofread roster

不允许再把这两个状态混成单个“官方全部通过/失败”。

## 7. Forward Path

如果目标是完全对齐官方 `proofread roster`，下一步应当：

1. 重构 full snapshot/export，使节点名录根改为 `proofread_root_ids_783.npy`
2. 将 `search_annotations` 降级为离线 frozen annotation enrichment（冻结注释覆盖层）的更新来源，而不是 roster source
3. 正式导出链默认只读本地 frozen annotation enrichment
4. 重建 snapshot / compiled graph / downstream artifacts

在这之前，当前正式主线应保持：

- 官方原始真值为根
- 当前运行图为明确的 graph scope
- 正式校验为 graph-scoped validation

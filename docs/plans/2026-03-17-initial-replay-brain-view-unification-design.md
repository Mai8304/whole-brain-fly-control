# Initial/Replay Brain-View Unification Design

## 背景

当前 `neural console（神经控制台）` 的 `brain-view（脑图载荷）` 已经完成了从旧 `ROI（脑区）` 单标签语义向 `neuropil（神经纤维区）` 正式语义的迁移，但 `initial /api/console/brain-view` 和 `replay /api/console/replay/brain-view` 仍然存在“来源不同、缓存可见性不同、调试可解释性不足”的问题。

仓库当前已具备这些前提：

- `node_neuropil_occupancy.parquet（节点级神经纤维区占据真值）`
- `neuropil_truth_validation.json（神经纤维区真值校验结果）`
- `runtime_activity_artifacts.py` 中统一的 `brain-view builder（脑图构建器）`
- `console_api.py` 中对过期 `brain_view.json` 的重物化逻辑
- `tests/ui/test_console_api.py` 中对旧 schema（旧数据契约）重物化的测试覆盖

这意味着当前设计目标不再是“从旧 ROI 主线迁移到 neuropil 主线”，而是把已经基本成型的 `formal neuropil truth chain（正式神经纤维区真值链）` 收紧成真正的 `single authoritative chain（唯一权威数据链）`。

## 问题定义

当前用户感知上的不确定性主要有两个来源：

1. 无法从 UI/API 一眼确认当前 `brain-view` 是否来自同一条正式数据链。
2. 无法从 UI/API 一眼确认当前显示的是：
   - `initial-materialized（初始最终步物化载荷）`
   - `replay-live-step（回放当前步实时载荷）`

此外，缓存当前是否“仍然有效”的规则虽然已经覆盖了旧 schema，但还需要更明确地表达为正式契约，而不是散落在实现细节中的隐式判断。

## 目标

- 统一 `initial` 和 `replay` 的 `brain-view` 响应契约。
- 明确 `brain_view.json / timeline.json` 只是 `cache artifact（缓存产物）`，不是事实来源。
- 明确 `stale invalidation（过期失效）` 规则，保证活动 trace（活动轨迹）或 neuropil 真值变化后不会继续读旧缓存。
- 在 UI/API 中显式表达 `provenance（来源追踪）`，让研究者能确认当前数据确实来自正式链。

## 非目标

- 不在本设计中加入 `3D neuropil glow（3D 脑区发光）`。
- 不在本设计中加入 `node position mapping（神经元空间位置映射）`。
- 不在本设计中重构 `BrainShellViewport（脑壳视口）` 的 3D 组件选型。

## 方案对比

### 方案 A：Strict Cacheless（完全无缓存）

每次请求 `/api/console/brain-view` 都直接从输入源现算，不再读取 `brain_view.json`。

优点：

- 语义最纯，不存在缓存误用。

缺点：

- 失去物化缓存的价值。
- 后续产物规模增加后，启动和请求成本更高。

### 方案 B：Validated Materialized Cache（带校验的物化缓存）

保留 `brain_view.json / timeline.json`，但只把它们当作缓存使用。只有在契约版本、必需字段和输入新鲜度都通过时才允许复用，否则强制重物化。

优点：

- 保留缓存收益。
- 与当前实现方向一致，改动面最小。
- 最容易满足科研模式下的可追溯性和 fail-closed（默认关闭式失败）要求。

缺点：

- 需要把“当前有效”规则定义得非常明确。

### 方案 C：Replay-First（回放优先单路径）

让 `initial` 也直接通过 `replay` builder 生成，只是固定取最终步。

优点：

- 路径看起来最统一。

缺点：

- 让 `initial` 路径语义上依赖 `ReplayRuntime（回放运行时）`，概念耦合偏重。
- 对没有 replay artifacts（回放产物）但有 final activity artifacts（最终活动产物）的场景不够友好。

## 推荐方案

推荐 `方案 B：Validated Materialized Cache（带校验的物化缓存）`。

原因：

- 当前仓库已经具备 `artifact_contract_version（产物契约版本）` 和重物化机制。
- 当前剩余问题不在“有没有 builder”，而在“怎么证明缓存仍然代表当前输入”。
- 该方案既保留缓存效率，又最符合科研模式下的“唯一数据链 + 明确来源 + 可审计失效”原则。

## 正式数据链定义

`initial` 和 `replay` 共享同一条正式数据链：

`node_neuropil_occupancy.parquet`
`+ neuropil_truth_validation.json`
`+ node_index.parquet`
`+ step-scoped node activity（某一步神经元活动）`
`-> runtime_activity_artifacts._build_brain_view_payload_for_step(...)`
`-> brain-view payload`

其中：

- `initial` 取 `activity_trace.json + final_node_activity.npy` 的最终步
- `replay` 取 `ReplayRuntime` 当前步

差异只允许出现在“取哪一步”和“来源标签”，不允许出现在正式字段语义上。

## 共享响应契约

`/api/console/brain-view` 和 `/api/console/replay/brain-view` 必须共享这些字段：

- `artifact_contract_version`
- `semantic_scope`
- `view_mode`
- `mapping_mode`
- `activity_metric`
- `validation_passed`
- `graph_scope_validation_passed`
- `roster_alignment_passed`
- `mapping_coverage.neuropil_mapped_nodes`
- `region_activity[*].neuropil_id`
- `region_activity[*].raw_activity_mass`
- `region_activity[*].signed_activity`
- `top_nodes[*].neuropil_memberships`
- `formal_truth`

允许不同的字段只有：

- `step_id`
- `artifact_origin`

其中建议新增：

- `artifact_origin = initial-materialized | replay-live-step`

该字段只用于来源追踪，不引入第二条语义链。

## 缓存失效规则

`brain_view.json` 和 `timeline.json` 只能在同时满足以下条件时复用：

1. `brain_view.json` 和 `timeline.json` 都存在。
2. `artifact_contract_version` 与当前运行时代码一致。
3. 正式必需字段完整，且使用 `neuropil` 语义：
   - `semantic_scope = neuropil`
   - `mapping_mode = node_neuropil_occupancy`
   - `mapping_coverage.neuropil_mapped_nodes` 存在
   - `top_nodes[*].neuropil_memberships` 为列表
4. 所有依赖输入都早于缓存文件：
   - `activity_trace.json`
   - `final_node_activity.npy`
   - `summary.json`
   - `node_neuropil_occupancy.parquet`
   - `neuropil_truth_validation.json`
   - `node_index.parquet`

判断式应明确为：

`stale = contract invalid OR dependency missing OR dependency newer than artifact`

只要命中 `stale`，就必须重物化，而不是继续返回旧缓存。

## UI/API 可见性要求

为了让研究者能确认“当前显示的是不是唯一正式链”，UI/API 应显式暴露：

- `artifact_contract_version`
- `artifact_origin`
- `validation_passed`
- `graph_scope_validation_passed`
- `roster_alignment_passed`

推荐在右侧 `brain details（脑区详情）` 中增加一条简短 provenance（来源追踪）提示，例如：

- `Formal neuropil truth · contract v1 · initial-materialized`
- `Formal neuropil truth · contract v1 · replay-live-step`

这样无需打开调试工具也能识别当前展示来源。

## 测试策略

最少应覆盖这些情形：

1. 旧 `ROI` schema 存在时，`initial` 路径会重物化为新 `neuropil` schema。
2. 缓存 schema 正确但比 `final_node_activity.npy` 更旧时，`initial` 路径会重物化。
3. 缓存 schema 正确但比 `node_neuropil_occupancy.parquet` 更旧时，`initial` 路径会重物化。
4. `replay` 路径返回与 `initial` 一致的正式字段集合，并带 `artifact_origin`。
5. 真值文件缺失或校验失败时，两条路径都 fail-closed。

## 风险与约束

- 当前工作区已有对这 3 个文件的未提交修改：
  - `src/fruitfly/evaluation/runtime_activity_artifacts.py`
  - `src/fruitfly/ui/console_api.py`
  - `tests/ui/test_console_api.py`
  本设计不重写这些文件的方向，只把既有修正收敛为完整契约。

- `3D brain-view（3D 脑图）` 目前仍仅渲染 `brain shell（整脑外壳）`。即使本设计完成，也不会自动得到 `neuropil glow（脑区发光）` 或 `node mapping（神经元映射）`，那属于后续单独设计范围。

## 结论

当前仓库已经基本具备 `initial/replay brain-view` 统一所需的实现基础。下一步不是推翻现有实现，而是把：

- 共享 builder
- 共享 schema
- 严格 stale invalidation
- 明确 provenance

这四件事补成一套完整、可测试、可审计的正式契约。

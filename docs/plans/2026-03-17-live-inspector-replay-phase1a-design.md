# Live Inspector Replay Phase 1A Design

**Goal:** 在不引入假渲染路径的前提下，把当前 `Fly Body Live（果蝇身体实时区）` 从 `artifact player（归档播放器）` 收敛成一个 `replay-first inspector（回放优先观察器）`，让研究者能够按统一 `step（时间步）` 同步检查身体、脑图、时间轴和行为摘要。

**Relationship to existing docs:** 本文档是对 [2026-03-17-live-inspector-design.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md) 和 [2026-03-17-live-inspector-implementation.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-implementation.md) 的 Phase 1A 收敛版补充。原文档保留 `live / replay / artifact（实时 / 回放 / 归档）` 总方向；本文档只固定当前优先实现的 `replay-first` 范围与契约。

**Scope:** 只覆盖 `Experiment Console（实验控制台）` 中右下身体区的 `replay inspector（回放观察器）` 一阶段能力，以及它与右上脑图区、共享时间轴的联动契约。

---

## 1. Approved Product Decision

Phase 1A 采用 `replay-first（回放优先）`，而不是直接上 `live session runtime（实时会话运行时）`。

原因：

- `replay` 更符合当前科研平台的核心需求：可复现、可暂停、可逐步检查、可切换相机复盘同一步状态。
- `replay` 比 `live` 风险更低，不需要先解决长连接、实时帧流、复杂会话生命周期。
- 项目已经有真实 `summary.json / rollout.mp4 / activity trace（活动轨迹）` 基础，距离正式 `replay inspector` 更近。

Phase 1A 明确不做：

- 前端假 3D 果蝇渲染器
- 以 `mp4 seek（视频拖动）` 代替真实回放
- 多用户共享会话
- 自由相机系统
- 每步完整 `brain_view.json` 归档

---

## 2. Scientific Truth Path

Phase 1A 的身体回放必须继续沿真实物理路径工作：

`checkpoint（模型检查点）`
`-> policy wrapper（策略包装器）`
`-> flybody（果蝇身体与 MuJoCo 环境）`
`-> MuJoCo state（MuJoCo 物理状态）`
`-> MuJoCo render（MuJoCo 渲染）`
`-> replay frame（回放帧）`

这里的关键变化是：

- `rollout.mp4` 继续保留，但只作为 `artifact（归档产物）`
- 回放主查看面不再是视频播放器
- 回放主查看面必须来自 `state_traces.npz（状态轨迹归档）` 的按步状态恢复与重渲染

这条路径的意义是：同一步状态下可以切不同相机，不会被预先烘焙的视频角度锁死。

---

## 3. Replay Artifact Contract

一次正式闭环评估在 Phase 1A 结束后应当写出以下主产物：

- `summary.json`
- `rollout.mp4`
- `session.json`
- `state_traces.npz`
- `neural_traces.npz`
- `events.jsonl`

语义分层如下：

### 3.1 主产物

这些文件构成 `replay inspector（回放观察器）` 的正式 SoT（单一事实来源）：

- `session.json`
  - 会话元数据
- `state_traces.npz`
  - 身体物理状态主真值
- `neural_traces.npz`
  - 每步神经活动主真值
- `events.jsonl`
  - 稀疏事件流

### 3.2 派生产物

以下文件继续存在，但不再是 replay 主真值：

- `brain_view.json`
- `timeline.json`

它们应从主产物动态派生或按需物化，用于 UI 消费，而不是用来反向定义 replay 真相。

### 3.3 session.json

Phase 1A 必需字段：

- `session_id`
- `task`
- `checkpoint`
- `compiled_graph_dir`
- `created_at`
- `default_camera`
- `steps_requested`
- `steps_completed`
- `terminated_early`
- `quality`

### 3.4 state_traces.npz

Phase 1A 必需字段：

- `step_id[T]`
- `sim_time[T]`
- `qpos[T, nq]`
- `qvel[T, nv]`
- `ctrl[T, nu]`
- `reward[T]`
- `terminated[T]`
- `body_upright[T]`
- `forward_velocity[T]`

### 3.5 neural_traces.npz

Phase 1A 必需字段：

- `step_id[T]`
- `node_activity[T, N]`
- `afferent_activity[T]`
- `intrinsic_activity[T]`
- `efferent_activity[T]`

其中：

- `node_activity[T, N]` 是脑活动正式主真值
- 三个 partition summary（分区摘要）只是低成本便捷取数层

### 3.6 events.jsonl

Phase 1A 必需事件：

- `rollout_started`
- `rollout_completed`
- `terminated_early`
- `camera_change`

---

## 4. Brain / Body Synchronization Model

Phase 1A 的核心约束是：

**整个 replay session（回放会话）只有一个 `global shared step cursor（全局共享步游标）`。**

这意味着：

- 身体区不拥有独立 step
- 脑图区不拥有独立 step
- 时间轴不拥有独立 step

它们全部订阅同一个 `current_step`。

同一步下：

- 身体区恢复 `state_traces.npz` 的物理状态并重渲染
- 脑图区读取 `neural_traces.npz` 中 `node_activity[t]`
- 脑图区再结合正式 [node_neuropil_occupancy.parquet](/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783/node_neuropil_occupancy.parquet) 动态聚合出该步 `brain_view`
- 行为摘要读取该步指标
- 时间轴高亮该步

任何控制源都只能修改同一个共享 `current_step`：

- 时间轴拖动
- `prev / next step`
- 播放自动推进
- 未来快捷键

---

## 5. Brain Replay Strategy

Phase 1A 的脑图联动采用：

**`dynamic aggregation（动态聚合）`**

而不是为每一步提前持久化完整 `brain_view.json`。

正式链为：

`node_activity[t]`
`+ node_neuropil_occupancy`
`-> brain_view(step=t)`

这样做的原因：

- 保持脑图 SoT 简洁
- 不引入另一层“每步脑区缓存真值”
- 若未来 `neuropil mapping（神经纤维区映射）` 更新，不必重写 replay 主产物

如果后面需要性能优化，可以引入缓存，但缓存必须明确是 `derived cache（派生缓存）`，不是主产物。

---

## 6. Replay Frame Strategy

Phase 1A 的身体回放不走 `mp4 seek`，而走：

**`on-demand re-render（按步即时重渲染）`**

即：

1. replay 选中 `step t`
2. 后端从 `state_traces.npz` 取出 `qpos/qvel/ctrl`
3. 把 `flybody` 环境恢复到该步状态
4. 用当前 `camera preset（相机预设）` 重渲染一帧
5. 返回身体区显示

这样做的直接收益是：

- 同一步可切不同相机
- replay 不再退化成视频播放器
- 身体区成为真正 inspector surface（观察面）

---

## 7. Camera Presets

Phase 1A 只支持小而明确的科研预设集，不做自由相机。

固定预设：

- `follow`
  - 默认跟随视角
  - 用于整体行为观察
- `side`
  - 侧视
  - 用于步态节律、摆腿、身体起伏
- `top`
  - 俯视
  - 用于路径、方向漂移、转向偏差
- `front-quarter`
  - 前侧 45 度
  - 用于姿态、稳定性、朝向变化

额外控制：

- `reset view`

规则：

- 相机目标始终锁到 fly root / body center（果蝇身体中心）
- Phase 1A 不做自由拖拽相机

---

## 8. Replay Controls

Phase 1A 的回放控制采用“比播放器强、比调试器轻”的控制集：

- `play / pause`
- `prev step`
- `next step`
- `step slider`
- `step counter`
- `speed select`
  - `0.25x / 0.5x / 1x / 2x`
- `camera preset select`
- `reset view`

可选快捷键：

- `Space`
- `← / →`

不做：

- 书签
- 区间循环
- 双 run 对比
- 事件跳转面板

---

## 9. Replay Layout

Phase 1A 采用 `dual-focus scientific layout（脑 / 身体双焦点科研布局）`。

保持当前实验页骨架：

- 左侧：实验参数与状态
- 右上：脑图
- 右下：身体观察器

在 replay 模式下做三点强化：

1. 右下身体区升级成真正 inspector viewport（观察视口）
2. `timeline（时间轴）` 升级成共享一级组件
3. 脑图和身体区都显示统一 replay 状态

也就是说：

- 不重做成整页 takeover（观察器接管页）
- 不让脑图区或身体区变成另一方的附属
- 共享 timeline 明确表达“同一步驱动脑 / 身体 / 摘要”

---

## 10. Phase Split

### Phase 1A

目标：

- artifact-backed replay inspector（基于归档产物的回放观察器）
- 无需 live streaming（实时流）
- 支持真正按步回放、按步脑图联动、按步切相机

### Phase 1B

后续再补：

- `live session runtime`
- 实时帧 transport（帧传输）
- 更复杂会话生命周期
- 可能的缓存/性能优化

这个拆分能保证：

- 先把科研复盘能力做实
- 再做实时观察体验

---

## 11. Acceptance Criteria

Phase 1A 完成时，至少应满足：

- 研究者能从一次真实 eval artifact 启动 replay
- 时间轴、脑图、身体区共享同一个 `step`
- 切换 `camera preset` 不改变当前 step
- 脑图来自 `node_activity[t] + node_neuropil_occupancy` 的动态聚合
- 身体区来自该步 MuJoCo 状态恢复后的即时重渲染
- `rollout.mp4` 仍可下载或查看，但不再是主观察面
- 当 replay 主产物缺失时，UI 明确返回 `unavailable`，不使用 mock fallback（模拟回退）

---

## 12. Non-Goals

Phase 1A 明确不是：

- 实时流媒体平台
- 多用户共享观察会话
- 身体调试器全集
- 前端自由 3D 编辑器
- 每步全量脑图缓存仓库

一句话总结：

**Phase 1A 要做的是“科学可复盘的共享 step 回放观察器”，不是“更高级的视频播放器”，也不是“重型实时平台”。**

# Neural Console UI Runtime Note

**Purpose:** Freeze the Phase 1 `neural console（神经控制台）` runtime split so later UI work does not drift into ad-hoc architecture.

## Fixed Runtime Split

The V1 runtime is intentionally split into two layers:

- **Frontend:** `React（前端框架） + shadcn/ui（组件体系） + react-three-fiber（React 的 Three.js 3D 渲染层）`
- **Backend:** existing Python evaluation/control pipeline in this repository

The frontend is responsible for:

- rendering the left-side `experiment console（实验控制台）`
- rendering the top pipeline state bar
- rendering the right-top 3D brain view
- rendering the right-bottom body video panel
- showing shared timeline, logs, and summaries

The backend is responsible for:

- loading `checkpoint（模型检查点）`
- loading `compiled graph（训练编译图）`
- applying environment and sensory parameter bundles
- running `flybody（果蝇身体与 MuJoCo 物理环境）` closed-loop rollout
- computing read-only neural/behavior summaries
- producing `summary.json` and `MP4（视频文件）` artifacts

## UI/Backend Contract

The UI backend should expose only read-only experiment surfaces. The contract must be limited to:

- `checkpoint_path`
- `compiled_graph_dir`
- `environment_physics`
- `sensory_inputs`
- `closed_loop_summary`
- `brain_view_payload`
- `timeline_payload`
- `rendered_frame` or recorded video artifact path

The runtime must not expose:

- editable `59`-dimensional action vectors
- direct joint overrides
- hidden state mutation controls intended for manual steering

## Environment Boundary

The backend control path continues to run from Python-side evaluation code and may use the dedicated `.venv-flybody` environment for body rollout. The frontend should treat that path as an execution service, not as a place to embed UI logic.

## Phase 1 Principle

The UI exists to visualize:

`Environment / Sensory Input（环境 / 感觉输入）`
`-> Afferent（输入神经元）`
`-> Whole-Brain（全脑模型）`
`-> Efferent（输出神经元）`
`-> Decoder（动作解码器）`
`-> Body（果蝇身体）`

It must not behave like a remote-control surface for body motion.

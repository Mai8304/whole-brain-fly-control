# Fruitfly

Full-graph fruit fly connectome control research workspace.

## Installation

```bash
pip install -e .
pip install -e '.[flywire]'
pip install -e '.[ui]'
pip install -e '.[flywire,dev]'
```

## Neural Console API

The read-only `neural console（神经控制台）` backend serves:

- `session（控制台会话）`
- `pipeline（执行流程）`
- `brain-view（脑图载荷）`
- `roi-assets（脑区资产包）`
- `timeline（共享时间轴）`
- `summary（闭环评估摘要）`
- `video（闭环视频）`

The current formal brain-region truth route is:

- `FlyWire official route（FlyWire 官方路线）`
- `neuropil（神经纤维区）` semantics, not generic `ROI（脑区）`
- `FlyWire 783` official release files as the raw truth source
- formal truth artifacts:
  - `synapse_neuropil_assignment.parquet`
  - `node_neuropil_occupancy.parquet`
- official validation against:
  - `per_neuron_neuropil_count_pre_783.feather`
  - `per_neuron_neuropil_count_post_783.feather`

Run it against an existing compiled graph and evaluation artifact directory:

```bash
./.venv-flywire/bin/python scripts/import_flywire_783_neuropil_release.py \
  --source-dir /path/to/flywire-783-release \
  --output-dir data/raw/flywire_783_neuropil

./.venv-flywire/bin/python scripts/import_flywire_brain_mesh.py \
  --output-dir outputs/ui-assets/flywire_brain_v141

./.venv-flywire/bin/python scripts/import_flywire_roi_meshes.py \
  --output-dir outputs/ui-assets/flywire_roi_meshes_v1

./.venv-flywire/bin/python scripts/build_synapse_roi_assignment.py \
  --compiled-graph-dir outputs/compiled/flywire_public_full_v783 \
  --raw-source-dir data/raw/flywire_783_neuropil \
  --cache-dir outputs/compiled/flywire_public_full_v783/synapse_neuropil_batches \
  --resume \
  --output-path outputs/compiled/flywire_public_full_v783/synapse_neuropil_assignment.parquet

./.venv-flywire/bin/python scripts/build_node_neuropil_occupancy.py \
  --compiled-graph-dir outputs/compiled/flywire_public_full_v783 \
  --synapse-assignment-path outputs/compiled/flywire_public_full_v783/synapse_neuropil_assignment.parquet \
  --output-path outputs/compiled/flywire_public_full_v783/node_neuropil_occupancy.parquet

./.venv-flywire/bin/python scripts/validate_neuropil_truth.py \
  --raw-source-dir data/raw/flywire_783_neuropil \
  --occupancy-path outputs/compiled/flywire_public_full_v783/node_neuropil_occupancy.parquet \
  --json
```

The current formal `neuropil truth（神经纤维区真值）` route distinguishes:

- `brain shell asset（整脑外壳资产）`
- `neuropil asset pack（神经纤维区资产包）`

The asset-pack layout is:

- `manifest.json`
- `roi_manifest.json`
- `node_neuropil_occupancy.parquet`
- `roi_mesh/<roi_id>.glb`

`node_neuropil_occupancy.parquet` is a compiled offline occupancy artifact derived from formal synapse-level truth. It is not inferred by the UI at runtime.
`scripts/build_synapse_roi_assignment.py` compiles `synapse_neuropil_assignment.parquet` from the official `flywire_synapses_783.feather` raw source.
`scripts/build_node_neuropil_occupancy.py` aggregates that synapse-level truth into node-level neuropil occupancy.
`scripts/validate_neuropil_truth.py` must pass against the official `per_neuron_neuropil_count_*_783.feather` files before the UI or API is allowed to expose formal neuropil activity.
`scripts/import_flywire_roi_meshes.py` exports the V1 ROI geometry from `fafbseg.flywire.get_neuropil_volumes（FlyWire 官方 Python 工具中的脑区几何入口）`, which ships a `FlyWire / FAFB14.1`-aligned neuropil mesh archive locally inside the `fafbseg` package.
If `--roi-mesh-dir` is provided, it should contain real `<ROI_ID>.glb` files for the V1 ROI set. If omitted, the builder currently emits placeholder ROI mesh files.

The runtime asset-pack / API layer now enforces one formal activity chain:

- `brain-view（脑图载荷）` only materializes formal neuropil activity from validated `node_neuropil_occupancy.parquet`
- `graph-scoped validation（运行图范围校验）` and `proofread roster alignment（官方校对名录对齐）` are carried as separate states
- grouped `AL / LH / LAL` labels in the V1 console are `display transforms（显示变换）`, not raw formal truth IDs

This means the commands above are now the full formal path for neuropil truth generation, validation, and read-only runtime exposure.

For the `React（前端框架） + shadcn/ui（组件体系）` console shell:

```bash
cd apps/neural-console
pnpm install
pnpm dev
```

During local development, `Vite（前端构建工具）` proxies `/api` to `http://127.0.0.1:8000`.
If the API is running elsewhere, set `VITE_CONSOLE_API_BASE_URL` before starting the frontend.
By default the console runs in `research strict mode（科研严格模式）`: if the live API is unavailable, or if formal `neuropil truth（神经纤维区真值）` artifacts are missing or unvalidated, the UI and API return unavailable state instead of falling back to mock data. Set `VITE_ENABLE_MOCK_FALLBACK=true` only for explicit UI development work.

## Compiled Graph Standard

The preferred graph path is now:

`snapshot（本地快照）`
`-> compiled graph（训练编译图）`
`-> train_il.py`

Compiled graph artifacts are written into a standard directory containing:

- `manifest.json`
- `config.json`
- `node_index.parquet`
- `edge_index.pt`
- `io_masks.pt`
- `graph_stats.json`

The preferred training interface is:

```bash
python3 scripts/compile_graph.py \
  --snapshot-dir outputs/snapshots/flywire_public_full_v783 \
  --output-dir outputs/compiled/flywire_public_full_v783

python3 scripts/train_il.py \
  --dataset data/datasets/walking_il/straight_smoke.jsonl \
  --compiled-graph-dir outputs/compiled/flywire_public_full_v783 \
  --output-dir outputs/train/full_graph_straight_smoke
```

After the first smoke run, the recommended next dataset step is:

- `data/datasets/walking_il/straight_v1.jsonl`
- `episodes=3`
- `max_steps=128`

This expanded dataset keeps the same core training fields and adds lightweight analysis metadata:

- `episode_id`
- `step_id`
- `task`

## flybody Straight-Walking Slice

The first `flybody（果蝇身体与 MuJoCo 物理环境）` behavior slice is:

`straight walking（稳定直行）`
`-> expert rollout（专家轨迹导出）`
`-> IL dataset（模仿学习数据集）`
`-> train_il.py`

This export should run from a dedicated environment, not the main project environment. The dataset file is then written back into this repository and consumed by the main training stack.

In the current repository state, `scripts/build_il_dataset.py` provides the export contract and CLI, but the real `flybody` expert backend still has to be run from that dedicated environment. If `flybody` is unavailable, the command exits with a short error instead of a full stack trace.

Before wiring expert rollout export, probe the dedicated `flybody` environment first:

```bash
python3 scripts/probe_flybody.py
```

Successful probe means:

- `flybody` imports
- `walk_imitation` environment can be created
- the environment can `reset`
- the environment can `step` once with a 59-dimensional action

To export the next-step straight-walking dataset:

```bash
./.venv-flybody/bin/python scripts/build_il_dataset.py \
  --output data/datasets/walking_il/straight_v1.jsonl \
  --episodes 3 \
  --max-steps 128 \
  --policy-dir outputs/flybody-data/trained-fly-policies
```

## Closed-Loop Evaluation

The first real closed-loop evaluation is engineering-focused:

`checkpoint（模型检查点）`
`-> model loader（模型加载器）`
`-> policy wrapper（策略包装器）`
`-> flybody rollout（闭环展开）`

Run it from the dedicated `flybody` environment:

```bash
./.venv-flybody/bin/python scripts/eval_flybody_closed_loop.py \
  --checkpoint outputs/train/full_graph_straight_v1/checkpoints/epoch_0001.pt \
  --compiled-graph-dir outputs/compiled/flywire_public_full_v783 \
  --task straight_walking \
  --max-steps 64 \
  --output-dir outputs/eval/full_graph_straight_v1
```

The evaluation writes:

- terminal JSON
- `outputs/eval/<run>/summary.json`

The first summary focuses on engineering stability, including:

- `steps_completed`
- `terminated_early`
- `has_nan_action`
- `mean_action_norm`
- `final_reward`
- `final_heading_delta`

## FlyWire Read-Only Verification

This repository treats `FlyWire（果蝇连接组平台）` read-only access as a Phase 1 milestone.

Install the `flywire extras（FlyWire 可选依赖组）`, then verify the standard local secret against the `public dataset（公开数据集）`:

```bash
python3 scripts/verify_flywire_readonly.py
python3 scripts/verify_flywire_readonly.py --json
```

`fafbseg（FlyWire Python 工具）` expects the user token at:

```text
~/.cloudvolume/secrets/cave-secret.json
```

The verification is considered successful when:

- `status=ok`
- `dataset=public`
- `materialization_count > 0`
- `resolved_roots > 0`

## FlyWire Dry-Run Snapshot Export

The first real `snapshot export（本地快照导出）` milestone uses the final snapshot schema with a constrained real export:

- `seed_strategy=readonly_coords`
- `max_hops=2`
- `max_nodes=5000`

Run the dry-run exporter:

```bash
python3 scripts/export_flywire_snapshot.py \
  --snapshot-id flywire_public_dry_run \
  --output-root outputs/snapshots \
  --json
```

This writes:

- `manifest.yaml`
- `raw/nodes.parquet`
- `raw/edges.parquet`
- `raw/flow_labels.parquet`
- `normalized/nodes.parquet`
- `normalized/edges.parquet`
- `normalized/partitions.parquet`
- `normalized/stats.json`

Then compile the normalized snapshot:

```bash
python3 scripts/compile_graph.py \
  --snapshot-dir outputs/snapshots/flywire_public_dry_run \
  --output-dir outputs/compiled/flywire_public_dry_run
```

## Phase 1 Runbook

```bash
python3 scripts/export_flywire_snapshot.py \
  --snapshot-id flywire_public_dry_run \
  --output-root outputs/snapshots
python3 scripts/compile_graph.py \
  --snapshot-dir outputs/snapshots/flywire_public_dry_run \
  --output-dir outputs/compiled/graph
python3 scripts/build_il_dataset.py \
  --output data/datasets/walking_il/dataset.jsonl \
  --episodes 1 \
  --max-steps 32
python3 scripts/train_il.py \
  --dataset data/datasets/walking_il/dataset.jsonl \
  --output-dir outputs/train/walking_il \
  --compiled-graph-dir outputs/compiled/graph
python3 scripts/eval_walking.py --headings 0.0 0.1 0.3
```

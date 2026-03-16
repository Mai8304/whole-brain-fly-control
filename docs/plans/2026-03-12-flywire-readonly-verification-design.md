# FlyWire Read-Only Verification Design

> Status: approved on 2026-03-12
> Scope: first real `FlyWire（果蝇连接组平台）` data-access milestone

## Goal

Add a minimal, repeatable, read-only verification step that proves the local machine can access `FlyWire` through a standard user secret, before any snapshot export or training data ingestion begins.

## Why This Exists

The current repository has a working Phase 1 training skeleton, but it still uses stub data-entry points for `compile_graph.py` and `build_il_dataset.py`. The project needs a real upstream data-access milestone before it can claim end-to-end progress toward a full digital fly workflow.

## Approved Decisions

- The verification target is `public dataset（公开数据集）`, not production datasets.
- The verification stack uses `fafbseg（FlyWire Python 工具）`, not raw `cloudvolume` or `caveclient`.
- `FlyWire` dependencies are installed through `flywire extras（FlyWire 可选依赖组）`, not the core runtime.
- Business logic lives in `src/fruitfly/snapshot/`.
- `scripts/` only contains a thin CLI entrypoint.
- The verification script counts as a Phase 1 milestone.

## Dependency Strategy

Optional dependency groups are split by capability boundary:

- `flywire`
  - `fafbseg`
  - `pyarrow（Parquet 读写库）`
- `embodiment`
  - reserved for `flybody（果蝇身体与 MuJoCo 物理环境）` and `MuJoCo（物理引擎）`
- `dev`
  - test and development tooling

This keeps the core training environment smaller while allowing data-ingest and embodied-runtime dependencies to evolve independently.

## Verification Path

The minimal verification path is:

1. Load the standard local secret from `~/.cloudvolume/secrets/cave-secret.json`
2. Explicitly set the dataset to `public`
3. Query available `materialization（静态版本）` metadata
4. Run a read-only `locs_to_segments（坐标转 root ID）` query against official example coordinates
5. Return a small success or failure summary without printing the token

## Output Contract

The verification result must include:

- `status`
- `dataset`
- `materialization_count`
- `latest_materialization`
- `query_points`
- `resolved_roots`

Failure output must additionally include:

- `error_type`
- `message`

## Acceptance Criteria

The milestone is complete when:

- the machine can import `fafbseg`
- the standard local secret is accepted by `FlyWire`
- `public` materializations can be listed
- the example coordinate query resolves at least one root ID
- the result can be emitted in stable text and JSON formats
- no token is printed or written into repository files

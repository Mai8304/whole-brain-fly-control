# FlyWire Dry-Run Snapshot Export Design

> Status: approved on 2026-03-12
> Scope: first real snapshot-export milestone after read-only verification

## Goal

Add a real `snapshot export（本地快照导出）` path that uses the final repository snapshot schema, but starts with a small real `dry run（试导出）` before attempting a full-brain export.

## Why This Exists

The project now has:

- a working Phase 1 training skeleton
- a real `FlyWire（果蝇连接组平台）` read-only verification milestone

What it still does not have is a real exported snapshot that can feed the `normalized（标准化层）` and `graph compiler（图编译层）` path. This design bridges that gap without introducing a second temporary export format.

## Approved Decisions

- The exporter uses the final snapshot layout from day one.
- The first execution is a real `dry run` against `FlyWire`, not a fake dataset.
- The first run is constrained by:
  - `seed from readonly coords（种子来自只读验证坐标）`
  - `max_hops=2`
  - `max_nodes=5000`
- The exporter must allow `--seed-root-id` to override the default seed source.
- The dry run must write the same artifact types the final exporter will use:
  - `manifest.yaml`
  - `nodes.parquet`
  - `edges.parquet`
  - `flow_labels.parquet`

## Export Strategy

The exporter should not have separate “toy” and “real” modes. Instead, it should use one code path with tunable limits:

- `dry run`
  - seed from a verified real root ID
  - `max_hops=2`
  - `max_nodes=5000`
- `full export`
  - same logic
  - relaxed or removed limits

This keeps the export logic faithful to the final system while reducing the debugging surface of the first real run.

## Seed Strategy

The first dry run uses the first non-zero `root ID（根神经元 ID）` returned from the same coordinates used by the read-only verification path.

Default behavior:

1. resolve the verification coordinates through `locs_to_segments（坐标转 root ID）`
2. select the first non-zero root ID
3. use it as the export seed

Override behavior:

- `--seed-root-id` bypasses coordinate-based seed resolution

## Neighborhood Expansion Strategy

The dry run uses a bounded neighborhood expansion:

- directional expansion from the seed root
- `max_hops=2`
- `max_nodes=5000`

The key requirement is not biological completeness; it is exporter correctness with a real connected subgraph and the final artifact schema.

## Output Layout

The dry run writes into the same snapshot layout used by the broader Phase 1 design:

```text
data/connectome/snapshots/<snapshot_id>/
  manifest.yaml
  raw/
    nodes.parquet
    edges.parquet
    flow_labels.parquet
  normalized/
    nodes.parquet
    edges.parquet
    partitions.parquet
    stats.json
```

The first dry run may keep `compiled/` out of scope if the repository already compiles from normalized tables through a separate step, but the normalized output must be sufficient for that next stage.

## Acceptance Criteria

The dry-run snapshot milestone is complete when:

- a real seed root ID is derived from the verified `FlyWire` path or provided explicitly
- the exporter writes a snapshot directory with:
  - `manifest.yaml`
  - `nodes.parquet`
  - `edges.parquet`
  - `flow_labels.parquet`
- exported node count is greater than zero
- exported edge count is greater than zero
- exported node count does not exceed `5000`
- the normalized tables can be validated by the repository schema checks
- the existing `graph compiler` can load the dry-run snapshot and produce a non-empty graph result

## Non-Goals

- no full-brain export yet
- no `flybody（果蝇身体与 MuJoCo 物理环境）` coupling in the exporter
- no `PPO fine-tune（强化学习微调）`
- no region-specific or behavior-specific filtering in the first dry run

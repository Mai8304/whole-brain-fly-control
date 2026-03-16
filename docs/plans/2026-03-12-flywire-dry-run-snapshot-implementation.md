# FlyWire Dry-Run Snapshot Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a real `FlyWire（果蝇连接组平台）` snapshot exporter that writes the final snapshot schema while first running as a constrained `dry run（试导出）` using a real seed root and a `5000`-node budget.

**Architecture:** Reuse the read-only verification path to resolve a real default seed root, then expand a bounded neighborhood through one export pipeline that can later scale to a full-brain snapshot. Keep export logic in `src/fruitfly/snapshot/`, write final-format artifacts into `data/connectome/snapshots/`, and keep the CLI in `scripts/` as a thin wrapper over library code.

**Tech Stack:** Python 3.13 for core code and tests, Python 3.12 `.venv-flywire` for real FlyWire execution, `fafbseg`, `pyarrow`, `PyYAML`, `pytest`

---

### Task 1: Add Snapshot Export Config and Contract Tests

**Files:**
- Create: `configs/snapshot/flywire_dry_run.yaml`
- Create: `tests/snapshot/test_export_config.py`
- Modify: `README.md`

**Step 1: Write the failing test**

```python
from pathlib import Path

import yaml


def test_dry_run_snapshot_config_defaults() -> None:
    payload = yaml.safe_load(Path("configs/snapshot/flywire_dry_run.yaml").read_text(encoding="utf-8"))

    assert payload["dataset"] == "public"
    assert payload["max_hops"] == 2
    assert payload["max_nodes"] == 5000
    assert payload["seed_strategy"] == "readonly_coords"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/snapshot/test_export_config.py -q`
Expected: FAIL because the dry-run config file does not exist yet.

**Step 3: Write minimal implementation**

Create `configs/snapshot/flywire_dry_run.yaml` with:

- `dataset: public`
- `seed_strategy: readonly_coords`
- `max_hops: 2`
- `max_nodes: 5000`
- `allow_seed_override: true`

Update `README.md` with one short section naming the dry-run export milestone and its limits.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/snapshot/test_export_config.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add configs/snapshot/flywire_dry_run.yaml README.md tests/snapshot/test_export_config.py
git commit -m "chore: add dry-run snapshot export config"
```

### Task 2: Define Export Request and Export Result Contracts

**Files:**
- Create: `src/fruitfly/snapshot/exporter.py`
- Modify: `src/fruitfly/snapshot/__init__.py`
- Create: `tests/snapshot/test_exporter_contracts.py`

**Step 1: Write the failing test**

```python
def test_snapshot_export_request_defaults() -> None:
    from fruitfly.snapshot.exporter import SnapshotExportRequest

    request = SnapshotExportRequest(snapshot_id="dry_run")

    assert request.dataset == "public"
    assert request.max_hops == 2
    assert request.max_nodes == 5000
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/snapshot/test_exporter_contracts.py -q`
Expected: FAIL because the exporter module does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `SnapshotExportRequest`
- `SnapshotExportResult`
- `build_snapshot_paths(snapshot_id)`

The request contract must support:

- `snapshot_id`
- `dataset`
- `seed_root_id`
- `max_hops`
- `max_nodes`
- `seed_strategy`

The result contract must report:

- `snapshot_dir`
- `seed_root_id`
- `node_count`
- `edge_count`
- `status`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/snapshot/test_exporter_contracts.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/snapshot/exporter.py src/fruitfly/snapshot/__init__.py tests/snapshot/test_exporter_contracts.py
git commit -m "feat: add snapshot export contracts"
```

### Task 3: Implement Seed Resolution from the Read-Only Verification Path

**Files:**
- Modify: `src/fruitfly/snapshot/exporter.py`
- Modify: `src/fruitfly/snapshot/flywire_verify.py`
- Create: `tests/snapshot/test_seed_resolution.py`

**Step 1: Write the failing test**

```python
def test_seed_resolution_uses_first_nonzero_root() -> None:
    from fruitfly.snapshot.exporter import resolve_seed_root_id

    class FakeFlyWire:
        def locs_to_segments(self, coords):
            return [0, 720575940000000123]

    root_id = resolve_seed_root_id(
        flywire_client=FakeFlyWire(),
        coords=[[1, 2, 3], [4, 5, 6]],
    )

    assert root_id == 720575940000000123
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/snapshot/test_seed_resolution.py -q`
Expected: FAIL because seed-resolution logic does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `resolve_seed_root_id(...)`
- support for explicit `seed_root_id`
- default fallback to `DEFAULT_PUBLIC_COORDS`
- clear failure on all-zero or empty results

Keep the function injectable with a fake `flywire_client` so it remains fully testable without network access.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/snapshot/test_seed_resolution.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/snapshot/exporter.py src/fruitfly/snapshot/flywire_verify.py tests/snapshot/test_seed_resolution.py
git commit -m "feat: add snapshot seed resolution"
```

### Task 4: Implement Dry-Run Neighborhood Export with Final Artifact Names

**Files:**
- Modify: `src/fruitfly/snapshot/exporter.py`
- Create: `tests/snapshot/test_exporter_dry_run.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_export_dry_run_writes_required_files(tmp_path: Path) -> None:
    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot_dry_run

    class FakeFlyWire:
        def get_neighborhood(self, seed_root_id, max_hops, max_nodes):
            return {
                "nodes": [
                    {"source_id": 1, "dataset_version": "public", "hemisphere": "unknown", "flow_role": "intrinsic", "is_active": True},
                    {"source_id": 2, "dataset_version": "public", "hemisphere": "unknown", "flow_role": "efferent", "is_active": True},
                ],
                "edges": [
                    {"pre_id": 1, "post_id": 2, "synapse_count": 3, "is_active": True},
                ],
                "flow_labels": [
                    {"source_id": 1, "flow_role": "intrinsic"},
                    {"source_id": 2, "flow_role": "efferent"},
                ],
            }

    request = SnapshotExportRequest(snapshot_id="dry_run_test")
    result = export_snapshot_dry_run(
        request=request,
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
        seed_root_id=1,
    )

    assert result.status == "ok"
    assert (result.snapshot_dir / "manifest.yaml").exists()
    assert (result.snapshot_dir / "raw" / "nodes.parquet").exists()
    assert (result.snapshot_dir / "raw" / "edges.parquet").exists()
    assert (result.snapshot_dir / "raw" / "flow_labels.parquet").exists()
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/snapshot/test_exporter_dry_run.py -q`
Expected: FAIL because export logic does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `export_snapshot_dry_run(...)`
- creation of snapshot directory layout
- manifest writing
- `raw/nodes.parquet`
- `raw/edges.parquet`
- `raw/flow_labels.parquet`

If the real `FlyWire` neighborhood API is not yet finalized, keep the exporter split so a fake provider can supply:

- `nodes`
- `edges`
- `flow_labels`

and the file-writing logic is already production-ready.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/snapshot/test_exporter_dry_run.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/snapshot/exporter.py tests/snapshot/test_exporter_dry_run.py
git commit -m "feat: add dry-run snapshot export"
```

### Task 5: Normalize the Dry-Run Export and Validate It Against Existing Schema Checks

**Files:**
- Modify: `src/fruitfly/snapshot/exporter.py`
- Create: `tests/snapshot/test_exporter_normalized.py`

**Step 1: Write the failing test**

```python
def test_export_dry_run_writes_normalized_tables(tmp_path) -> None:
    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot_dry_run
    from fruitfly.snapshot.schema import validate_nodes_columns, validate_edges_columns
    import pyarrow.parquet as pq

    class FakeFlyWire:
        def get_neighborhood(self, seed_root_id, max_hops, max_nodes):
            return {
                "nodes": [
                    {"source_id": 1, "dataset_version": "public", "hemisphere": "unknown", "flow_role": "intrinsic", "is_active": True},
                ],
                "edges": [],
                "flow_labels": [
                    {"source_id": 1, "flow_role": "intrinsic"},
                ],
            }

    result = export_snapshot_dry_run(
        request=SnapshotExportRequest(snapshot_id="normalized_test"),
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
        seed_root_id=1,
    )

    node_columns = set(pq.read_table(result.snapshot_dir / "normalized" / "nodes.parquet").column_names)
    edge_columns = set(pq.read_table(result.snapshot_dir / "normalized" / "edges.parquet").column_names)

    assert validate_nodes_columns(node_columns)
    assert validate_edges_columns(edge_columns)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/snapshot/test_exporter_normalized.py -q`
Expected: FAIL because normalized export outputs do not exist yet.

**Step 3: Write minimal implementation**

Add normalized output generation:

- `normalized/nodes.parquet`
- `normalized/edges.parquet`
- `normalized/partitions.parquet`
- `normalized/stats.json`

Ensure the existing schema validators can read the resulting columns without special cases.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/snapshot/test_exporter_normalized.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/snapshot/exporter.py tests/snapshot/test_exporter_normalized.py
git commit -m "feat: add normalized dry-run snapshot outputs"
```

### Task 6: Add CLI Entry Point and Real Dry-Run Validation

**Files:**
- Create: `scripts/export_flywire_snapshot.py`
- Modify: `README.md`
- Create: `tests/scripts/test_export_flywire_snapshot.py`

**Step 1: Write the failing test**

```python
def test_export_cli_accepts_dry_run_flags(capsys, monkeypatch) -> None:
    from fruitfly.snapshot import exporter

    monkeypatch.setattr(
        exporter,
        "export_snapshot_dry_run",
        lambda **_: exporter.SnapshotExportResult(
            snapshot_dir=None,
            seed_root_id=123,
            node_count=10,
            edge_count=9,
            status="ok",
        ),
    )

    exit_code = exporter.main(["--snapshot-id", "dry_run", "--max-hops", "2", "--max-nodes", "5000"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "status=ok" in captured.out
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/scripts/test_export_flywire_snapshot.py -q`
Expected: FAIL because the CLI does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- thin CLI wrapper in `scripts/export_flywire_snapshot.py`
- `main(argv=None)` inside `src/fruitfly/snapshot/exporter.py`
- support for:
  - `--snapshot-id`
  - `--seed-root-id`
  - `--max-hops`
  - `--max-nodes`
  - `--output-root`
  - `--json`

Then run the real dry run with the dedicated FlyWire environment:

```bash
.venv-flywire/bin/python scripts/export_flywire_snapshot.py \
  --snapshot-id flywire_dry_run \
  --max-hops 2 \
  --max-nodes 5000 \
  --json
```

Expected manual result:

- `status=ok`
- `node_count > 0`
- `edge_count > 0`
- `node_count <= 5000`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/scripts/test_export_flywire_snapshot.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/export_flywire_snapshot.py src/fruitfly/snapshot/exporter.py tests/scripts/test_export_flywire_snapshot.py README.md
git commit -m "feat: add flywire dry-run snapshot cli"
```

### Task 7: Prove the Dry-Run Snapshot Compiles into a Non-Empty Graph

**Files:**
- Modify: `tests/integration/test_smoke_configs.py`
- Create: `tests/integration/test_dry_run_snapshot_compile.py`

**Step 1: Write the failing test**

```python
def test_compiler_accepts_dry_run_snapshot(tmp_path) -> None:
    from fruitfly.graph.compiler import compile_snapshot
    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot_dry_run
    import pyarrow.parquet as pq

    class FakeFlyWire:
        def get_neighborhood(self, seed_root_id, max_hops, max_nodes):
            return {
                "nodes": [
                    {"source_id": 1, "dataset_version": "public", "hemisphere": "unknown", "flow_role": "afferent", "is_active": True},
                    {"source_id": 2, "dataset_version": "public", "hemisphere": "unknown", "flow_role": "efferent", "is_active": True},
                ],
                "edges": [
                    {"pre_id": 1, "post_id": 2, "synapse_count": 1, "is_active": True},
                ],
                "flow_labels": [
                    {"source_id": 1, "flow_role": "afferent"},
                    {"source_id": 2, "flow_role": "efferent"},
                ],
            }

    result = export_snapshot_dry_run(
        request=SnapshotExportRequest(snapshot_id="compile_test"),
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
        seed_root_id=1,
    )

    nodes = pq.read_table(result.snapshot_dir / "normalized" / "nodes.parquet").to_pylist()
    edges = pq.read_table(result.snapshot_dir / "normalized" / "edges.parquet").to_pylist()
    compiled = compile_snapshot(nodes=nodes, edges=edges)

    assert compiled.node_index
    assert compiled.edge_index
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/integration/test_dry_run_snapshot_compile.py -q`
Expected: FAIL until dry-run export outputs are compatible with the compiler inputs.

**Step 3: Write minimal implementation**

Adjust dry-run export fields if needed so the existing compiler can consume normalized outputs without custom adapters.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/integration/test_dry_run_snapshot_compile.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/integration/test_dry_run_snapshot_compile.py src/fruitfly/snapshot/exporter.py
git commit -m "test: prove dry-run snapshot compiles"
```

# FlyWire Read-Only Verification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a real `FlyWire（果蝇连接组平台）` read-only verification milestone that proves the local machine can access the `public dataset（公开数据集）` with the standard local secret, before snapshot export begins.

**Architecture:** Keep `FlyWire` access logic inside `src/fruitfly/snapshot/` so it can be reused by future snapshot-export code. Add a thin CLI in `scripts/` that only parses arguments, formats output, and exits with stable codes. Keep `FlyWire` packages in `flywire extras（FlyWire 可选依赖组）` so the core training environment stays smaller and easier to manage.

**Tech Stack:** Python 3.13, `fafbseg`, `pyarrow`, `pytest`, built-in `tomllib`

---

### Task 1: Add Optional Dependency Groups for FlyWire and Dev Workflows

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Create: `tests/project/test_dependency_groups.py`

**Step 1: Write the failing test**

```python
import tomllib
from pathlib import Path


def test_optional_dependency_groups_exist() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    optional = payload["project"]["optional-dependencies"]

    assert "flywire" in optional
    assert "embodiment" in optional
    assert "dev" in optional
    assert "fafbseg" in " ".join(optional["flywire"])
    assert "pyarrow" in " ".join(optional["flywire"])
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/project/test_dependency_groups.py -q`
Expected: FAIL because `optional-dependencies` are not defined yet.

**Step 3: Write minimal implementation**

Add `optional-dependencies` groups:

- `flywire`
  - `fafbseg`
  - `pyarrow`
- `embodiment`
  - empty placeholder list or a documented placeholder comment in README
- `dev`
  - `pytest`

Update `README.md` to document:

- `pip install -e .`
- `pip install -e '.[flywire]'`
- `pip install -e '.[flywire,dev]'`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/project/test_dependency_groups.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml README.md tests/project/test_dependency_groups.py
git commit -m "chore: add optional dependency groups"
```

### Task 2: Create the Read-Only Verification Result Contract

**Files:**
- Create: `src/fruitfly/snapshot/flywire_verify.py`
- Modify: `src/fruitfly/snapshot/__init__.py`
- Create: `tests/snapshot/test_flywire_verify.py`

**Step 1: Write the failing test**

```python
def test_verification_result_to_dict() -> None:
    from fruitfly.snapshot.flywire_verify import FlyWireVerificationResult

    result = FlyWireVerificationResult(
        status="ok",
        dataset="public",
        materialization_count=3,
        latest_materialization=783,
        query_points=1,
        resolved_roots=1,
    )

    assert result.to_dict()["status"] == "ok"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/snapshot/test_flywire_verify.py::test_verification_result_to_dict -q`
Expected: FAIL because the module does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `FlyWireVerificationResult` dataclass
- stable `to_dict()` method
- optional `error_type` and `message` fields
- import-safe helper that raises a clear error if `fafbseg` is unavailable

```python
@dataclass(slots=True)
class FlyWireVerificationResult:
    status: str
    dataset: str
    materialization_count: int
    latest_materialization: int | None
    query_points: int
    resolved_roots: int
    error_type: str | None = None
    message: str | None = None
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/snapshot/test_flywire_verify.py::test_verification_result_to_dict -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/snapshot/flywire_verify.py src/fruitfly/snapshot/__init__.py tests/snapshot/test_flywire_verify.py
git commit -m "feat: add flywire verification result contract"
```

### Task 3: Implement the Core Read-Only Verification Logic

**Files:**
- Modify: `src/fruitfly/snapshot/flywire_verify.py`
- Modify: `tests/snapshot/test_flywire_verify.py`

**Step 1: Write the failing test**

```python
def test_verify_flywire_readonly_returns_ok_summary() -> None:
    from fruitfly.snapshot.flywire_verify import verify_flywire_readonly

    class FakeFlyWire:
        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def get_materialization_versions(self) -> list[int]:
            return [630, 783]

        def locs_to_segments(self, coords):
            return [720575940000000001]

    result = verify_flywire_readonly(
        flywire_client=FakeFlyWire(),
        coords=[[75350, 60162, 3162]],
        dataset="public",
    )

    assert result.status == "ok"
    assert result.latest_materialization == 783
    assert result.resolved_roots == 1
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/snapshot/test_flywire_verify.py::test_verify_flywire_readonly_returns_ok_summary -q`
Expected: FAIL because verification logic does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `DEFAULT_PUBLIC_COORDS`
- `verify_flywire_readonly(...)`
- dataset pinning to `public`
- materialization listing
- root-resolution count
- error classification for:
  - missing dependency
  - auth failure
  - network failure
  - empty result

Keep the core function testable by allowing a fake `flywire_client` object to be injected.

```python
def verify_flywire_readonly(*, flywire_client=None, coords=None, dataset="public"):
    client = flywire_client or _load_flywire_client()
    client.set_default_dataset(dataset)
    materializations = client.get_materialization_versions()
    roots = client.locs_to_segments(coords or DEFAULT_PUBLIC_COORDS)
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/snapshot/test_flywire_verify.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/snapshot/flywire_verify.py tests/snapshot/test_flywire_verify.py
git commit -m "feat: add flywire readonly verification logic"
```

### Task 4: Add a Thin CLI for Human and JSON Output

**Files:**
- Create: `scripts/verify_flywire_readonly.py`
- Modify: `src/fruitfly/snapshot/flywire_verify.py`
- Create: `tests/scripts/test_verify_flywire_readonly.py`

**Step 1: Write the failing test**

```python
def test_cli_json_output(capsys, monkeypatch) -> None:
    from fruitfly.snapshot import flywire_verify

    monkeypatch.setattr(
        flywire_verify,
        "verify_flywire_readonly",
        lambda **_: flywire_verify.FlyWireVerificationResult(
            status="ok",
            dataset="public",
            materialization_count=2,
            latest_materialization=783,
            query_points=1,
            resolved_roots=1,
        ),
    )

    exit_code = flywire_verify.main(["--json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"status": "ok"' in captured.out
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/scripts/test_verify_flywire_readonly.py -q`
Expected: FAIL because the CLI entrypoint does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `main(argv=None) -> int` inside `src/fruitfly/snapshot/flywire_verify.py`
- text output mode
- `--json` output mode
- stable exit codes:
  - `0`: success
  - `1`: dependency error
  - `2`: auth error
  - `3`: network error
  - `4`: empty result
- thin wrapper script in `scripts/verify_flywire_readonly.py`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/scripts/test_verify_flywire_readonly.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/verify_flywire_readonly.py src/fruitfly/snapshot/flywire_verify.py tests/scripts/test_verify_flywire_readonly.py
git commit -m "feat: add flywire readonly verification cli"
```

### Task 5: Verify the Real Public Dataset Path and Document the Milestone

**Files:**
- Modify: `README.md`
- Create: `tests/integration/test_flywire_readonly_contract.py`

**Step 1: Write the failing test**

```python
def test_readonly_contract_fields_are_stable() -> None:
    from fruitfly.snapshot.flywire_verify import FlyWireVerificationResult

    payload = FlyWireVerificationResult(
        status="ok",
        dataset="public",
        materialization_count=1,
        latest_materialization=783,
        query_points=1,
        resolved_roots=1,
    ).to_dict()

    assert list(payload)[:6] == [
        "status",
        "dataset",
        "materialization_count",
        "latest_materialization",
        "query_points",
        "resolved_roots",
    ]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/integration/test_flywire_readonly_contract.py -q`
Expected: FAIL until the final output contract is implemented.

**Step 3: Write minimal implementation**

Update:

- `README.md` with:
  - install command for `flywire extras`
  - `verify_flywire_readonly.py` example usage
  - milestone definition
- if needed, adjust `to_dict()` field order to keep the contract stable

After code and docs are in place, run the real command manually:

```bash
pip install -e '.[flywire,dev]'
python3 scripts/verify_flywire_readonly.py --json
```

Expected manual result:

- `status` is `ok`
- `dataset` is `public`
- `materialization_count > 0`
- `resolved_roots > 0`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/integration/test_flywire_readonly_contract.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md tests/integration/test_flywire_readonly_contract.py
git commit -m "docs: add flywire readonly verification milestone"
```

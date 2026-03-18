from __future__ import annotations

from pathlib import Path


def test_mujoco_fly_runtime_reports_unavailable_when_policy_checkpoint_missing(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_runtime import MujocoFlyRuntimeConfig, create_mujoco_fly_runtime

    scene_dir = tmp_path / "flybody-official-walk"
    scene_dir.mkdir()
    (scene_dir / "manifest.json").write_text(
        '{"entry_xml":"walk_imitation.xml","scene_version":"flybody-walk-imitation-v1"}',
        encoding="utf-8",
    )

    runtime = create_mujoco_fly_runtime(
        MujocoFlyRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=tmp_path / "missing-policy.ckpt",
        )
    )

    session = runtime.session_payload()

    assert session["status"] == "unavailable"
    assert session["available"] is False
    assert "checkpoint" in session["reason"].lower()
    assert session["scene_version"] == "flybody-walk-imitation-v1"


def test_mujoco_fly_runtime_rejects_start_when_unavailable(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_runtime import MujocoFlyRuntimeConfig, create_mujoco_fly_runtime

    runtime = create_mujoco_fly_runtime(
        MujocoFlyRuntimeConfig(
            scene_dir=tmp_path / "missing-scene",
            policy_checkpoint_path=tmp_path / "missing-policy.ckpt",
        )
    )

    try:
        runtime.start()
    except RuntimeError as exc:
        assert "unavailable" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("runtime.start() should fail when runtime is unavailable")


def test_mujoco_fly_runtime_emits_unavailable_viewer_state(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_runtime import MujocoFlyRuntimeConfig, create_mujoco_fly_runtime

    runtime = create_mujoco_fly_runtime(
        MujocoFlyRuntimeConfig(
            scene_dir=tmp_path / "missing-scene",
            policy_checkpoint_path=None,
        )
    )

    payload = runtime.current_viewer_state()

    assert payload["running_state"] == "unavailable"
    assert payload["body_poses"] == []
    assert payload["scene_version"] == "unavailable"

from __future__ import annotations

import json
from pathlib import Path


class _FakeMjcfModel:
    pass


class _FakeRootEntity:
    def __init__(self, mjcf_model) -> None:
        self.mjcf_model = mjcf_model


class _FakeTask:
    def __init__(self, mjcf_model) -> None:
        self.root_entity = _FakeRootEntity(mjcf_model)


class _FakeEnvironment:
    def __init__(self, mjcf_model) -> None:
        self.task = _FakeTask(mjcf_model)
        self.reset_calls = 0

    def reset(self) -> None:
        self.reset_calls += 1


def test_export_official_walk_scene_calls_official_export_and_writes_manifest(
    tmp_path: Path, monkeypatch
) -> None:
    from scripts import export_official_walk_imitation_scene

    mjcf_model = _FakeMjcfModel()
    fake_env = _FakeEnvironment(mjcf_model)
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        export_official_walk_imitation_scene,
        "_build_walk_imitation_environment",
        lambda: fake_env,
    )

    def fake_export_with_assets(model, out_dir, out_file_name) -> None:
        captured["model"] = model
        captured["out_dir"] = Path(out_dir)
        captured["out_file_name"] = out_file_name
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / out_file_name).write_text(
            """
<mujoco>
  <default>
    <default class="walker/">
      <mesh scale="0.1 0.1 0.1" />
      <default class="walker/body">
        <geom material="walker/body" />
      </default>
    </default>
  </default>
  <asset>
    <mesh name="walker/thorax" class="walker/" file="thorax_body.obj" />
    <material name="walker/body" rgba="0.67 0.35 0.14 1" shininess="0.6" />
  </asset>
  <worldbody>
    <camera name="walker/track1" mode="trackcom" pos="0.6 0.6 0.22" quat="0.312 0.221 0.533 0.754" />
    <body name="walker/">
      <body name="walker/thorax" childclass="walker/body">
        <geom
          name="walker/thorax"
          mesh="walker/thorax"
          pos="0 0 0.25"
          quat="1 0 0 0"
        />
      </body>
    </body>
  </worldbody>
</mujoco>
            """.strip(),
            encoding="utf-8",
        )
        (Path(out_dir) / "thorax_body.obj").write_text("o thorax\n", encoding="utf-8")

    monkeypatch.setattr(
        export_official_walk_imitation_scene,
        "_export_with_assets",
        fake_export_with_assets,
    )

    output_dir = tmp_path / "official-walk"
    manifest = export_official_walk_imitation_scene.export_official_walk_scene(
        output_dir=output_dir
    )

    assert fake_env.reset_calls == 1
    assert captured["model"] is mjcf_model
    assert captured["out_dir"] == output_dir
    assert captured["out_file_name"] == "walk_imitation.xml"
    assert manifest["entry_xml"] == "walk_imitation.xml"
    assert manifest["scene_version"] == "flybody-walk-imitation-v1"
    assert manifest["asset_count"] == 2
    assert manifest["body_manifest"][1]["body_name"] == "walker/thorax"
    assert manifest["body_manifest"][1]["parent_body_name"] == "walker/"
    assert manifest["geom_manifest"][0]["geom_name"] == "walker/thorax"
    assert manifest["geom_manifest"][0]["mesh_asset_path"] == "thorax_body.obj"
    assert manifest["geom_manifest"][0]["mesh_scale"] == [0.1, 0.1, 0.1]
    assert manifest["geom_manifest"][0]["material_name"] == "walker/body"
    assert manifest["geom_manifest"][0]["material_rgba"] == [0.67, 0.35, 0.14, 1.0]
    assert manifest["camera_manifest"][0]["preset"] == "track"
    assert manifest["camera_manifest"][0]["camera_name"] == "walker/track1"
    assert manifest["camera_manifest"][0]["position"] == [0.6, 0.6, 0.22]
    assert (output_dir / "manifest.json").exists()


def test_export_official_walk_scene_main_prints_manifest_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from scripts import export_official_walk_imitation_scene

    output_dir = tmp_path / "public" / "mujoco-fly" / "flybody-official-walk"

    monkeypatch.setattr(
        export_official_walk_imitation_scene,
        "export_official_walk_scene",
        lambda output_dir: {
            "entry_xml": "walk_imitation.xml",
            "scene_version": "flybody-walk-imitation-v1",
            "asset_count": 3,
            "output_dir": str(output_dir),
        },
    )

    exit_code = export_official_walk_imitation_scene.main(
        ["--output-dir", str(output_dir), "--json"]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert parsed["entry_xml"] == "walk_imitation.xml"
    assert parsed["output_dir"] == str(output_dir)


def test_prepare_runtime_environment_defaults_mujoco_gl_to_off() -> None:
    from scripts import export_official_walk_imitation_scene

    environ: dict[str, str] = {}

    export_official_walk_imitation_scene._prepare_runtime_environment(environ)

    assert environ["MUJOCO_GL"] == "off"


def test_prepare_runtime_environment_preserves_explicit_backend() -> None:
    from scripts import export_official_walk_imitation_scene

    environ = {"MUJOCO_GL": "egl"}

    export_official_walk_imitation_scene._prepare_runtime_environment(environ)

    assert environ["MUJOCO_GL"] == "egl"

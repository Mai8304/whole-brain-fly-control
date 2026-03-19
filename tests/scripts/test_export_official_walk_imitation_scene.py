from __future__ import annotations

import json
from pathlib import Path

import numpy as np


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
    <texture
      name="groundplane"
      type="2d"
      builtin="checker"
      rgb1="0.2 0.3 0.4"
      rgb2="0.1 0.2 0.3"
      mark="edge"
      markrgb="0.8 0.8 0.8"
      width="200"
      height="200"
    />
    <mesh name="walker/thorax" class="walker/" file="thorax_body.obj" />
    <material
      name="groundplane"
      texture="groundplane"
      texrepeat="2 2"
      texuniform="true"
      reflectance="0.2"
    />
    <material name="walker/body" rgba="0.67 0.35 0.14 1" shininess="0.6" />
  </asset>
  <worldbody>
    <geom
      name="groundplane"
      type="plane"
      size="8 8 0.25"
      material="groundplane"
      friction="0.5"
    />
    <body name="walker/">
      <body name="walker/thorax" childclass="walker/body">
        <light name="walker/right" mode="trackcom" pos="0 -1 1" dir="0 1 -1" diffuse="0.3 0.3 0.3" />
        <camera name="walker/track1" mode="trackcom" pos="0.6 0.6 0.22" quat="0.312 0.221 0.533 0.754" />
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
    assert manifest["geom_manifest"][0]["geom_local_position"] == [0.0, 0.0, 0.25]
    assert manifest["geom_manifest"][0]["geom_local_quaternion"] == [1.0, 0.0, 0.0, 0.0]
    assert manifest["geom_manifest"][0]["mesh_local_position"] == [0.0, 0.0, 0.0]
    assert manifest["geom_manifest"][0]["mesh_local_quaternion"] == [1.0, 0.0, 0.0, 0.0]
    assert manifest["geom_manifest"][0]["material_name"] == "walker/body"
    assert manifest["geom_manifest"][0]["material_rgba"] == [0.67, 0.35, 0.14, 1.0]
    assert manifest["camera_manifest"][0]["preset"] == "track"
    assert manifest["camera_manifest"][0]["camera_name"] == "walker/track1"
    assert manifest["camera_manifest"][0]["parent_body_name"] == "walker/thorax"
    assert manifest["camera_manifest"][0]["position"] == [0.6, 0.6, 0.22]
    assert manifest["ground_manifest"]["geom_name"] == "groundplane"
    assert manifest["ground_manifest"]["texture_builtin"] == "checker"
    assert manifest["ground_manifest"]["texrepeat"] == [2.0, 2.0]
    assert manifest["ground_manifest"]["reflectance"] == 0.2
    assert manifest["light_manifest"][0]["name"] == "walker/right"
    assert manifest["light_manifest"][0]["parent_body_name"] == "walker/thorax"
    assert manifest["light_manifest"][0]["direction"] == [0.0, 1.0, -1.0]
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


def test_compiled_mesh_geometry_is_baked_for_browser_viewer_assets(tmp_path: Path) -> None:
    from scripts import export_official_walk_imitation_scene

    class _FakeModel:
        def __init__(self) -> None:
            self.geom_dataid = np.asarray([7], dtype=np.int32)
            self.mesh_pos = np.asarray(
                [[float(index), -0.03, 0.45] for index in range(8)],
                dtype=np.float64,
            )
            self.mesh_quat = np.asarray(
                [[1.0, 0.0, 0.0, float(index) / 10.0] for index in range(8)],
                dtype=np.float64,
            )
            self.mesh_scale = np.asarray([[0.1, 0.2, 0.3] for _ in range(8)], dtype=np.float64)
            self.mesh_vert = np.asarray(
                [[9.0, 9.0, 9.0]] * 4
                + [[7.0, 0.0, 0.0], [8.0, 0.0, 0.0], [7.0, 1.0, 0.0]]
                + [[8.0, 8.0, 8.0]] * 4,
                dtype=np.float64,
            )
            self.mesh_vertadr = np.asarray([4 for _ in range(8)], dtype=np.int32)
            self.mesh_vertnum = np.asarray([3 for _ in range(8)], dtype=np.int32)
            self.mesh_face = np.asarray([[0, 1, 2]], dtype=np.int32)
            self.mesh_faceadr = np.asarray([0 for _ in range(8)], dtype=np.int32)
            self.mesh_facenum = np.asarray([1 for _ in range(8)], dtype=np.int32)
            self.mesh_normal = np.asarray(
                [[0.0, 0.0, 1.0]] * 4
                + [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]
                + [[0.0, 0.0, 1.0]] * 4,
                dtype=np.float64,
            )
            self.mesh_normaladr = np.asarray([4 for _ in range(8)], dtype=np.int32)
            self.mesh_normalnum = np.asarray([3 for _ in range(8)], dtype=np.int32)
            self.mesh_texcoord = np.asarray(
                [[0.5, 0.5]] * 4
                + [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
                + [[0.5, 0.5]] * 4,
                dtype=np.float64,
            )
            self.mesh_texcoordadr = np.asarray([4 for _ in range(8)], dtype=np.int32)
            self.mesh_texcoordnum = np.asarray([3 for _ in range(8)], dtype=np.int32)

        def name2id(self, name: str, object_type: str) -> int:
            assert object_type == "geom"
            if name != "walker/thorax":
                raise KeyError(name)
            return 0

    class _FakePhysics:
        def __init__(self) -> None:
            self.model = _FakeModel()

    geom_manifest = [
        {
            "geom_name": "walker/thorax",
            "body_name": "walker/thorax",
            "mesh_asset_path": "thorax_body.obj",
            "mesh_scale": [9.0, 9.0, 9.0],
            "geom_local_position": [0.0, 0.0, 0.25],
            "geom_local_quaternion": [1.0, 0.0, 0.0, 0.0],
            "mesh_local_position": [9.0, 9.0, 9.0],
            "mesh_local_quaternion": [0.0, 1.0, 0.0, 0.0],
        }
    ]

    export_official_walk_imitation_scene._materialize_compiled_mesh_assets(
        output_dir=tmp_path,
        geom_manifest=geom_manifest,
        physics=_FakePhysics(),
    )

    assert geom_manifest[0]["mesh_scale"] == [1.0, 1.0, 1.0]
    assert geom_manifest[0]["geom_local_position"] == [0.0, 0.0, 0.25]
    assert geom_manifest[0]["geom_local_quaternion"] == [1.0, 0.0, 0.0, 0.0]
    assert geom_manifest[0]["mesh_local_position"] == [0.0, 0.0, 0.0]
    assert geom_manifest[0]["mesh_local_quaternion"] == [1.0, 0.0, 0.0, 0.0]
    assert geom_manifest[0]["mesh_asset_path"] == "compiled/mesh-7.obj"
    baked_mesh_path = tmp_path / geom_manifest[0]["mesh_asset_path"]
    assert baked_mesh_path.exists()
    baked_obj = baked_mesh_path.read_text(encoding="utf-8")
    assert "v 7 0 0" in baked_obj
    assert "v 8 0 0" in baked_obj
    assert "v 7 1 0" in baked_obj
    assert "f 1/1/1 2/2/2 3/3/3" in baked_obj


def test_compiled_mesh_geometry_uses_official_geom_dataid_mapping(
    tmp_path: Path,
) -> None:
    from scripts import export_official_walk_imitation_scene

    class _FakeModel:
        def __init__(self) -> None:
            self.geom_dataid = np.asarray([7], dtype=np.int32)
            self.mesh_pos = np.asarray(
                [[float(index), 0.0, 0.0] for index in range(8)],
                dtype=np.float64,
            )
            self.mesh_quat = np.asarray(
                [[1.0, 0.0, 0.0, float(index) / 10.0] for index in range(8)],
                dtype=np.float64,
            )
            self.mesh_scale = np.asarray([[1.0, 1.0, 1.0] for _ in range(8)], dtype=np.float64)
            self.mesh_vert = np.asarray(
                [[9.0, 9.0, 9.0]] * 6
                + [[3.0, 0.0, 0.0], [4.0, 0.0, 0.0], [3.0, 1.0, 0.0]]
                + [[7.0, 0.0, 0.0], [8.0, 0.0, 0.0], [7.0, 1.0, 0.0]]
                + [[8.0, 8.0, 8.0]] * 3,
                dtype=np.float64,
            )
            self.mesh_vertadr = np.asarray([6, 6, 6, 6, 6, 6, 6, 9], dtype=np.int32)
            self.mesh_vertnum = np.asarray([3, 3, 3, 3, 3, 3, 3, 3], dtype=np.int32)
            self.mesh_face = np.asarray([[0, 1, 2], [0, 1, 2]], dtype=np.int32)
            self.mesh_faceadr = np.asarray([0, 0, 0, 1, 1, 1, 1, 1], dtype=np.int32)
            self.mesh_facenum = np.asarray([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int32)
            self.mesh_normal = np.asarray([[0.0, 0.0, 1.0]] * 12, dtype=np.float64)
            self.mesh_normaladr = np.asarray([6, 6, 6, 6, 6, 6, 6, 9], dtype=np.int32)
            self.mesh_normalnum = np.asarray([3, 3, 3, 3, 3, 3, 3, 3], dtype=np.int32)
            self.mesh_texcoord = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]] * 4, dtype=np.float64)
            self.mesh_texcoordadr = np.asarray([6, 6, 6, 6, 6, 6, 6, 9], dtype=np.int32)
            self.mesh_texcoordnum = np.asarray([3, 3, 3, 3, 3, 3, 3, 3], dtype=np.int32)

        def name2id(self, name: str, object_type: str) -> int:
            assert object_type == "geom"
            if name != "walker/thorax":
                raise KeyError(name)
            return 0

    class _FakePhysics:
        def __init__(self) -> None:
            self.model = _FakeModel()

    geom_manifest = [
        {
            "geom_name": "walker/thorax",
            "body_name": "walker/thorax",
            "mesh_asset_path": "thorax_body.obj",
            "mesh_scale": [9.0, 9.0, 9.0],
            "geom_local_position": [0.0, 0.0, 0.25],
            "geom_local_quaternion": [1.0, 0.0, 0.0, 0.0],
            "mesh_local_position": [9.0, 9.0, 9.0],
            "mesh_local_quaternion": [0.0, 1.0, 0.0, 0.0],
        }
    ]

    export_official_walk_imitation_scene._materialize_compiled_mesh_assets(
        output_dir=tmp_path,
        geom_manifest=geom_manifest,
        physics=_FakePhysics(),
    )

    assert geom_manifest[0]["mesh_asset_path"] == "compiled/mesh-7.obj"
    assert geom_manifest[0]["mesh_local_position"] == [0.0, 0.0, 0.0]
    assert geom_manifest[0]["mesh_local_quaternion"] == [1.0, 0.0, 0.0, 0.0]

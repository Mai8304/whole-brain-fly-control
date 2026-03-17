from pathlib import Path

import pytest


def test_serve_neural_console_api_cli_invokes_uvicorn(tmp_path, monkeypatch) -> None:
    from scripts import serve_neural_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    checkpoint_path = tmp_path / "epoch_0001.pt"
    brain_asset_dir = tmp_path / "outputs" / "ui-assets" / "flywire_brain_v141"
    compiled_dir.mkdir()
    eval_dir.mkdir()
    brain_asset_dir.mkdir(parents=True)
    checkpoint_path.write_bytes(b"checkpoint")
    (brain_asset_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (brain_asset_dir / "brain_shell.glb").write_bytes(b"glb")

    captured = {}

    monkeypatch.setattr(serve_neural_console_api, "ROOT", tmp_path)

    def fake_create_console_api(config):
        captured["config"] = config
        return object()

    def fake_run(app, *, host, port, reload):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    monkeypatch.setattr(serve_neural_console_api, "create_console_api", fake_create_console_api)
    monkeypatch.setattr(serve_neural_console_api.uvicorn, "run", fake_run)

    exit_code = serve_neural_console_api.main(
        [
            "--compiled-graph-dir",
            str(compiled_dir),
            "--eval-dir",
            str(eval_dir),
            "--checkpoint",
            str(checkpoint_path),
            "--host",
            "127.0.0.1",
            "--port",
            "9010",
            "--reload",
        ]
    )

    assert exit_code == 0
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 9010
    assert captured["reload"] is True
    assert captured["app"] is not None
    assert captured["config"].brain_asset_dir == brain_asset_dir
    assert not hasattr(captured["config"], "roi_asset_dir")


def test_serve_neural_console_api_rejects_legacy_roi_asset_dir_flag(tmp_path) -> None:
    from scripts import serve_neural_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    roi_asset_dir = tmp_path / "roi_assets"
    compiled_dir.mkdir()
    eval_dir.mkdir()
    roi_asset_dir.mkdir()

    with pytest.raises(SystemExit) as exc_info:
        serve_neural_console_api.main(
            [
                "--compiled-graph-dir",
                str(compiled_dir),
                "--eval-dir",
                str(eval_dir),
                "--roi-asset-dir",
                str(roi_asset_dir),
            ]
        )

    assert exc_info.value.code == 2

from __future__ import annotations

import json
from pathlib import Path

from scripts import import_flywire_roi_meshes


def test_main_prints_output_path(monkeypatch, tmp_path: Path, capsys) -> None:
    def fake_export(*, output_dir: Path):
        (output_dir / "source_info.json").write_text("{}", encoding="utf-8")
        return {"provider": "fake"}

    monkeypatch.setattr(import_flywire_roi_meshes, "export_v1_roi_meshes", fake_export)

    exit_code = import_flywire_roi_meshes.main(["--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(tmp_path / "source_info.json")


def test_main_prints_json(monkeypatch, tmp_path: Path, capsys) -> None:
    payload = {"provider": "fake", "roi_meshes": []}

    def fake_export(*, output_dir: Path):
        return payload

    monkeypatch.setattr(import_flywire_roi_meshes, "export_v1_roi_meshes", fake_export)

    exit_code = import_flywire_roi_meshes.main(["--output-dir", str(tmp_path), "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == payload

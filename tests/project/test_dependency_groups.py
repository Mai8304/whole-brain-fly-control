import tomllib
from pathlib import Path


def test_optional_dependency_groups_exist() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    optional = payload["project"]["optional-dependencies"]

    assert "flywire" in optional
    assert "embodiment" in optional
    assert "ui" in optional
    assert "dev" in optional
    assert "fafbseg" in " ".join(optional["flywire"])
    assert "pyarrow" in " ".join(optional["flywire"])
    assert "fastapi" in " ".join(optional["ui"])
    assert "uvicorn" in " ".join(optional["ui"])


def test_readme_documents_optional_installs() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "pip install -e .[flywire]" in readme or "pip install -e '.[flywire]'" in readme
    assert "pip install -e '.[flywire,dev]'" in readme
    assert "pip install -e '.[ui]'" in readme or "pip install -e .[ui]" in readme

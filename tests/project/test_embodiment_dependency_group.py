import tomllib
from pathlib import Path


def test_embodiment_dependency_group_exists() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    optional = payload["project"]["optional-dependencies"]

    assert "embodiment" in optional


def test_readme_documents_flybody_slice() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "flybody" in readme
    assert "straight walking" in readme
    assert "separate environment" in readme or "dedicated environment" in readme


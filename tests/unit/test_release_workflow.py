from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


def read_workflow(name: str) -> str:
    return (PROJECT_ROOT / ".github" / "workflows" / f"{name}.yml").read_text(encoding="utf-8")


def test_publish_workflow_requires_release_commit_to_be_on_main() -> None:
    workflow = read_workflow("publish")

    assert "git fetch --no-tags origin main" in workflow
    assert 'git merge-base --is-ancestor "${GITHUB_SHA}" origin/main' in workflow
    assert "distribution_version=" in workflow
    assert "module_version=" in workflow
    assert 'test "${distribution_version}" = "${module_version}"' in workflow
    assert 'test "v${distribution_version}" = "${GITHUB_REF_NAME}"' in workflow
    assert "Verify built artifact version" in workflow


def test_publish_workflow_repeats_security_and_quality_gates() -> None:
    workflow = read_workflow("publish")

    assert "--cov=opentradeintel" in workflow
    assert "--cov-fail-under=90" in workflow
    assert "vulture src --min-confidence 90 --ignore-names cls" in workflow
    assert "uv export --frozen --no-dev --no-emit-project" in workflow
    assert "uv run pip-audit" in workflow


def test_ci_workflow_enforces_coverage_dead_code_and_container_health() -> None:
    workflow = read_workflow("ci")

    assert "--cov=opentradeintel" in workflow
    assert "--cov-fail-under=90" in workflow
    assert "vulture src --min-confidence 90 --ignore-names cls" in workflow
    assert "docker build --tag opentradeintel:ci ." in workflow
    assert "State.Health.Status" in workflow


def test_security_workflow_audits_runtime_dependencies_and_secrets() -> None:
    workflow = read_workflow("security")

    assert "uv export --frozen --no-dev --no-emit-project" in workflow
    assert "uv run pip-audit" in workflow
    assert "gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e" in workflow
    assert "GITLEAKS_VERSION: 8.29.1" in workflow


def test_quality_tools_are_direct_development_dependencies() -> None:
    project = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"pip-audit>=2.10.1,<3"' in project
    assert '"pytest-cov>=7.1,<8"' in project
    assert '"vulture>=2.16,<3"' in project

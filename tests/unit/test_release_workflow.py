from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


def test_publish_workflow_requires_release_commit_to_be_on_main() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")

    assert "git fetch --no-tags origin main" in workflow
    assert 'git merge-base --is-ancestor "${GITHUB_SHA}" origin/main' in workflow
    assert "distribution_version=" in workflow
    assert "module_version=" in workflow
    assert 'test "${distribution_version}" = "${module_version}"' in workflow
    assert 'test "v${distribution_version}" = "${GITHUB_REF_NAME}"' in workflow
    assert "Verify built artifact version" in workflow

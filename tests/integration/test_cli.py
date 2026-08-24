from pathlib import Path

from typer.testing import CliRunner

from opentradeintel.cli import app

runner = CliRunner()
PROJECT_ROOT = Path(__file__).parents[2]
TENDER_PATH = PROJECT_ROOT / "examples" / "tenders" / "sample.json"
CATALOG_PATH = PROJECT_ROOT / "examples" / "catalogs" / "sample.csv"


def test_cli_help_describes_the_tool() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "procurement and B2B sourcing intelligence" in result.stdout
    assert "inspect" in result.stdout
    assert "match" in result.stdout


def test_cli_version_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "0.1.0"


def test_cli_inspect_prints_validated_tender_summary() -> None:
    result = runner.invoke(app, ["inspect", str(TENDER_PATH)])

    assert result.exit_code == 0
    assert "Organic dried mango" in result.stdout
    assert "Demo Meridian Buyers Cooperative" in result.stdout
    assert "20,000 kg" in result.stdout
    assert "Germany" in result.stdout


def test_cli_match_prints_computed_results_and_explanations() -> None:
    result = runner.invoke(
        app,
        ["match", "--tender", str(TENDER_PATH), "--catalog", str(CATALOG_PATH)],
    )

    assert result.exit_code == 0
    assert "Best matches:" in result.stdout
    assert "Dried Mango 500g" in result.stdout
    assert "Score: 100/100" in result.stdout
    assert "Reasons:" in result.stdout
    assert "Product similarity: 40/40" in result.stdout
    assert "Warnings:" in result.stdout


def test_cli_match_output_is_safe_for_ascii_only_terminals() -> None:
    result = runner.invoke(
        app,
        ["match", "--tender", str(TENDER_PATH), "--catalog", str(CATALOG_PATH)],
    )

    assert result.exit_code == 0
    result.stdout.encode("ascii")


def test_cli_match_reports_missing_file_without_traceback(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"

    result = runner.invoke(
        app,
        ["match", "--tender", str(missing), "--catalog", str(CATALOG_PATH)],
    )

    assert result.exit_code == 1
    assert "Could not read source file" in result.stderr
    assert "Traceback" not in result.stderr

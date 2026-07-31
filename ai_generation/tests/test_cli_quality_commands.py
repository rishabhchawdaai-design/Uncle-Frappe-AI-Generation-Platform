"""
Integration tests for the Phase 33-36 quality engineering CLI commands.

Each test exercises the full path: CLI command -> Unified SDK lazy property ->
engine implementation -> console output.
"""
import asyncio
import textwrap

from ai_generation.cli import (
    cmd_analyze_code,
    cmd_debt_scan,
    cmd_orchestrate,
    cmd_quality_gates,
    cmd_quality_report,
    cmd_refactor_suggest,
    cmd_review_code,
    cmd_scan_secrets,
)


SAMPLE_CODE = textwrap.dedent(
    '''
    """Sample module for CLI quality command tests."""
    import logging

    logger = logging.getLogger(__name__)


    def add(a, b):
        # TODO: handle None inputs
        return a + b


    def main() -> None:
        """Entry point."""
        print(add(1, 2))


    if __name__ == "__main__":
        main()
    '''
)


SECRET_CODE = textwrap.dedent(
    '''
    """Module containing a leaked credential."""
    aws_key = "AKIAIOSFODNN7EXAMPLE"
    endpoint = "https://example.com"
    '''
)


def test_cmd_quality_gates(capsys):
    asyncio.run(cmd_quality_gates(""))
    out = capsys.readouterr().out
    assert "Quality Gates" in out
    assert "Swiss Cheese Model" in out


def test_cmd_quality_gates_with_file(tmp_path, capsys):
    target = tmp_path / "sample.py"
    target.write_text(SAMPLE_CODE)
    asyncio.run(cmd_quality_gates(str(target)))
    out = capsys.readouterr().out
    assert "Quality Gates" in out


def test_cmd_review_code(capsys):
    asyncio.run(cmd_review_code(""))
    out = capsys.readouterr().out
    assert "Multi-Agent Code Review" in out
    assert "Quality Score" in out
    assert "Total Findings" in out


def test_cmd_scan_secrets_clean(capsys):
    asyncio.run(cmd_scan_secrets(""))
    out = capsys.readouterr().out
    assert "Secret Scanner" in out


def test_cmd_scan_secrets_detects_aws_key(tmp_path, capsys):
    target = tmp_path / "leak.py"
    target.write_text(SECRET_CODE)
    asyncio.run(cmd_scan_secrets(str(target)))
    out = capsys.readouterr().out
    assert "Secret Scanner" in out
    assert "line=3" in out


def test_cmd_analyze_code(capsys):
    asyncio.run(cmd_analyze_code(""))
    out = capsys.readouterr().out
    assert "Code Analysis" in out
    assert "Static Issues" in out
    assert "Structural Findings" in out


def test_cmd_debt_scan(capsys):
    asyncio.run(cmd_debt_scan(""))
    out = capsys.readouterr().out
    assert "Technical Debt Scan" in out


def test_cmd_refactor_suggest(capsys):
    asyncio.run(cmd_refactor_suggest(""))
    out = capsys.readouterr().out
    assert "Refactoring Suggestions" in out


def test_cmd_quality_report(capsys):
    asyncio.run(cmd_quality_report(""))
    out = capsys.readouterr().out
    assert "Quality Dashboard" in out
    assert "Overall" in out


def test_cmd_orchestrate(capsys):
    asyncio.run(cmd_orchestrate(""))
    out = capsys.readouterr().out
    assert "Orchestration Pipeline" in out
    assert "Final Result" in out

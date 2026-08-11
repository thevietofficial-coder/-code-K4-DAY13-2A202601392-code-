from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PANEL_CONTRACT = {
    "latency": {
        "events": ["response_sent"],
        "fields": ["latency_ms"],
        "aggregations": ["p50", "p95", "p99"],
        "unit": "ms",
    },
    "traffic": {
        "events": ["request_received"],
        "fields": ["event"],
        "aggregations": ["count", "rate_per_minute"],
        "unit": "requests_per_minute",
    },
    "errors": {
        "events": ["request_received", "request_failed"],
        "fields": ["error_type"],
        "aggregations": ["error_rate_pct", "count_by_value"],
        "unit": "percent",
    },
    "cost": {
        "events": ["response_sent"],
        "fields": ["cost_usd"],
        "aggregations": ["sum_by_minute", "total"],
        "unit": "usd",
    },
    "tokens": {
        "events": ["response_sent"],
        "fields": ["tokens_in", "tokens_out"],
        "aggregations": ["sum_by_field"],
        "unit": "tokens",
    },
    "quality": {
        "events": ["response_sent"],
        "fields": ["quality_score"],
        "aggregations": ["mean"],
        "unit": "score_0_to_1",
    },
}


def run_validator(config_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_dashboard.py"),
            "--config",
            str(config_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_repository_dashboard_contract_is_valid() -> None:
    result = run_validator(REPO_ROOT / "config" / "dashboard.yaml")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "6/6 panel" in result.stdout


def test_repository_dashboard_uses_six_required_metric_definitions() -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )
    panels = {panel["id"]: panel for panel in payload["dashboard"]["panels"]}

    assert set(panels) == set(EXPECTED_PANEL_CONTRACT)
    for panel_id, expected in EXPECTED_PANEL_CONTRACT.items():
        panel = panels[panel_id]
        assert panel["source"] == "data/logs.jsonl"
        for key, value in expected.items():
            assert panel[key] == value

    error_query = panels["errors"]["query"]
    assert 'count(event == "request_failed")' in error_query
    assert 'count(event == "request_received")' in error_query


def test_validator_rejects_panel_without_threshold(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )
    del payload["dashboard"]["panels"][0]["threshold"]
    invalid_config = tmp_path / "dashboard.yaml"
    invalid_config.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    result = run_validator(invalid_config)

    assert result.returncode == 1
    assert "latency.threshold" in result.stdout


def test_validator_rejects_panel_without_query_example(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )
    payload["dashboard"]["panels"][0].pop("query", None)
    invalid_config = tmp_path / "dashboard.yaml"
    invalid_config.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    result = run_validator(invalid_config)

    assert result.returncode == 1
    assert "latency.query" in result.stdout

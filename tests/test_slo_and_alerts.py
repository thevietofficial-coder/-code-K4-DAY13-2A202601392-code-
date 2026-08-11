from __future__ import annotations

from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_slo_config_validity() -> None:
    slo_path = REPO_ROOT / "config" / "slo.yaml"
    assert slo_path.exists(), "config/slo.yaml phải tồn tại"

    content = slo_path.read_text(encoding="utf-8")
    payload = yaml.safe_load(content)
    assert isinstance(payload, dict), "Payload trong config/slo.yaml phải là dict"
    assert "service" in payload, "Cần có trường 'service'"
    assert "window" in payload, "Cần có trường 'window'"
    assert "slis" in payload, "Cần có trường 'slis'"

    slis = payload["slis"]
    required_slis = {"latency_p95_ms", "error_rate_pct", "daily_cost_usd", "quality_score_avg"}
    assert required_slis.issubset(set(slis.keys())), f"SLIs phải chứa: {required_slis}"

    for sli_name, sli_data in slis.items():
        assert "objective" in sli_data, f"SLI {sli_name} thiếu 'objective'"
        assert "target" in sli_data, f"SLI {sli_name} thiếu 'target'"
        assert isinstance(sli_data["objective"], (int, float)), f"{sli_name}.objective phải là số"
        assert isinstance(sli_data["target"], (int, float)), f"{sli_name}.target phải là số"


def test_alert_rules_config_validity() -> None:
    alert_rules_path = REPO_ROOT / "config" / "alert_rules.yaml"
    assert alert_rules_path.exists(), "config/alert_rules.yaml phải tồn tại"

    content = alert_rules_path.read_text(encoding="utf-8")
    payload = yaml.safe_load(content)
    assert isinstance(payload, dict), "Payload trong config/alert_rules.yaml phải là dict"
    assert "alerts" in payload, "Cần có trường 'alerts'"

    alerts = payload["alerts"]
    assert isinstance(alerts, list), "'alerts' phải là danh sách"
    assert len(alerts) >= 3, "Phải có ít nhất 3 alert rules"

    required_fields = ("name", "severity", "condition", "type", "owner", "runbook")
    for idx, alert in enumerate(alerts, 1):
        assert isinstance(alert, dict), f"Alert thứ {idx} phải là dict"
        for field in required_fields:
            val = alert.get(field)
            assert val is not None and str(val).strip() != "", f"Alert thứ {idx} thiếu hoặc rỗng field '{field}'"
            assert "TODO" not in str(val), f"Alert thứ {idx} field '{field}' còn chứa placeholder TODO chưa hoàn thiện"

        assert alert["severity"].lower() in {"warning", "critical"}, f"Alert '{alert['name']}' severity phải là 'warning' hoặc 'critical'"
        assert alert["type"] == "symptom-based", f"Alert '{alert['name']}' type phải là 'symptom-based'"
        assert "docs/alerts.md#" in alert["runbook"], f"Alert '{alert['name']}' runbook phải liên kết đến docs/alerts.md"


def test_alert_runbook_completeness() -> None:
    alerts_doc_path = REPO_ROOT / "docs" / "alerts.md"
    assert alerts_doc_path.exists(), "docs/alerts.md phải tồn tại"

    content = alerts_doc_path.read_text(encoding="utf-8")
    assert "## Alert 1" in content, "docs/alerts.md phải có '## Alert 1'"
    assert "## Alert 2" in content, "docs/alerts.md phải có '## Alert 2'"
    assert "## Alert 3" in content, "docs/alerts.md phải có '## Alert 3'"

    required_headers = [
        "Severity",
        "SLI/SLO",
        "Điều kiện",
        "Ảnh hưởng",
        "Ba bước kiểm tra",
        "Mitigation",
        "Owner",
    ]
    for header in required_headers:
        assert header in content, f"docs/alerts.md phải chứa mục '{header}'"

    assert "Nguyễn Đình Duy" in content or "Thành viên D" in content, "docs/alerts.md phải ghi rõ Owner là Nguyễn Đình Duy / Thành viên D"

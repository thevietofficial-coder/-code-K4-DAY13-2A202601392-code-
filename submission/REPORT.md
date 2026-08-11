# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel
- Evidence dashboard: `submission/evidence/dashboard.png`
- SLO đã chọn và lý do:
  - `latency_p95_ms` <= 3000ms (Target 99.5%): Giữ trải nghiệm tương tác với AI API mượt mà, phản hồi không quá 3 giây.
  - `error_rate_pct` <= 2.0% (Target 99.0%): Đảm bảo tính sẵn sàng cao, hạn chế lỗi HTTP 500/503.
  - `daily_cost_usd` <= $2.5 USD (Target 100%): Kiểm soát ngân sách API token trong định mức quy định.
  - `quality_score_avg` >= 0.75 (Target 95.0%): Đảm bảo chất lượng câu trả lời RAG/LLM vượt ngưỡng tối thiểu.
- Alert rules và runbook:
  - Cấu hình Alert Rules: `config/alert_rules.yaml` (bao gồm HighLatencyP95Warning, HighErrorRateCritical, LowQualityScoreOrCostBreach).
  - Alert Runbook: `docs/alerts.md#alert-1`, `docs/alerts.md#alert-2`, `docs/alerts.md#alert-3`.

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Đình Duy (Thành viên D) | CP2 Thiết lập SLO (`config/slo.yaml`), Alert Rules (`config/alert_rules.yaml`), Alert Runbook (`docs/alerts.md`), bổ sung unit test `tests/test_slo_and_alerts.py` | [Commit SHA] | Học được cách thiết lập SLO/SLI chuẩn SRE, thiết kế symptom-based alerts dựa trên triệu chứng người dùng và xây dựng Alert Runbook ứng cứu sự cố bằng Correlation ID & Trace Waterfall. |


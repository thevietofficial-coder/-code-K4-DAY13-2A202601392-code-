# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 30/100
- Tổng số traces: 50+ (đếm qua Langfuse API `client.api.trace.list(tags="lab")`, xem `submission/evidence/cp2-tracing-prompt-version.md`)
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: bản tạm (E dựng thay C, snapshot tĩnh từ `data/logs.jsonl`) — xem mục 5. C có thể thay bằng dashboard runtime riêng nếu muốn.

## 3. Logging và tracing

- Evidence correlation ID: **TODO (Thành viên A)**
- Evidence PII redaction: **TODO (Thành viên B)**
- Evidence trace waterfall: trace `737d560702c7f58cf9fcb7ac6f563d13` (xem `submission/evidence/cp2-tracing-prompt-version.md` mục 4) — cần bổ sung ảnh chụp waterfall từ Langfuse UI.
- Giải thích một span đáng chú ý: mỗi request tạo waterfall 3 tầng `run` (generation cha) → `llm.generate` (generation con) và `rag.retrieve` (span con). Việc tách `rag.retrieve` thành span riêng (mở rộng của Thành viên E, xem `app/mock_rag.py`) cho phép nhìn thấy riêng thời gian truy hồi tài liệu tách biệt khỏi thời gian gọi LLM — quan trọng cho điều tra CP3 vì incident chính thức của nhóm là `rag_slow`.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: version 1, label `baseline` (nội dung `Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}`)
- Version/label candidate: version 2, label `candidate` (v1 + thêm hướng dẫn "Answer in at most 3 concise sentences.")
- Trace ID của mỗi version: baseline → `737d560702c7f58cf9fcb7ac6f563d13` (prompt_version=1); candidate → `f998e11004eb1af0d9642f7b7278822c` (prompt_version=2)
- Bằng chứng đổi label hoặc rollback: chuyển `production` sang v2 → trace `fa93db2f3e2beab28fa44dda968e4358` (prompt_version=2, prompt_label=production); rollback `production` về v1 → trace `61eaae867c8db9611495ea1fc0ff51c8` (prompt_version=1, prompt_label=production). Chi tiết đầy đủ trong `submission/evidence/cp2-tracing-prompt-version.md`. Ảnh chụp màn hình Langfuse UI (Prompts → day13-chat → Versions/Labels) còn thiếu, cần chụp thủ công.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel
- Evidence dashboard: `submission/evidence/dashboard.png` (chụp từ bản dashboard tạm thời do Thành viên E dựng thay C — đọc trực tiếp `data/logs.jsonl`, đúng 6 panel/đơn vị/threshold theo `config/dashboard.yaml`, script tính số liệu: xem `submission/evidence/cp2-dashboard.md`). C có thể thay bằng dashboard runtime riêng (Streamlit/Grafana/…) nếu muốn, miễn giữ đúng 6 panel/threshold của contract.
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


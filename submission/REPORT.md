# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: SilverFlag 
- Repository URL: https://github.com/thevietofficial-coder/-code-K4-DAY13-2A202601392-code-
- Commit SHA cuối: xem `git log -1 --format=%H` trên nhánh `main` ngay trước khi nộp (mỗi lần cập nhật report sẽ tạo thêm 1 commit mới)
- Thành viên và vai trò:
  - Thành viên A — Nghia — API & Middleware (Correlation ID, exception handler)
  - Thành viên B — Tuấn (Tuannt04) — Security Engineer (PII Scrubbing)
  - Thành viên C — Minh (MinhHA04) — Metrics & Dashboard
  - Thành viên D — Nguyễn Đình Duy — SRE & Alerts Engineer
  - Thành viên E — Bùi Hoàng Việt (trưởng nhóm) — QA & Chief Investigator

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (chạy lại trên `data/logs.jsonl` sạch sau khi tất cả TODO CP1 đã merge — điểm cũ 30-50/100 là do log cũ từ trước khi A/B hoàn thiện middleware/PII còn lẫn trong file dev cục bộ)
- Tổng số traces: 50+ (đếm qua Langfuse API `client.api.trace.list(tags="lab")`, xem `submission/evidence/cp2-tracing-prompt-version.md`)
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: bản tạm (E dựng thay C, snapshot tĩnh từ `data/logs.jsonl`) — xem mục 5. C có thể thay bằng dashboard runtime riêng nếu muốn.

## 3. Logging và tracing

- Evidence correlation ID: `req-139f2fa0` xuất hiện đồng nhất trên cả 2 dòng log `request_received` và `response_sent` của cùng 1 request (đối chiếu qua `app/middleware.py:CorrelationIdMiddleware` + `bind_contextvars` trong `app/main.py`), kèm đủ enrichment `user_id_hash=2055254ee30a, session_id=s01, feature=qa, model=claude-sonnet-4-5, env=dev`. Trích `data/logs.jsonl`:
  ```json
  {"event":"request_received","correlation_id":"req-139f2fa0","session_id":"s01","feature":"qa","user_id_hash":"2055254ee30a","model":"claude-sonnet-4-5","env":"dev","ts":"2026-08-11T10:06:49.223405Z"}
  {"event":"response_sent","correlation_id":"req-139f2fa0","session_id":"s01","feature":"qa","latency_ms":1044,"ts":"2026-08-11T10:06:50.699639Z"}
  ```
- Evidence PII redaction: cùng request trên gửi `"My email is student@vinuni.edu.vn"`, log ghi `"message_preview": "What is your refund policy? My email is [REDACTED_EMAIL]"` — email gốc không xuất hiện. Tương tự với số điện thoại (`req-0af4646a` → `[REDACTED_PHONE_VN]`) và số thẻ tín dụng (`req-edac0b37` → `[REDACTED_CREDIT_CARD]`), xử lý bởi `scrub_event` trong `app/logging_config.py` (đăng ký trước `JsonlFileProcessor`) dùng pattern trong `app/pii.py`. `python scripts/validate_logs.py` xác nhận độc lập: "Potential PII leaks detected: 0".
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

Chi tiết đầy đủ (bảng đối chiếu 5 session, log timestamp, trace span breakdown): `submission/evidence/cp3-challenge-investigation.md`.

- Challenge ID: `day13-k4-observability-v1` (cohort K4, incident `rag_slow`, `latency_threshold_ms=2000`, `affected_feature=monitoring`)
- Triệu chứng từ metrics: `latency_ms` của cả 5/5 request `feature=monitoring` nhảy từ ~150ms (baseline, incident tắt) lên ~2651-2652ms (incident bật) — vượt `latency_threshold_ms=2000` của challenge và vượt hẳn baseline bình thường
- Trace ID liên quan: cặp trước/sau tiêu biểu cho session `k4-challenge-s01` — tắt: `4674e302731ccfac7601a78813845910` (span `rag.retrieve`=0ms); bật: `04198e5255b430eb914710c7ded4387b` (span `rag.retrieve`=2502ms, `llm.generate`=151ms không đổi). 4 session còn lại cho kết quả tương tự, xem bảng đầy đủ trong file evidence.
- Log line/correlation ID liên quan: `req-a21686e4` (s01), `req-a9a1d40f` (s02), `req-7f992c69` (s03), `req-8535c3d6` (s04), `req-c834d151` (s05) — tất cả `feature=monitoring`, `latency_ms` 2651-2652, đối chiếu khớp với trace ở trên
- Root cause: bước RAG retrieval (`app/mock_rag.py:retrieve()`) bị delay giả lập 2.5s/request khi cờ incident `rag_slow` bật, chiếm >94% tổng latency của request (span `rag.retrieve` 2501-2502ms trên tổng ~2652-2653ms), trong khi `llm.generate` không đổi (~150ms)
- Fix action: đặt timeout + fallback cho lời gọi retrieval; cache kết quả truy hồi cho câu hỏi lặp lại; chạy `retrieve()` qua thread pool (`asyncio.to_thread`) thay vì gọi đồng bộ chặn event loop — phát hiện phụ: log timestamp cho thấy 5 request bị server xử lý hoàn toàn tuần tự dù gửi đồng thời, vì `time.sleep()` đồng bộ trong handler `async def` chặn event loop
- Preventive measure: alert latency P95 tách riêng theo `feature` (phối hợp `HighLatencyP95Warning` trong `config/alert_rules.yaml`); theo dõi riêng thời lượng span `rag.retrieve` như một tín hiệu độc lập; thêm synthetic/canary request định kỳ cho bước retrieval để phát hiện sớm trước khi ảnh hưởng người dùng thật

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nghia (Thành viên A) | CP1 Middleware (`app/middleware.py`: clear/bind contextvars, sinh `x-request-id` dạng `req-<8-hex>`, gắn header response), enrich context request trong `app/main.py`, bổ sung global exception handler (`generic_exception_handler`) cho lỗi ngoài luồng try/except chính | `417fcc3`, `c7c5dab` (PR #1) | Cách `structlog.contextvars` lan truyền field xuyên suốt một request mà không cần truyền tay qua từng hàm log; vì sao clear context đầu mỗi request là bắt buộc để tránh rò rỉ giữa các request. |
| Tuấn — Tuannt04 (Thành viên B) | CP1 PII Scrubbing: mở rộng `PII_PATTERNS` trong `app/pii.py`, đăng ký `scrub_event` vào pipeline `structlog` trong `app/logging_config.py` (đặt trước `JsonlFileProcessor` để redact trước khi ghi file) | `f612441`, `f3ebabf` (PR #2) | Thứ tự processor trong `structlog` quyết định dữ liệu có bị redact trước khi ghi xuống đĩa hay không; PII có thể lọt qua nếu scrub chạy sau bước render/ghi. |
| Minh — MinhHA04 (Thành viên C) | CP1/CP2 hoàn thiện `app/metrics.py` (snapshot/percentile), `docs/dashboard-spec.md`, `tests/test_dashboard_validator.py`, ảnh `dashboard-validator.png` | `fd74f95`, `77f77c4`, `e7dbdc4` (PR #3, #5, #6) | Cách tính `error_rate_pct` đúng cần lấy mẫu số từ `request_received`/`request_failed` trong log thay vì chỉ dựa vào bộ đếm in-memory (có thể thiếu request lỗi); cách viết test cho validator contract. |
| Nguyễn Đình Duy (Thành viên D) | CP2 Thiết lập SLO (`config/slo.yaml`), Alert Rules (`config/alert_rules.yaml`), Alert Runbook (`docs/alerts.md`), bổ sung unit test `tests/test_slo_and_alerts.py` | `d013c52` (PR #4) | Học được cách thiết lập SLO/SLI chuẩn SRE, thiết kế symptom-based alerts dựa trên triệu chứng người dùng và xây dựng Alert Runbook ứng cứu sự cố bằng Correlation ID & Trace Waterfall. |
| Bùi Hoàng Việt (Thành viên E, trưởng nhóm) | CP2: bọc trace riêng cho RAG/LLM (`app/mock_rag.py`, `app/mock_llm.py`), tạo prompt v1/v2 + label/rollback trên Langfuse, dashboard tạm thay C, evidence tracing/prompt/dashboard. CP3: dẫn dắt điều tra challenge `rag_slow` (baseline vs incident, khoanh vùng span, đối chiếu log), viết `submission/REPORT.md` | `a836eb0`, `f734c83`, `f378d42`, `26041e7` | Cách tách span con bằng `@observe()` lồng nhau giúp khoanh vùng root cause chính xác hơn nhìn tổng latency; latency đo ở tầng server (`latency_ms`) có thể thấp hơn nhiều so với latency client thấy được nếu có nghẽn ở tầng ASGI/middleware phía trước. |


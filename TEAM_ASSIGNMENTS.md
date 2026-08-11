# Phân công & Hướng dẫn triển khai — Nhóm 5 người (Day 13 Observability)

> Tài liệu nội bộ của nhóm, dựa trên toàn bộ nội dung hiện có trong repo (README, CHECKPOINTS, RUBRIC, RULES, SETUP, SUBMISSION, `docs/`, `app/`, `config/`, `scripts/`, `tests/`). Dùng file này để phân việc theo từng Checkpoint và theo dõi tiến độ. Người điều phối: **Thành viên E (trưởng nhóm)**.

## 0. Vai trò

| Người | Vai trò | Phạm vi chính |
|---|---|---|
| A | API & Middleware | `app/middleware.py`, Correlation ID, exception handler mở rộng |
| B | Security Engineer | `app/pii.py`, `app/logging_config.py`, kiểm chứng log không lộ PII |
| C | Metrics & Dashboard | `error_rate_pct`, dashboard 6 panel theo `config/dashboard.yaml` |
| D | SRE & Alerts | `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md` |
| **E** | QA & Chief Investigator (trưởng nhóm) | load test, bọc trace RAG/LLM, dẫn dắt CP3, hoàn thiện `submission/REPORT.md` |

**Lưu ý quan trọng:** danh sách vai trò gốc không ghi rõ ai phụ trách "prompt versioning + ≥10 traces" (yêu cầu bắt buộc ở Checkpoint 2). Việc này cần chạy trace thật để có evidence, và gắn chặt với việc E cần trace sạch để điều tra CP3 — nên tài liệu này gán phần đó cho **E**. Nếu nhóm muốn chia lại (ví dụ giao cho A hoặc B phụ), điều chỉnh ở mục 4.3.

**Trước khi bắt đầu code (10 phút, cả nhóm):** điền nhanh [`docs/blueprint-template.md`](docs/blueprint-template.md) (ai gửi request, request đi qua thành phần nào, log/metric/span cần gì, PII có thể ở đâu). Đây là khung tư duy dùng lại được cho `submission/REPORT.md`, không phải giấy tờ thủ tục — làm nó trước sẽ giúp A/B/C/D không đá nhau khi code.

---

## 1. Checkpoint 0 (0:00–0:30) — Setup & baseline — cả nhóm

Mỗi người tự làm theo [SETUP.md](SETUP.md) trên máy mình:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

- Điền `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` bằng project chung Lab Coach cấp (hoặc Langfuse Cloud). Không commit `.env` (đã có trong `.gitignore`).
- Chạy thử: `uvicorn app.main:app --reload --env-file .env`, terminal khác chạy `python scripts/load_test.py`, kiểm tra `data/logs.jsonl` sinh ra.
- Chạy baseline: `python scripts/validate_logs.py` và `python scripts/validate_dashboard.py` — lưu kết quả (baseline sẽ thấp vì các TODO chưa được làm, đây là điểm khởi đầu, không phải lỗi).
- **E** xác nhận cả nhóm cùng trỏ vào một project Langfuse (để trace/prompt version của tất cả mọi người gộp chung, đủ ≥10 traces).
- **E** kiểm tra `/health` trả `ok: true` trên máy demo cuối cùng sẽ dùng để chấm.

Đầu ra: mỗi người có API chạy được, `data/logs.jsonl` có dữ liệu, điểm baseline của `validate_logs.py` đã ghi lại.

---

## 2. Checkpoint 1 (0:30–1:30) — Logging & PII

### 2.1 Thành viên A — Middleware, Correlation ID, Exception handler

File: [`app/middleware.py`](app/middleware.py) — 4 TODO trong `CorrelationIdMiddleware.dispatch`:

1. `clear_contextvars()` ngay đầu `dispatch` — bắt buộc, nếu không context của request trước sẽ rò rỉ sang request sau (structlog contextvars là global theo thread/task).
2. Lấy `x-request-id` từ header nếu client đã gửi, nếu không thì tự sinh theo đúng format `req-<8 ký tự hex>` (gợi ý: `uuid.uuid4().hex[:8]`).
3. `bind_contextvars(correlation_id=correlation_id)` — để mọi `log.info(...)` gọi sau đó trong cùng request tự động có field `correlation_id` mà không cần truyền tay.
4. Sau khi có `response` từ `call_next`, gắn lại `response.headers["x-request-id"]` và `response.headers["x-response-time-ms"]` (dùng `time.perf_counter() - start`).

File: [`app/main.py`](app/main.py) dòng 47 — trong handler `chat()`, trước dòng `log.info("request_received", ...)`, cần `bind_contextvars(...)` thêm: `user_id_hash=hash_user_id(body.user_id)` (dùng hàm có sẵn trong `app/pii.py`), `session_id=body.session_id`, `feature=body.feature`, `model=agent.model`, `env=os.getenv("APP_ENV")`. Đây chính là 4 field `validate_logs.py` kiểm tra ở mục "enrichment" (`user_id_hash, session_id, feature, model`).

**Phần mở rộng — exception handler:** khối `try/except` trong `chat()` hiện đã bắt lỗi *bên trong* logic agent và log `request_failed` đúng cách. Khoảng trống còn lại: nếu request gửi JSON sai schema (Pydantic validation lỗi 422), lỗi xảy ra *trước khi* vào được thân hàm `chat()`, nên sẽ không có log `request_failed` nào được ghi — middleware vẫn chạy nên vẫn có `x-request-id`, nhưng log thì thiếu. Đề xuất: thêm một global exception handler bằng `@app.exception_handler(RequestValidationError)` (và có thể `@app.exception_handler(Exception)` cho lỗi không lường trước) để log thống nhất kèm `correlation_id`, tránh có request "vô hình" không xuất hiện trong log/metrics.

**Tự kiểm tra:** `python scripts/validate_logs.py` → mục "Records with missing enrichment" = 0, "Unique correlation IDs" ≥ 2; response của `/chat` có header `x-request-id`.

### 2.2 Thành viên B — PII Scrubbing

File: [`app/pii.py`](app/pii.py) dòng 11 — bổ sung thêm pattern vào `PII_PATTERNS` (hiện đã có `email`, `phone_vn`, `cccd`, `credit_card`). Gợi ý bổ sung:
- Số hộ chiếu Việt Nam (thường 1 chữ cái + 7 chữ số, ví dụ `B1234567`).
- Từ khóa địa chỉ (`Đường`, `Phường`, `Quận`, `Thôn`, `Xã` kèm số nhà) nếu muốn redact địa chỉ cụ thể.
- Kiểm tra lại `cccd` (`\b\d{12}\b`) có bắt nhầm số điện thoại/số khác không — vì `phone_vn` chạy trước nên số điện thoại 10 số thường không đụng, nhưng cần test với vài chuỗi số 12 chữ số bất kỳ để chắc không có false positive nghiêm trọng.

File: [`app/logging_config.py`](app/logging_config.py) dòng 45–46 — **đây là phần quan trọng nhất, thiếu nó thì PII không bao giờ được che dù `scrub_text` đúng**: uncomment và đăng ký hàm `scrub_event` vào pipeline `structlog.configure(processors=[...])`, đặt **trước** `JsonlFileProcessor()` (vì `JsonlFileProcessor` là nơi render JSON và ghi xuống file — redact phải xảy ra trước bước này, không phải sau).

**Tự kiểm tra:**
- Gửi thử một request có email/số điện thoại/số thẻ giả trong `message`, xem `data/logs.jsonl` — không được xuất hiện chuỗi gốc, chỉ thấy `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, v.v.
- `python scripts/validate_logs.py` → "Potential PII leaks detected: 0".
- `python -m pytest tests/test_pii.py -q`.

**Cả A và B cùng chịu trách nhiệm đạt mốc CP1:** `validate_logs.py` ≥ 80/100.

---

## 3. Checkpoint 2 (1:30–2:30) — Metrics, Dashboard, SLO, Alert, Tracing & Prompt Version

### 3.1 Thành viên C — Metrics & Dashboard (đo `error_rate_pct` + spec 6 panel)

`config/dashboard.yaml` đã là **contract hoàn chỉnh, không được sửa** — việc của C là *dựng dashboard thật* đọc từ `data/logs.jsonl` khớp đúng contract này, không phải sửa file yaml.

Mapping bắt buộc (đã định nghĩa sẵn trong yaml + [`docs/DASHBOARD_SETUP.md`](docs/DASHBOARD_SETUP.md)):

| Panel | Nguồn field | Phép tính | Threshold |
|---|---|---|---|
| latency | `response_sent.latency_ms` | P50/P95/P99 | P95 ≤ 3000ms |
| traffic | `request_received` | count/phút | ≥ 1 req/phút |
| errors | `request_received`, `request_failed`, `error_type` | `error_rate_pct` + breakdown | ≤ 2% |
| cost | `response_sent.cost_usd` | tổng theo phút + toàn cửa sổ | ≤ 2.5 USD |
| tokens | `response_sent.tokens_in/out` | tổng | ≤ 50,000 |
| quality | `response_sent.quality_score` | mean | ≥ 0.75 |

**Lưu ý kỹ thuật về `error_rate_pct`:** endpoint `/metrics` (`app/metrics.py`) **không đủ để tính đúng** chỉ số này — biến `TRAFFIC` chỉ tăng khi `metrics.record_request()` được gọi, mà hàm này chỉ chạy khi agent chạy **thành công**; khi request lỗi (ví dụ do incident `tool_fail`), `record_request` không được gọi nên mẫu số bị thiếu. Vì vậy phải tính trực tiếp từ `data/logs.jsonl` như contract yêu cầu (`source: data/logs.jsonl`): `count(event == "request_failed") / count(event == "request_received") * 100`.

Công cụ dựng dashboard tự chọn (Streamlit, notebook, Grafana...). Không có Streamlit sẵn trong `requirements.txt` — nếu chọn Streamlit thì `pip install streamlit pandas` thêm (không bắt buộc phải dùng Streamlit).

Quy trình:
1. Chờ A/B xong CP1 (dashboard cần log sạch, có `feature`, `latency_ms`...).
2. `python scripts/load_test.py --concurrency 5` để có đủ dữ liệu baseline.
3. Dựng đúng 6 panel, đặt tên/đơn vị/threshold giống contract, time range 60 phút, refresh 15–30s.
4. `python scripts/validate_dashboard.py` → phải in `HỢP LỆ: 6/6 panel`.
5. Kiểm tra runtime (theo [DASHBOARD_SETUP.md](docs/DASHBOARD_SETUP.md)): chụp ảnh baseline → bật `python scripts/inject_incident.py --scenario rag_slow` → chạy lại load test → xác nhận panel latency tăng rõ → chụp ảnh → tắt bằng `--disable`.

Evidence: ảnh dashboard (thấy rõ tên panel, time range, đơn vị, threshold) + kết quả validator.

### 3.2 Thành viên D — SLO & Alerts

File: [`config/slo.yaml`](config/slo.yaml) — đã có object mẫu nhưng `latency_p95_ms` còn ghi chú `note: Replace with your group's target`. D quyết định target chính thức của nhóm (có thể giữ 3000ms để khớp threshold dashboard, hoặc chọn số khác nếu có lý do — miễn giải thích được trong report) và xóa/ cập nhật ghi chú placeholder.

File: [`config/alert_rules.yaml`](config/alert_rules.yaml) — 3 alert đang là `TODO`. Điền `name`, `severity`, `condition`, `owner` (giữ nguyên `type: symptom-based` và `runbook: docs/alerts.md#alert-N` đã có sẵn). Gợi ý bám theo 3/4 SLI đã có sẵn trong `slo.yaml`:
- Alert 1: Latency P95 cao (điều kiện dựa trên SLO, không dựa tên hàm nội bộ, ví dụ "latency_p95_ms > 3000 trong 5 phút liên tục").
- Alert 2: Error rate cao (`error_rate_pct > 2% trong 5 phút`).
- Alert 3: Cost spike hoặc Quality giảm — chọn 1 trong 2 tùy triệu chứng nhóm thấy quan trọng hơn khi demo.

File: [`docs/alerts.md`](docs/alerts.md) — điền đầy đủ runbook cho từng alert ở trên (Tên, Severity, SLI/SLO liên quan, Điều kiện & thời gian duy trì, Ảnh hưởng người dùng, 3 bước kiểm tra đầu tiên, Mitigation tạm thời, Owner). Tên alert trong `alerts.md` phải khớp với `alert_rules.yaml` để hai file nhất quán (anchor `#alert-1/2/3` đã trỏ sẵn).

Evidence: `config/alert_rules.yaml` + `docs/alerts.md` hoàn chỉnh, dẫn lại trong `submission/REPORT.md` mục 5.

### 3.3 Thành viên E — Tracing, Prompt Versioning, bọc trace RAG/LLM (mở rộng)

Code nền (`app/agent.py`, `app/prompt_management.py`, `app/tracing.py`) đã viết đầy đủ, **không có TODO** — phần việc của E chủ yếu là thao tác trên Langfuse UI + chạy script, không phải sửa code, ngoại trừ phần mở rộng bên dưới.

1. Xác nhận `.env` có `LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST` hợp lệ, restart API, `/health` trả `tracing_enabled: true`.
2. Theo [`docs/PROMPT_VERSIONING.md`](docs/PROMPT_VERSIONING.md): tạo prompt text tên `day13-chat` trên Langfuse với 3 biến `{{feature}}`, `{{docs}}`, `{{message}}` — version 1 gắn label `baseline` + `production`, version 2 gắn label `candidate`.
3. Chạy cùng một input hai lần: đổi `.env` → `LANGFUSE_PROMPT_LABEL=baseline`, restart API, gửi request; đổi thành `candidate`, restart, gửi lại. Mở 2 trace, xác nhận metadata `prompt_name/prompt_label/prompt_version` khác nhau và đúng.
4. Đổi label `production` sang version 2, chạy 1 request; sau đó rollback `production` về version 1 — chụp ảnh trước/sau.
5. Chạy đủ traffic (lặp lại `python scripts/load_test.py`, có thể tăng `--concurrency`) để tổng số trace trên Langfuse ≥ 10, có metadata (`tags=["lab", feature, model]`, `user_id`, `session_id` đã được `agent.py` gắn sẵn).

**Phần mở rộng — bọc trace cho sub-component RAG/LLM:** hiện tại `LabAgent.run()` trong [`app/agent.py`](app/agent.py) chỉ có **một** span duy nhất (`@observe(as_type="generation")`) bao trùm cả bước `retrieve()` (RAG) lẫn bước gọi `self.llm.generate()`. Điều này có nghĩa là khi xem trace waterfall, không thể biết riêng bước RAG mất bao lâu so với bước LLM — mà incident chính thức của nhóm (`rag_slow`, xem mục 4) chính là RAG bị chậm. Đề xuất: thêm decorator `@observe()` (span mặc định, không cần `as_type="generation"`) lên hàm `retrieve()` trong [`app/mock_rag.py`](app/mock_rag.py) (Langfuse SDK tự lồng span con vào trace cha đang mở nhờ context truyền qua decorator). Sau khi làm, trace waterfall sẽ hiện rõ một span riêng cho retrieval — bằng chứng trực quan nhất cho CP3.

Evidence: danh sách ≥10 trace, 1 ảnh waterfall (có span RAG tách riêng), 2 trace ID của baseline/candidate, ảnh đổi label/rollback.

---

## 4. Checkpoint 3 (2:30–3:30) — Challenge chính thức — E dẫn dắt, cả nhóm hỗ trợ

**`config/challenge.json` đã được Lab Coach release sẵn trong repo** (không cần chờ thêm): `cohort: K4`, `challenge_id: day13-k4-observability-v1`, `incident: rag_slow`, `latency_threshold_ms: 2000`, `affected_feature: monitoring`, 5 câu hỏi practice. **Tuyệt đối không tự sửa file này** (RULES.md).

Điều kiện tiên quyết: CP1 (logging/PII) và CP2 (tracing có span RAG riêng, dashboard chạy được) phải xong trước — nếu không sẽ không có bằng chứng để điều tra.

Quy trình điều tra (E chủ trì, ghi lại từng bước làm evidence):

1. **Bật incident:** `python scripts/inject_incident.py` (không cần `--scenario`, script tự đọc `incident: rag_slow` từ `challenge.json`).
2. **Chạy input chính thức:** `python scripts/load_test.py --challenge --concurrency 5` (gửi 5 câu hỏi với `feature=monitoring`, thứ tự xáo trộn theo `seed: 1304`).
3. **Đọc triệu chứng từ metrics/dashboard:** panel latency (P95/P99) cho các request `feature=monitoring` sẽ tăng vọt — `mock_rag.retrieve()` bị `time.sleep(2.5)` cứng khi `rag_slow` bật, tức là mọi request loại này chắc chắn vượt `latency_threshold_ms=2000` và threshold dashboard 3000ms tùy tải.
4. **Khoanh vùng bằng trace:** mở Langfuse, tìm trace của các session `k4-challenge-s01`…`s05`. Nếu đã làm phần mở rộng ở mục 3.3, span `retrieve()` sẽ hiện riêng và chiếm phần lớn latency — đây là bằng chứng khoanh vùng span bất thường.
5. **Chứng minh bằng log:** lọc `data/logs.jsonl` theo `correlation_id` của các request chậm, đối chiếu `latency_ms`, `feature: "monitoring"` khớp với trace.
6. **Root cause:** bước truy hồi tài liệu (RAG) bị delay giả lập 2.5 giây/request (mô phỏng vector store/backend chậm) → vi phạm SLO latency của feature `monitoring`.
7. **Fix action đề xuất:** thêm timeout + fallback cho lời gọi retrieval, cache câu hỏi lặp lại, tối ưu/scale vector store, cân nhắc chạy song song retrieval với các bước không phụ thuộc.
8. **Preventive measure:** alert latency P95 tách riêng theo `feature` (phối hợp với alert của D), thêm synthetic/canary check định kỳ cho pipeline RAG, đặt budget latency riêng cho span retrieval.
9. **Tắt incident sau khi điều tra xong:** `python scripts/inject_incident.py --disable`.
10. Ghi lại toàn bộ: challenge ID, trace ID, correlation ID, số liệu metric cụ thể vào `submission/evidence/` và `submission/REPORT.md` mục 6 — mọi kết luận phải có bằng chứng cụ thể kèm theo (RULES.md), không được suy đoán chung chung.

---

## 5. Hoàn tất (3:30–4:00) — Báo cáo & Demo — E chủ trì, cả nhóm điền phần mình

- E tổng hợp [`submission/REPORT.md`](submission/REPORT.md) — các mục 2–6 lấy trực tiếp từ evidence của C (dashboard/metrics), A+B (logging/PII), E (trace/prompt version), D (SLO/alert), E+cả nhóm (challenge).
- **Mỗi thành viên tự điền dòng của mình ở mục 7 "Đóng góp cá nhân"** kèm link commit/PR cụ thể — đây là phần chấm điểm cá nhân (B2, 20 điểm), không được để trống hoặc chung chung.
- Checklist trước khi nộp (chạy trong bash/terminal):

```bash
python -m pytest -q
python scripts/validate_logs.py
python scripts/validate_dashboard.py
git status --short
```

- Kiểm tra `git status --short` không có `.env`, `.venv/`, `data/logs.jsonl`, `data/audit.jsonl` — các file này đã nằm trong `.gitignore` nhưng vẫn nên double-check trước khi push, đặc biệt nếu ai đó lỡ `git add -A` từ ngoài repo.
- Chuẩn bị demo đúng thứ tự: **Metrics (dashboard) → Traces (Langfuse waterfall) → Logs (log line + correlation ID) → Root cause & Fix** — đúng luồng RUBRIC A3 chấm.
- Mỗi người phải tự giải thích được phần mình làm khi được hỏi (RUBRIC B1 chấm riêng từng cá nhân về logging/tracing/prompt version/PII/percentile/alert).

---

## 6. Checklist evidence bắt buộc (tổng hợp từ SUBMISSION.md + docs/grading-evidence.md)

| Evidence | Người phụ trách |
|---|---|
| Kết quả cuối `validate_logs.py` | A, B |
| Log JSON có correlation ID + metadata | A |
| Log chứng minh PII đã redact | B |
| Danh sách ≥10 trace + 1 ảnh waterfall | E |
| 2 prompt version + trace đúng name/label/version | E |
| Ảnh đổi label/rollback prompt | E |
| Kết quả `validate_dashboard.py` + ảnh dashboard đủ 6 panel | C |
| SLO, alert rules, runbook hoàn thiện | D |
| Bằng chứng điều tra challenge (metric + trace ID + log line) | E (chủ trì), cả nhóm hỗ trợ |
| `submission/REPORT.md` đầy đủ 7 mục | E tổng hợp, mỗi người tự điền mục 7 |

## 7. Việc riêng của trưởng nhóm (E)

- Điều phối tiến độ theo đúng mốc thời gian trong `CHECKPOINTS.md`, nhắc trước 10–15 phút khi sắp hết giờ mỗi Checkpoint.
- Đảm bảo cả nhóm dùng chung một project Langfuse (để tổng trace/prompt version gộp đủ số lượng yêu cầu).
- Chạy `load_test.py` nhiều lần trong CP2 để cung cấp đủ dữ liệu cho C dựng dashboard và D kiểm tra alert.
- Dẫn dắt điều tra CP3 theo đúng quy trình mục 4, đảm bảo mọi kết luận đều có evidence cụ thể (trace ID/log line/metric), không suy đoán.
- Tổng hợp `submission/REPORT.md`, rà soát không lộ secret/PII trong Git trước khi nộp, chuẩn bị và dẫn demo cuối buổi.

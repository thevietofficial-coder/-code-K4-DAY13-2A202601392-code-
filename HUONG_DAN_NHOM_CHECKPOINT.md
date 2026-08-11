# Kế hoạch hoàn thành Day 13 Observability — Nhóm 5 thành viên

> Dành cho trưởng nhóm kiêm **Thành viên E — QA & Chief Investigator**.  
> Tài liệu này được lập từ toàn bộ mã nguồn, test, cấu hình, dữ liệu và tài liệu hiện có trong repository.

## 1. Mục tiêu cuối cùng của nhóm

Nhóm chỉ được xem là hoàn thành khi đồng thời có đủ:

- API chạy được; `/health` trả `ok: true` và `/metrics` trả metrics.
- Structured JSON log có correlation ID, metadata và không lộ PII.
- `python scripts/validate_logs.py` đạt tối thiểu **80/100**, nên hướng tới 100/100.
- Tối thiểu **10 trace thật** trên Langfuse, có metadata và trace waterfall.
- Prompt `day13-chat` có v1/v2, label, trace gắn đúng version và evidence rollback.
- Dashboard runtime đủ đúng **6 nhóm chỉ số**, có đơn vị, time range và threshold/SLO line.
- `python scripts/validate_dashboard.py` báo `HỢP LỆ: 6/6 panel`.
- `config/slo.yaml`, `config/alert_rules.yaml` và `docs/alerts.md` hoàn chỉnh.
- Challenge chính thức được điều tra theo chuỗi **Metrics → Traces → Logs → Root cause**.
- `submission/REPORT.md`, evidence, test và lịch sử Git khớp với đóng góp từng người.

## 2. Việc trưởng nhóm phải xử lý ngay trước CP0

### 2.1. Xử lý bảo mật

File `.env` hiện chứa credential Langfuse có giá trị. Vì secret đã xuất hiện trong workspace, trưởng nhóm cần:

1. Thu hồi/rotate cặp key hiện tại trên Langfuse.
2. Tạo key mới và chỉ lưu trong `.env` local.
3. Kiểm tra `.env` vẫn nằm trong `.gitignore`.
4. Kiểm tra lịch sử Git; nếu secret từng được commit thì báo Lab Coach và làm sạch lịch sử theo hướng dẫn của Coach.
5. Không chụp màn hình để lộ key và không copy key vào report/chat/commit.

Ngoài ra, `.env` hiện dùng `LANGFUSE_BASE_URL`, trong khi `.env.example`, `SETUP.md` và luồng cấu hình của bài dùng `LANGFUSE_HOST`. Hãy đổi sang `LANGFUSE_HOST=...`, sau đó khởi động lại API và xác nhận `/health` báo `tracing_enabled: true`.

### 2.2. Quy ước phối hợp

- Mỗi người làm trên branch riêng: `member-a/...` đến `member-e/...`.
- Mỗi commit chỉ chứa một thay đổi có thể giải thích; không gom toàn bộ bài vào một commit của trưởng nhóm.
- Mỗi người tự ghi commit SHA/PR và evidence của phần mình vào bảng bàn giao.
- Mọi ảnh đặt trong `submission/evidence/`, tên gợi ý: `cp1-a-correlation.png`, `cp1-b-pii.png`, `cp2-c-dashboard.png`, `cp2-d-alerts.png`, `cp3-e-investigation.png`.
- Không sửa hoặc tự tạo lại `config/challenge.json`. File hiện có là challenge K4 đã được release; giữ nguyên nội dung.
- Không xóa log lỗi, làm giả trace hoặc hard-code kết quả validator.

## 3. Ma trận trách nhiệm

| Thành viên | Owner chính | File/phạm vi | Bàn giao bắt buộc |
|---|---|---|---|
| A — API & Middleware | Correlation ID, context log, exception handler | `app/middleware.py`, `app/main.py`, test liên quan | Log của cùng request có cùng ID; response header có ID/thời gian; lỗi có log an toàn |
| B — Security | PII scrub và kiểm chứng leak | `app/pii.py`, `app/logging_config.py`, test PII | Regex/test; processor chạy trước render; evidence 0 PII leak |
| C — Metrics & Dashboard | Error rate và 6 panel | `app/metrics.py`, `config/dashboard.yaml`, dashboard runtime | `/metrics` có `error_rate_pct`; validator 6/6; ảnh 6 panel |
| D — SRE & Alerts | SLO, alert, runbook | `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md` | SLO có lý do; 3 alert hợp lệ; runbook thao tác được |
| E — QA & Chief Investigator | Load test, span RAG/LLM, challenge, report | `scripts/load_test.py`, `app/agent.py`, `app/mock_rag.py`, `app/mock_llm.py`, `submission/` | Kết quả test/load; trace waterfall; điều tra có ID/log/metric; report cuối |

## 4. Checkpoint 0 — 0:00–0:30: Setup và baseline

### Cả nhóm

1. Tạo/activate Python 3.11 virtual environment và cài `requirements.txt`.
2. Cấu hình key Langfuse đã rotate trong `.env`; không commit file này.
3. Terminal 1 chạy:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --env-file .env
   ```

4. Terminal 2 chạy baseline:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python scripts/load_test.py
   python scripts/validate_logs.py
   python scripts/validate_dashboard.py
   python -m pytest -q
   ```

5. Lưu output baseline vào evidence hoặc ghi nguyên kết quả vào report; chưa sửa số liệu.

### Phân công CP0

- **A:** kiểm tra `/health`, `/chat`, response headers và quan sát `correlation_id` hiện đang là `MISSING` để xác nhận baseline.
- **B:** đưa email, số điện thoại, CCCD và thẻ test vào request; ghi lại PII leak baseline.
- **C:** đọc `/metrics`, đối chiếu các field với sáu panel và lưu giá trị latency/error/cost baseline.
- **D:** rà `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md`; liệt kê TODO và ngưỡng cần thống nhất.
- **E:** chạy toàn bộ test/load, lập bảng pass/fail, kiểm tra Langfuse có trace thật, tạo danh mục evidence chung.

### Gate CP0

- API và load test chạy được.
- Có `data/logs.jsonl`.
- Có kết quả baseline của pytest, log validator và dashboard validator.
- Không ai bắt đầu challenge khi các signal cơ bản chưa dùng được.

## 5. Checkpoint 1 — 0:30–1:30: Logging và PII

### Thành viên A — API & Middleware

Trong `app/middleware.py`:

1. Gọi `clear_contextvars()` ở đầu mỗi request để tránh rò context giữa request đồng thời.
2. Đọc `x-request-id`; chỉ chấp nhận format hợp lệ `req-<8 ký tự hex>`, nếu thiếu/sai thì sinh `req-{uuid.uuid4().hex[:8]}`.
3. `bind_contextvars(correlation_id=correlation_id)` trước `call_next`.
4. Gán `request.state.correlation_id`.
5. Trả `x-request-id` và `x-response-time-ms` trong response.
6. Bảo đảm cả đường lỗi cũng có correlation ID/header; nên dùng `try/finally` hoặc exception handler phù hợp.

Trong `app/main.py`:

1. Trước `request_received`, bind: `user_id_hash`, `session_id`, `feature`, `model`, `env`.
2. Không bind raw `user_id` hay raw message.
3. Bổ sung global exception handler nếu làm phần mở rộng: trả lỗi chung, log `error_type`, không trả stack trace/PII cho client.
4. Viết test cho ID do server sinh, ID hợp lệ do client truyền, hai request có ID khác nhau và lỗi vẫn truy vết được.

**Definition of Done của A:** mọi log `service=api` có đủ enrichment; cùng một request nối được request/response/error bằng correlation ID; response trả cùng ID.

### Thành viên B — Security Engineer

Trong `app/pii.py` và `app/logging_config.py`:

1. Rà regex email, điện thoại VN, CCCD, credit card; thêm passport/địa chỉ nếu nhóm chọn phần mở rộng.
2. Ưu tiên regex có boundary để tránh che nhầm token, timestamp hoặc số hợp lệ khác.
3. Bật `scrub_event` trong processor chain **trước** `JsonlFileProcessor` và `JSONRenderer`.
4. Kiểm tra PII trong cả `event`, mọi string trong `payload`, message preview và exception detail. Nếu payload lồng nhau, mở rộng scrub đệ quy và thêm test.
5. Thêm test positive/negative cho từng loại PII và các format điện thoại đã có trong public test.
6. Chạy request chứa dữ liệu test, sau đó tìm raw value trong `data/logs.jsonl`; kết quả phải bằng 0.

**Definition of Done của B:** `validate_logs.py` báo `Potential PII leaks detected: 0`; test PII pass; ảnh evidence chỉ chứa placeholder `[REDACTED_...]`.

### Thành viên C, D, E hỗ trợ CP1

- **C:** xác nhận `request_received`, `response_sent`, `request_failed` đủ dữ liệu để tính traffic/error.
- **D:** xác nhận log lỗi chứa dữ liệu vận hành cần thiết nhưng không lộ PII.
- **E:** chạy test đồng thời (`--concurrency 5`) để phát hiện context leakage; nghiệm thu output A/B và chụp evidence.

### Gate CP1

```powershell
python -m pytest -q
python scripts/load_test.py --concurrency 5
python scripts/validate_logs.py
```

Yêu cầu: tối thiểu 80/100, mục tiêu 100/100; ít nhất 2 correlation ID; enrichment không thiếu; PII leak bằng 0.

## 6. Checkpoint 2 — 1:30–2:30: Metrics, traces, prompt, dashboard, SLO và alerts

### Thành viên C — Metrics & Dashboard

1. Bổ sung `error_rate_pct` vào `app/metrics.py`/`snapshot()` theo contract:

   ```text
   error_rate_pct = số request_failed / số request_received * 100
   ```

   Cần thống nhất mẫu số. Vì `TRAFFIC` hiện tăng trong `record_request()` sau khi agent thành công, lỗi có thể không nằm trong traffic. C nên sửa cách đếm để tổng request bao gồm cả thành công lẫn thất bại, tránh error rate sai.

2. Thêm test: chưa có request → 0%; success-only → 0%; có lỗi → tỷ lệ đúng; không chia cho 0.
3. Dùng `data/logs.jsonl` làm nguồn chuẩn và dựng đúng sáu panel:
   - Latency: `response_sent.latency_ms`, P50/P95/P99, ms, P95 ≤ 3000.
   - Traffic: `request_received`, count/rate mỗi phút.
   - Errors: error rate và breakdown `error_type`, ≤ 2%.
   - Cost: tổng theo phút/toàn cửa sổ, USD, ≤ 2.5.
   - Tokens: tổng input/output, tokens, ≤ 50000.
   - Quality: mean `quality_score`, thang 0–1, ≥ 0.75.
4. Giữ time range 60 phút, refresh 30 giây, hiển thị threshold và đơn vị.
5. Chạy validator và chụp cả dashboard baseline lẫn dashboard khi practice `rag_slow`.

**Definition of Done của C:** `/metrics` có error rate đúng; validator 6/6; dashboard runtime thật đủ sáu panel và phản ứng khi incident bật.

### Thành viên D — SRE & Alerts Engineer

1. Hoàn thiện `config/slo.yaml`; ghi lý do cho target, đặc biệt latency P95 3000 ms, error rate 2%, cost 2.5 USD, quality 0.75.
2. Thay toàn bộ TODO trong `config/alert_rules.yaml` bằng ba alert hướng triệu chứng/SLO, ví dụ:
   - P95 latency vượt 3000 ms trong 5 phút — warning/critical theo mức vượt.
   - Error rate vượt 2% trong 5 phút — critical.
   - Cost hoặc quality vi phạm ngưỡng trong cửa sổ phù hợp — warning.
3. Không đặt điều kiện alert trực tiếp theo implementation như `rag_slow == true`; alert phải phản ánh ảnh hưởng người dùng.
4. Điền đủ `docs/alerts.md`: SLI/SLO, duration, ảnh hưởng, ba bước kiểm tra, mitigation, owner.
5. Ba bước kiểm tra đầu tiên phải dẫn được từ dashboard → trace bất thường → log cùng correlation ID.
6. Thử runbook bằng practice incident và sửa bước nào không thực thi được.

**Definition of Done của D:** YAML không còn TODO; mỗi alert có condition, duration, severity, owner, link runbook; runbook được E dry-run thành công.

### Thành viên E — trace RAG/LLM, load test và QA

1. Bọc trace cho sub-component để waterfall tách rõ:
   - RAG `retrieve`: span/tool observation, không capture raw PII.
   - LLM `generate`: generation observation; model, token usage, cost và latency.
   - Parent `LabAgent.run` vẫn liên kết cùng trace.
2. Không ghi raw prompt/message chứa PII; dùng `capture_input=False`, `capture_output=False` hoặc sanitized metadata.
3. Chạy ít nhất hai lượt load test đủ tạo ≥10 trace. Vì file sample/challenge có số query hữu hạn, đếm trace thật trên Langfuse, không suy đoán từ số lần chạy.
4. Kiểm tra mỗi trace có `user_id` đã hash, `session_id`, tags và metadata `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`.
5. Chọn một trace waterfall có parent → RAG → LLM và lưu trace ID/evidence.
6. Phối hợp tạo prompt:
   - v1: labels `baseline`, `production`.
   - v2: label `candidate`.
   - Cùng input chạy với baseline và candidate.
   - Chuyển production sang v2, chạy một request, rồi rollback production về v1.
   - Lưu hai trace ID và ảnh trước/sau rollback.
7. Dry-run `rag_slow`: ghi baseline P95, bật incident, chạy lại cùng concurrency/input, xác nhận P95 và RAG span tăng, rồi tắt incident.

### Gate CP2

```powershell
python -m pytest -q
python scripts/validate_dashboard.py
python scripts/load_test.py --concurrency 5
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 5
python scripts/inject_incident.py --scenario rag_slow --disable
```

Phải có: ≥10 trace; waterfall RAG/LLM; prompt v1/v2 + rollback; validator 6/6; ảnh dashboard; SLO/alert/runbook hoàn chỉnh.

## 7. Checkpoint 3 — 2:30–3:30: Challenge chính thức

Challenge hiện tại có ID `day13-k4-observability-v1`, incident `rag_slow`, feature bị ảnh hưởng `monitoring`, threshold 2000 ms. Không sửa file để khai thác thông tin khác hoặc thay kết quả.

### Quy trình do E dẫn dắt

1. Xác nhận mọi practice incident đã tắt và ghi trạng thái `/health`.
2. Ghi timestamp bắt đầu và snapshot `/metrics`/dashboard trước challenge.
3. Bật incident chính thức và chạy input chính thức:

   ```powershell
   python scripts/inject_incident.py
   python scripts/load_test.py --challenge --concurrency 5
   ```

4. **Metrics — C cung cấp:** xác định P95/P99 tăng bao nhiêu, feature/cửa sổ nào bị ảnh hưởng; lưu ảnh và số cụ thể.
5. **Traces — E điều tra:** lọc trace trong cửa sổ, chọn trace vượt 2000 ms, ghi trace ID; so waterfall và xác định RAG span khoảng 2.5 giây là phần bất thường, trong khi LLM khoảng 0.15 giây.
6. **Logs — A/B hỗ trợ:** dùng correlation ID của request để tìm `request_received`/`response_sent`; ghi log line, latency và metadata. Không kết luận chỉ từ tên scenario.
7. **Root cause:** chỉ ghi sau khi cả ba lớp khớp. Với evidence hiện có, kết luận dự kiến là retrieval bị delay khi incident bật; phải thay số liệu và ID dự kiến bằng evidence runtime thật.
8. **D đề xuất mitigation:** tạm giảm tải/fallback/bypass retrieval theo chính sách; đặt timeout/circuit breaker nếu phù hợp.
9. **Preventive measure:** alert P95, sub-span instrumentation, timeout/retry budget, performance regression/load test trước release.
10. Tắt incident chính thức sau khi thu evidence:

    ```powershell
    python scripts/inject_incident.py --disable
    ```

11. Chạy lại một lượt để chứng minh phục hồi; lưu P95 sau khôi phục.

### Gate CP3

Không chấp nhận câu “RAG chậm” nếu thiếu ít nhất: metric cụ thể + trace ID + RAG span duration + correlation ID/log line + fix + preventive measure.

## 8. Hoàn tất — 3:30–4:00: Report, Git và demo

### E chịu trách nhiệm chính

1. Điền đầy đủ `submission/REPORT.md`, không để dòng placeholder.
2. Kiểm tra mỗi nhận định kỹ thuật dẫn tới một file evidence hoặc ID kiểm chứng được.
3. Điền đóng góp từng người đúng commit/PR; yêu cầu mỗi người tự xác nhận nội dung “Điều đã học”.
4. Chuẩn bị demo 5–7 phút:
   - 30 giây: health và kiến trúc signal.
   - 60 giây: log correlation + PII redaction.
   - 60 giây: dashboard sáu panel và SLO/alert.
   - 2 phút: Metrics → trace waterfall → log → root cause.
   - 60 giây: prompt version/rollback.
   - 30 giây: fix, prevention và trạng thái test.
5. Chạy kiểm tra cuối:

   ```powershell
   python -m pytest -q
   python scripts/validate_logs.py
   python scripts/validate_dashboard.py
   git status --short
   git grep -n -I -E "(sk-lf-|pk-lf-|LANGFUSE_SECRET_KEY=.*[^=]$)" -- . ":(exclude).env.example"
   ```

6. Kiểm tra thủ công evidence không lộ key, raw PII, email cá nhân hoặc số điện thoại.
7. Push repo và ghi đúng repository URL + commit SHA cuối vào report/hệ thống Codelabs.

## 9. Checklist cá nhân của bạn — Thành viên E

### Trước khi code

- [ ] Rotate key bị lộ và sửa biến `LANGFUSE_HOST`.
- [ ] Tạo bảng baseline test/validator/load test.
- [ ] Tạo danh mục/tên file evidence.
- [ ] Chốt Definition of Done và branch/commit cho A–D.

### Phần kỹ thuật trực tiếp của E

- [ ] Bọc RAG span và LLM generation, giữ an toàn PII.
- [ ] Test trace adapter và quan hệ parent/sub-component.
- [ ] Chạy load test baseline/concurrency; tạo và đếm ≥10 trace thật.
- [ ] Chứng minh trace metadata và waterfall đầy đủ.
- [ ] Tạo/kiểm tra prompt v1/v2, label switch và rollback evidence.
- [ ] Dry-run practice incident và runbook trước challenge.

### Điều tra CP3

- [ ] Ghi timestamp và baseline.
- [ ] Chạy đúng challenge K4, không sửa config.
- [ ] Ghi metric symptom cụ thể.
- [ ] Chọn trace ID chậm và đo từng span.
- [ ] Tìm log bằng correlation ID.
- [ ] Viết root cause dựa trên evidence.
- [ ] Ghi fix action, mitigation và preventive measure.
- [ ] Tắt incident và chứng minh phục hồi.

### Report và bảo vệ cá nhân

- [ ] Report dẫn đúng mọi evidence.
- [ ] Commit/PR của E thể hiện load/trace/investigation/report, không nhận thay phần người khác.
- [ ] Có thể giải thích: average vs P95/P99; trace ID vs correlation ID; vì sao scrub trước JSON render; error-rate denominator; alert condition/duration; bằng chứng đủ cho root cause.
- [ ] Có thể demo trực tiếp Metrics → Traces → Logs mà không phụ thuộc ảnh tĩnh.

## 10. Bảng bàn giao để trưởng nhóm theo dõi

| Gate | Owner | Kết quả/giá trị | Evidence | Commit/PR | E duyệt |
|---|---|---|---|---|---|
| CP0 health/baseline | E | | | | ☐ |
| CP1 correlation/enrichment | A | | | | ☐ |
| CP1 PII leak = 0 | B | | | | ☐ |
| CP2 error rate + 6 panel | C | | | | ☐ |
| CP2 SLO/3 alert/runbook | D | | | | ☐ |
| CP2 ≥10 trace + waterfall | E | | | | ☐ |
| CP2 prompt v1/v2/rollback | E | | | | ☐ |
| CP3 metric/trace/log/root cause | E + cả nhóm | | | | ☐ |
| Final tests/security/report | E | | | | ☐ |

## 11. Các lỗi dễ mất điểm cần tránh

- Validator 6/6 chỉ chứng minh YAML đúng contract, không thay thế ảnh dashboard runtime.
- `validate_logs.py` 100/100 không thay thế trace, prompt rollback, SLO, alert và challenge evidence.
- Không dùng `TRAFFIC` chỉ đếm success làm mẫu số error rate.
- Không dùng average latency thay P95/P99 để điều tra tail latency.
- Không kết luận từ `config/challenge.json`; phải chứng minh bằng dữ liệu runtime.
- Không để trace ghi `prompt_source=local-fallback` rồi khai là managed prompt thành công.
- Không chụp key/PII và không commit `.env`, `.venv`, cache hay log nhạy cảm.
- Không để trưởng nhóm commit thay tất cả; rubric cá nhân yêu cầu contribution kiểm chứng được.

# CP2 Evidence — Tracing & Prompt Versioning (Thành viên E)

Nguồn: Langfuse project (`day13-chat`), truy vấn qua Langfuse Python SDK vào 2026-08-11.

**Tái xác minh 2026-08-11 (sau khi có báo cáo lỗi 401):** đã chạy lại `client.api.trace.get()` cho cả 4 trace ID ở mục 2–3 và `client.api.trace.list(tags="lab")` — kết nối Langfuse hoạt động bình thường, cả 4 trace vẫn trả đúng `prompt_version`/`prompt_label`/observations như ghi nhận ban đầu, tổng số trace tag `lab` hiện là **50** (bị chặn ở `limit=50`, số thực tế còn cao hơn vì cả nhóm vẫn đang test). Dòng lỗi `Failed to export span batch code: 401` xuất hiện khi chạy `pytest` là do `tests/test_agent_prompt_trace.py` monkeypatch key giả (`test-public-key`/`test-secret-key`) để cô lập unit test khỏi mạng thật — đây là cảnh báo vô hại từ background exporter khi shutdown, không phải lỗi kết nối với project Langfuse thật, và không ảnh hưởng tới các trace ID liệt kê trong file này.

## 1. Prompt versions trên Langfuse

Prompt `day13-chat`, biến `{{feature}}`, `{{docs}}`, `{{message}}`:

| Version | Nội dung | Label |
|---|---|---|
| 1 | `Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}` | `baseline` (ban đầu cũng có `production`, xem mục 3) |
| 2 | v1 + `\n\nAnswer in at most 3 concise sentences.` | `candidate` |

Trạng thái label cuối cùng sau khi rollback: `production` → version 1, `baseline` → version 1, `candidate` → version 2.

## 2. Hai trace ID chứng minh hai version/label khác nhau

Cùng một input: *"Explain the observability workflow for an AI API in one short paragraph."*

| Label chạy | Trace ID | `prompt_name` | `prompt_label` | `prompt_version` | `prompt_source` |
|---|---|---|---|---|---|
| `baseline` | `737d560702c7f58cf9fcb7ac6f563d13` | day13-chat | baseline | 1 | langfuse |
| `candidate` | `f998e11004eb1af0d9642f7b7278822c` | day13-chat | candidate | 2 | langfuse |

Trace URL (thay `<host>` bằng `LANGFUSE_HOST` trong `.env`, mặc định `cloud.langfuse.com`):
`https://cloud.langfuse.com/trace/737d560702c7f58cf9fcb7ac6f563d13`
`https://cloud.langfuse.com/trace/f998e11004eb1af0d9642f7b7278822c`

## 3. Đổi label `production` sang v2 rồi rollback về v1

Trình tự thao tác qua `client.update_prompt(name="day13-chat", version=..., new_labels=["production"])`:

1. Trước khi đổi: `production` → version 1.
2. `update_prompt(version=2, new_labels=["production"])` → `production` → version 2. Chạy 1 request cùng input, được trace `fa93db2f3e2beab28fa44dda968e4358`, metadata xác nhận `prompt_version=2`, `prompt_label=production`.
3. Rollback: `update_prompt(version=1, new_labels=["production"])` → `production` → version 1. Chạy lại request, được trace `61eaae867c8db9611495ea1fc0ff51c8`, metadata xác nhận `prompt_version=1`, `prompt_label=production`.

| Bước | Trace ID | `prompt_version` | `prompt_label` |
|---|---|---|---|
| Sau khi chuyển production sang v2 | `fa93db2f3e2beab28fa44dda968e4358` | 2 | production |
| Sau khi rollback production về v1 | `61eaae867c8db9611495ea1fc0ff51c8` | 1 | production |

**Còn thiếu:** ảnh chụp màn hình Langfuse UI (trang Prompts, tab Versions/Labels) trước/sau khi đổi label — cần chụp thủ công vì không thể tự động chụp UI. Mở `https://cloud.langfuse.com` → Prompts → `day13-chat` để lấy ảnh.

## 4. Sub-span RAG/LLM (phần mở rộng của E)

`app/mock_rag.py:retrieve()` và `app/mock_llm.py:FakeLLM.generate()` đã được bọc bằng `@observe(...)` riêng (xem diff trong repo). Với trace `737d560702c7f58cf9fcb7ac6f563d13` ở trên, waterfall gồm 3 observation lồng nhau, xác nhận qua API:

```
run             (GENERATION)  <- span cha, toàn bộ LabAgent.run()
├─ llm.generate (GENERATION)  <- riêng bước gọi LLM
└─ rag.retrieve (SPAN)        <- riêng bước truy hồi tài liệu (RAG)
```

Đây là bằng chứng phục vụ điều tra CP3 (incident `rag_slow`): khi bật incident, span `rag.retrieve` sẽ phình to rõ rệt so với `llm.generate`, cho phép khoanh vùng root cause trực tiếp trên waterfall thay vì chỉ nhìn tổng latency.

**Còn thiếu:** ảnh chụp waterfall thật trong Langfuse UI (Trace detail page) cho 1 trong các trace ID ở trên.

## 5. Tổng số trace có metadata (≥10 theo yêu cầu CP2)

Truy vấn `client.api.trace.list(tags="lab")` trả về **50 trace** (giới hạn `limit=50`, số thực tế còn cao hơn) tính đến thời điểm tái xác minh, tất cả đều có `tags=["lab", <feature>, <model>]`, `session_id`, `user_id` (hashed) — vượt yêu cầu tối thiểu 10. Danh sách đầy đủ (id | session | tags | timestamp) được in ra khi chạy script; xem log chạy trong buổi làm bài hoặc truy vấn lại bằng:

```python
client.api.trace.list(tags="lab", limit=30, order_by="timestamp.desc")
```

10 trace gần nhất từ lần chạy `python scripts/load_test.py` (feature qa/summary, session s01–s10):

- `006230d6edfb0ccc800d42700fb5c97f` (s10, qa)
- `55e0f17f17334cc9746020484d6d613a` (s09, qa)
- `714c41a6fafafda8d4c175e49bf7e5ac` (s08, qa)
- `2fe3a826ab5513f62dab43086f31e439` (s07, qa)
- `2318f99fd1401cc9f79dfc60f5cf7313` (s06, summary)
- `335b327ab2dfa6f0508d09c14bf0cd6d` (s05, qa)
- `855e86c841aac29af9205a26b7b316e6` (s04, qa)
- `14a8ef963ea0cc914cdb1523b9b979b4` (s03, summary)
- `f7df401ef07018fd57298ea01c233500` (s02, qa)
- `2bbe93433bb6c5c8a7e1a3507f5adf42` (s01, qa)

**Còn thiếu:** 1 ảnh chụp danh sách trace trong Langfuse UI (Traces tab, lọc theo tag `lab`) để nộp làm evidence trực quan.

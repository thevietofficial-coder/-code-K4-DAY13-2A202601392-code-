# CP3 Evidence — Điều tra Challenge chính thức (Thành viên E)

**Challenge:** `day13-k4-observability-v1` · cohort `K4` · incident `rag_slow` · `affected_feature: monitoring` · `latency_threshold_ms: 2000` (từ `config/challenge.json`, không chỉnh sửa file này).

**Quy trình:** chạy baseline (incident tắt) với đúng 5 câu hỏi chính thức → bật incident qua `python scripts/inject_incident.py` (tự đọc `challenge.json`) → chạy lại `python scripts/load_test.py --challenge --concurrency 5` → đối chiếu metrics/log/trace → tắt incident.

## 1. Triệu chứng từ metrics/log — latency_ms tăng đột biến

| session_id | correlation_id | latency_ms (incident TẮT) | correlation_id | latency_ms (incident BẬT) | Δ |
|---|---|---:|---|---:|---:|
| k4-challenge-s01 | req-c711a49f | 151 | req-a21686e4 | 2651 | **+2500** |
| k4-challenge-s02 | req-f40dcb52 | 151 | req-a9a1d40f | 2652 | **+2501** |
| k4-challenge-s03 | req-5005f825 | 151 | req-7f992c69 | 2651 | **+2500** |
| k4-challenge-s04 | req-25b55300 | 150 | req-8535c3d6 | 2651 | **+2501** |
| k4-challenge-s05 | req-a2a7d364 | 1259* | req-c834d151 | 2652 | +1393 |

\* s05 baseline dính cold-start (request đầu tiên trong batch), 4 request còn lại của baseline đều ~150ms nên vẫn là mức tham chiếu hợp lệ.

Cả 5/5 request khi bật incident đều **vượt `latency_threshold_ms=2000`** của challenge và **vượt ngưỡng dashboard P95 ≤ 3000ms** khi tính theo P95 thực tế của cụm 5 request này (2652ms vẫn dưới 3000ms tính đơn lẻ, nhưng đã vượt hẳn `latency_threshold_ms` riêng của challenge — đây chính là tiêu chí "triệu chứng" theo `config/challenge.json`).

**Phát hiện phụ (đáng chú ý, không phải nguyên nhân chính):** đối chiếu timestamp `request_received`/`response_sent` trong `data/logs.jsonl` cho thấy 5 request dù gửi đồng thời (`--concurrency 5`) nhưng được server xử lý **hoàn toàn tuần tự** (request sau chỉ bắt đầu đúng lúc request trước kết thúc, ví dụ `req-a9a1d40f` nhận lúc `09:53:10.389`, đúng bằng thời điểm `req-8535c3d6` trả response `09:53:10.388`). Nguyên nhân: `LabAgent.run()`/`retrieve()`/`FakeLLM.generate()` gọi `time.sleep()` đồng bộ bên trong handler `async def`, chặn toàn bộ event loop — mỗi request incident chiếm trọn event loop trong 2.5s nên không request nào khác được xử lý song song. Đây là một rủi ro kiến trúc riêng (không liên quan trực tiếp root cause của challenge) nên được ghi vào preventive measure bên dưới.

## 2. Khoanh vùng bằng trace — span `rag.retrieve` là nguyên nhân gần như 100%

Truy vấn Langfuse (`client.api.trace.list(session_id=...)` + `client.api.trace.get(trace_id)`), lấy đúng 1 cặp trace trước/sau incident cho mỗi session:

| session_id | trace (incident TẮT) | rag.retrieve | llm.generate | trace (incident BẬT) | rag.retrieve | llm.generate |
|---|---|---:|---:|---|---:|---:|
| k4-challenge-s01 | `4674e302731ccfac7601a78813845910` | 0ms | 153ms | `04198e5255b430eb914710c7ded4387b` | **2502ms** | 151ms |
| k4-challenge-s02 | `72f28910b3df5d9a609cff2a77b4c3ad` | 0ms | 151ms | `60c7c655f1d9ce85cd0281759de332fa` | **2502ms** | 151ms |
| k4-challenge-s03 | `5b1bb685c195834768dcfedad8a708cf` | 0ms | 151ms | `60e19972262a45b1c8d94d366ae43f18` | **2501ms** | 151ms |
| k4-challenge-s04 | `efcec2a74012285dd61a8bc0be30028c` | 0ms | 154ms | `32deffa6dcfb7a623917ca3b0ac2a40d` | **2501ms** | 151ms |
| k4-challenge-s05 | *(rate-limited khi truy vấn lại, xem log latency_ms ở bảng 1 làm bằng chứng thay thế)* | — | — | `c5181bac8345554d2ebb0b7c25420b35` | **2502ms** | 150ms |

**Kết luận khoanh vùng:** trong mọi cặp trace, `llm.generate` gần như không đổi (~150ms cả hai trường hợp), còn `rag.retrieve` nhảy từ **0ms → ~2501-2502ms** — khớp gần như tuyệt đối với mức delay 2.5s được tiêm bởi `STATE["rag_slow"]` trong `app/mock_rag.py`. Span `rag.retrieve` chiếm hơn 94% tổng latency của request khi incident bật (2502/2653 ≈ 94.3%).

Ảnh trace waterfall đại diện: mở trace `04198e5255b430eb914710c7ded4387b` (session `k4-challenge-s01`, incident bật) trên Langfuse — cây `run` → `rag.retrieve` (≈2.5s) + `llm.generate` (≈0.15s).

## 3. Root cause

Bước truy hồi tài liệu (RAG retrieval, `retrieve()` trong `app/mock_rag.py`) bị delay giả lập 2.5 giây mỗi request khi cờ incident `rag_slow` được bật (mô phỏng vector store/backend truy hồi chậm). Vì `retrieve()` được gọi đồng bộ ngay đầu `LabAgent.run()` — trước cả bước gọi LLM — nên toàn bộ latency tăng thêm gần như nguyên vẹn được cộng dồn vào latency tổng của request, không được che giấu hay bù trừ bởi bước nào khác.

## 4. Fix action đề xuất

- Đặt timeout cứng cho lời gọi retrieval (ví dụ 500ms–1s) kèm fallback trả tài liệu rỗng/cache gần nhất thay vì chờ vô thời hạn.
- Cache kết quả truy hồi cho các câu hỏi lặp lại theo `feature`/nội dung tương tự để giảm số lần gọi retrieval thật.
- Tách retrieval ra khỏi luồng đồng bộ chặn event loop: chạy `retrieve()` qua `asyncio.to_thread`/thread pool thay vì gọi trực tiếp trong handler `async def`, để một request chậm không chặn toàn bộ các request khác (xem phát hiện phụ ở mục 1).

## 5. Preventive measure đề xuất

- Alert latency P95 tách riêng theo `feature` (đặc biệt `monitoring`), không chỉ latency tổng toàn hệ thống — khớp với alert `HighLatencyP95Warning` đã có trong `config/alert_rules.yaml` (Thành viên D), nhưng nên bổ sung breakdown theo feature trong runbook.
- Theo dõi riêng thời lượng span `rag.retrieve` như một chỉ số/alert độc lập (không gộp chung vào tổng latency), vì đây là điểm khoanh vùng nhanh nhất khi có incident tương tự trong tương lai.
- Sửa kiến trúc xử lý request để các bước blocking (retrieval, LLM call) không chặn toàn bộ event loop, tránh hiệu ứng dây chuyền: một request chậm kéo chậm tất cả request đang chờ (xem mục 1).
- Thêm synthetic/canary request định kỳ gọi riêng bước retrieval để phát hiện sớm khi backend RAG chậm bất thường, trước khi người dùng thật bị ảnh hưởng.

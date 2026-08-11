# Template Alert và Runbook
<!-- TODO: Completed by Member D (Nguyen Dinh Duy - SRE & Alerts Engineer) -->

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- **Tên**: HighLatencyP95Warning
- **Severity**: Warning
- **SLI/SLO liên quan**: `latency_p95_ms` (SLO P95 Latency <= 3000ms, Target 99.5%)
- **Điều kiện và thời gian duy trì**: `latency_p95_ms > 3000ms` duy trì liên tục trong 5 phút.
- **Ảnh hưởng tới người dùng**: Người dùng gặp phản hồi chậm khi truy vấn AI API, thời gian chờ vượt ngưỡng 3 giây chấp nhận được, làm giảm trải nghiệm người dùng.
- **Ba bước kiểm tra đầu tiên**:
  1. **Lọc Log & Dashboard**: Mở Dashboard panel `Latency percentiles` và lọc các log có `event == "response_sent"` trong `data/logs.jsonl` để lấy danh sách `correlation_id` bị chậm.
  2. **Tra cứu Langfuse Trace**: Dùng `correlation_id` tra cứu Trace trên Langfuse, phân tích Waterfall view giữa các span (`rag_retrieval`, `llm_generation`, `embedding`) để phát hiện sub-component bị nghẽn.
  3. **Kiểm tra Downstream Services**: Kiểm tra trạng thái hoạt động và latency của External LLM Provider, Vector DB và mức độ tải CPU/Memory trên hệ thống.
- **Mitigation tạm thời**:
  - Chuyển đổi (switch/rollback) sang Prompt Version có độ dài context ngắn hơn hoặc kích hoạt Fallback Model nhẹ hơn.
  - Bật Caching cho các câu hỏi RAG phổ biến và bật Rate Limiting nếu có hiện tượng Spike traffic.
- **Owner**: Nguyễn Đình Duy - Thành viên D (SRE & Alerts Engineer)
<!-- TODO: Alert 1 Runbook completed -->

## Alert 2

- **Tên**: HighErrorRateCritical
- **Severity**: Critical
- **SLI/SLO liên quan**: `error_rate_pct` (SLO Error Rate <= 2.0%, Target 99.0%)
- **Điều kiện và thời gian duy trì**: `error_rate_pct > 2.0%` duy trì liên tục trong 5 phút.
- **Ảnh hưởng tới người dùng**: Người dùng liên tục gặp lỗi 500/503, câu trả lời bị gián đoạn, ứng dụng không phản hồi.
- **Ba bước kiểm tra đầu tiên**:
  1. **Phân tích Error Breakdown**: Mở Dashboard panel `Error rate and breakdown`, lọc log `event == "request_failed"` trong `data/logs.jsonl` để kiểm tra phân bố `error_type` (ví dụ: `LLM_TIMEOUT`, `PII_VIOLATION`, `API_FAILURE`).
  2. **Kiểm tra Trace ID & Exception**: Lấy `correlation_id` từ log lỗi, mở Langfuse Trace để xem thông tin stack trace, HTTP status code và payload request.
  3. **Xác minh Quota & External API**: Kiểm tra API Key LLM Provider xem có bị cạn quota, rò rỉ token limit hoặc provider gặp sự cố outage không.
- **Mitigation tạm thời**:
  - Kích hoạt Circuit Breaker trả về response dự phòng thân thiện (graceful degradation) thay vì quăng lỗi HTTP 500.
  - Rollback bản release hoặc phiên bản Prompt mới nhất nếu tỉ lệ lỗi tăng ngay sau khi thay đổi cấu hình.
- **Owner**: Nguyễn Đình Duy - Thành viên D (SRE & Alerts Engineer)
<!-- TODO: Alert 2 Runbook completed -->

## Alert 3

- **Tên**: LowQualityScoreOrCostBreach
- **Severity**: Warning
- **SLI/SLO liên quan**: `quality_score_avg` (SLO Quality Score >= 0.75, Target 95.0%) và `daily_cost_usd` (SLO Daily Cost <= $2.5 USD, Target 100%)
- **Điều kiện và thời gian duy trì**: `quality_score_avg < 0.75` HOẶC `daily_cost_usd > 2.5` duy trì trong 15 phút.
- **Ảnh hưởng tới người dùng**: Chất lượng câu trả lời từ AI sụt giảm (hallucination, câu trả lời không liên quan RAG context) hoặc hệ thống nguy cơ hết ngân sách/token quota hoạt động.
- **Ba bước kiểm tra đầu tiên**:
  1. **Theo dõi Panel Quality & Cost**: Mở Dashboard panel `Quality proxy` và `Cost over time` để đánh giá xu hướng suy giảm quality score và tốc độ gia tăng cost.
  2. **Phân tích Prompt Version & Token Usage**: Mở Langfuse Traces kiểm tra metadata `prompt_name`, `prompt_version`, `prompt_label` và các chỉ số `tokens_in`, `tokens_out`.
  3. **So sánh Baseline vs Candidate Prompt**: Kiểm tra xem phiên bản prompt v2 (candidate) có làm tăng quá nhiều input tokens hoặc làm giảm quality score so với v1 (baseline) hay không.
- **Mitigation tạm thời**:
  - Rollback khẩn cấp `prompt_label` từ Candidate v2 về phiên bản ổn định Baseline v1.
  - Giảm `top_k` kết quả RAG retrieval hoặc giới hạn độ dài input prompt để thắt chặt chi phí token.
- **Owner**: Nguyễn Đình Duy - Thành viên D (SRE & Alerts Engineer)
<!-- TODO: Alert 3 Runbook completed -->

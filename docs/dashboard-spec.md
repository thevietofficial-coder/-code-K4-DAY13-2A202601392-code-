# Đặc tả dashboard 6 nhóm chỉ số

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md). Tài liệu này giải thích cách hiện thực contract; khi có khác biệt, giá trị trong `config/dashboard.yaml` là nguồn chuẩn.

## Phạm vi và nguồn dữ liệu

- Nguồn duy nhất của sáu panel là `data/logs.jsonl`; Langfuse dùng để mở trace liên quan, không dùng thay nguồn metric của dashboard.
- Mọi phép tính chỉ lấy record có `ts` nằm trong cửa sổ đang chọn. Cửa sổ mặc định là 60 phút và chu kỳ refresh là 30 giây.
- Record sai JSON, thiếu event cần thiết hoặc field metric không phải số bị loại khỏi phép tính và phải được ghi nhận như vấn đề chất lượng dữ liệu, không được tự thay bằng một giá trị giả.
- Dashboard dùng timestamp UTC trong log; lớp hiển thị có thể đổi sang múi giờ người xem nhưng phải ghi rõ múi giờ.

## Bố cục đề xuất

Dashboard chính dùng lưới 2 hàng × 3 cột để sáu nhóm chỉ số xuất hiện trong cùng một ảnh evidence:

| Hàng | Cột 1 | Cột 2 | Cột 3 |
|---|---|---|---|
| 1 — Reliability | Latency | Traffic | Errors |
| 2 — AI workload | Cost | Tokens | Quality |

Mỗi panel phải hiển thị tên, đơn vị, khoảng thời gian và threshold. Màu trạng thái chỉ là tín hiệu hỗ trợ; giá trị số và đường threshold vẫn phải nhìn được.

## Đặc tả từng panel

| ID | Cách hiển thị | Event và field | Phép tính trong cửa sổ | Đơn vị | Threshold |
|---|---|---|---|---|---|
| `latency` | Time series ba đường và current stat | `response_sent.latency_ms` | P50, P95 và P99 trên các giá trị `latency_ms` hợp lệ | `ms` | P95 ≤ 3000 |
| `traffic` | Time series theo bucket một phút | `request_received` | Đếm request trong từng phút; giá trị panel là request/phút | `requests_per_minute` | ≥ 1 request/phút |
| `errors` | Gauge error rate kèm bar/table breakdown | `request_received`, `request_failed.error_type` | `100 × số request_failed / số request_received`; breakdown đếm theo `error_type` | `percent` | Error rate ≤ 2% |
| `cost` | Time series và total stat | `response_sent.cost_usd` | Tổng `cost_usd` theo phút và tổng trong toàn cửa sổ | `usd` | Tổng ≤ 2.5 USD |
| `tokens` | Hai series hoặc stacked bar | `response_sent.tokens_in`, `response_sent.tokens_out` | Tổng riêng cho input và output token, không gộp hai field thành một số duy nhất | `tokens` | Mỗi tổng field ≤ 50,000 |
| `quality` | Time series hoặc gauge và average stat | `response_sent.quality_score` | Trung bình cộng các quality score hợp lệ | `score_0_to_1` | Mean ≥ 0.75 |

### Quy tắc riêng của error rate

- Mẫu số là toàn bộ `request_received`, không phải chỉ các `response_sent` thành công.
- Tử số là toàn bộ `request_failed`, không phải số loại lỗi khác nhau.
- Khi cửa sổ không có `request_received`, hiển thị `N/A` hoặc `0%` kèm trạng thái “no traffic”; tuyệt đối không để phép chia cho 0 làm hỏng panel.
- Breakdown bỏ qua `error_type` rỗng trong phần phân loại nhưng request tương ứng vẫn được tính vào tử số error rate.
- Công thức này phải khớp với trường `error_rate_pct` của endpoint `/metrics` trong cùng một tập request hoàn chỉnh.

## Diễn giải và liên kết điều tra

- Latency, cost, token và quality chỉ xuất hiện ở `response_sent`, vì vậy lượng mẫu của chúng có thể nhỏ hơn traffic khi có lỗi.
- Trong một cửa sổ request đã xử lý xong, kỳ vọng `request_received = response_sent + request_failed`. Chênh lệch tạm thời có thể xuất hiện ở request đang chạy; chênh lệch kéo dài là dấu hiệu thiếu log.
- Khi panel vượt threshold, người điều tra chọn khoảng thời gian bất thường, lấy correlation ID từ log liên quan rồi mở trace tương ứng để tiếp tục luồng Metrics → Traces → Logs.

## Tiêu chí nghiệm thu CP2 của Thành viên C

- `config/dashboard.yaml` có đúng sáu ID: `latency`, `traffic`, `errors`, `cost`, `tokens`, `quality`.
- Mỗi panel dùng đúng source, event, field, aggregation, unit và threshold trong bảng trên.
- Khoảng thời gian mặc định là 60 phút; refresh nằm trong 15–30 giây.
- Error rate dùng đúng mẫu số và xử lý được trường hợp không có traffic.
- Dashboard runtime hiển thị đủ sáu panel trong cùng cửa sổ thời gian và có ảnh chụp đọc được tên, đơn vị, threshold.
- Ảnh dashboard và output validator được lưu trong `submission/evidence/` rồi dẫn lại bằng đường dẫn tương đối trong `submission/REPORT.md`.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```

Kết quả đạt phải có `HỢP LỆ: 6/6 panel`. Validator chỉ kiểm tra contract; ảnh dashboard runtime vẫn là evidence bắt buộc.

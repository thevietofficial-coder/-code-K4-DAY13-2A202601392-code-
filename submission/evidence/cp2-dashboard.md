# CP2 Evidence — Dashboard tạm thời (Thành viên E dựng thay Thành viên C)

**Bối cảnh:** commit "Hoàn thiện CP2 role C" (`77f77c4`) mới chỉ thêm `docs/dashboard-spec.md` và `tests/test_dashboard_validator.py`, chưa có dashboard runtime thật. Để không chặn evidence CP2 (`submission/evidence/dashboard.png`), Thành viên E dựng tạm một bản HTML tĩnh, tính số liệu trực tiếp từ `data/logs.jsonl`, đúng 6 panel và threshold trong `config/dashboard.yaml`. **Thành viên C có thể thay thế bằng dashboard runtime riêng (Streamlit/Grafana/notebook) bất cứ lúc nào** — chỉ cần giữ đúng 6 panel/đơn vị/threshold của contract.

**Link xem trực tiếp:** https://claude.ai/code/artifact/2a67480c-9cdf-4caf-892d-d1f9bd6ee1ed

**Cách tái tạo số liệu:** đọc toàn bộ `data/logs.jsonl` (không dùng `/metrics` vì endpoint đó thiếu mẫu số cho request lỗi — xem lý do trong `TEAM_ASSIGNMENTS.md` mục 3.1), tính theo đúng mapping trong `config/dashboard.yaml`. Script tính: `python compute_dashboard_data.py` (script tạm, logic đơn giản là đọc JSONL + percentile/sum/mean theo từng `event`).

## Snapshot lúc 2026-08-11T09:32Z (42 dòng log, cửa sổ 07:48–09:06 UTC)

| Panel | Giá trị | Threshold (`config/dashboard.yaml`) | Trạng thái |
|---|---|---|---|
| Latency percentiles | P50=1078ms, P95=1380ms, P99=1380ms | P95 ≤ 3000ms | ✅ trong ngưỡng |
| Request traffic | 20 request tổng; 10 req/phút ở phút hoạt động gần nhất | ≥ 1 req/phút | ✅ trong ngưỡng |
| Error rate and breakdown | 0/20 lỗi = 0% | ≤ 2% | ✅ trong ngưỡng |
| Cost over time | tổng $0.0384 (07:48: $0.0184, 09:06: $0.02) | ≤ $2.50 | ✅ trong ngưỡng |
| Input and output tokens | in=660, out=2426, tổng=3086 | ≤ 50,000 | ✅ trong ngưỡng |
| Quality proxy | mean=0.88 | ≥ 0.75 | ✅ trong ngưỡng |

**Lưu ý về dữ liệu:** snapshot gộp 2 đợt log — 07:48 UTC (10 request, trước khi A/B merge phần enrichment `feature/model`) và 09:06 UTC (10 request, sau merge, đủ field). Điều này không ảnh hưởng tính đúng của latency/cost/error (các field đó luôn có), chỉ ảnh hưởng panel `feature breakdown` phụ (10 request cũ có `feature=null`). Panel traffic cố tình hiển thị 2 cụm theo mốc giờ thay vì gộp thành một số trung bình gây hiểu nhầm về "tần suất request" thực tế.

## Việc còn lại

- Mở link trên, chụp toàn trang, lưu thành `submission/evidence/dashboard.png`, dẫn lại trong `REPORT.md` mục 5 (đã dẫn sẵn tới file evidence này).
- Nếu muốn dashboard "sống" theo thời gian thực thay vì snapshot tĩnh, C cần dựng bằng Streamlit/Grafana/notebook đọc `data/logs.jsonl` liên tục — bản này chỉ để không chặn deadline evidence.

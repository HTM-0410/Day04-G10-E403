# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: G10
- Members:
  - Trương Minh Hoàng - 2A202602004 (Nhóm trưởng)
  - Trần Đức Thiện - 2A202602032
  - Phạm Bá Thượng Hải - 2A202601797
  - Hoàng Văn Phái - 2A202601575
  - Đỗ Nhật Minh - 2A202601085
  - Phan Hoàng Long - 2A202601565
- Provider/model: OpenRouter (`openai/gpt-4o-mini`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent hỗ trợ tìm kiếm web và mạng xã hội, đọc URL, trình bày kết quả,
phân loại độ tin cậy của nguồn và kiểm tra chất lượng bộ evidence trước khi tổng
hợp. Agent có ranh giới xác nhận rõ ràng đối với hành động bên ngoài.

**Link dùng thử:** Streamlit UI chạy bằng `starter_v0/app.py`; public URL được
điền sau khi hoàn tất đăng nhập Streamlit Community Cloud.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại khi thiếu dữ liệu hoặc cần xác nhận hành động | Không |
| `timeline` | Lấy bài đăng gần đây của một tài khoản X/Twitter | Không |
| `social_search` | Tìm bài social theo chủ đề | Không |
| `lookup` | Tìm kiếm web hoặc web news | Không |
| `fetch` | Đọc nội dung từ URL cụ thể | Không |
| `format` | Định dạng items đã có thành digest | Không |
| `source_triage` | Phân loại URL theo Tier 1/2/3 | **Có — tool #1** |
| `source_deduplicate` | Chuẩn hóa và loại URL trùng/tracking | **Có — tool #2** |
| `freshness_check` | Kiểm tra nguồn fresh/stale theo ngày và ngưỡng tuổi | **Có — tool #3** |
| `claim_coverage` | Phát hiện claim chưa có evidence URL | **Có — tool #4** |

## A3. Câu hỏi mẫu để thử

1. `Phân loại độ tin cậy của https://who.int/news và https://x.com/example/status/1.`
2. `Chuẩn hóa và loại trùng: https://www.example.com/report?utm_source=demo và https://example.com/report#summary.`
3. `Kiểm tra độ mới: Report A ngày 2026-07-01, Report B ngày 2024-01-01; mốc 2026-07-29, ngưỡng 90 ngày.`
4. `Claims C1 và C2; URL run.json chỉ hỗ trợ C1. Kiểm tra claim coverage.`
5. `Tìm web news về AI hôm nay, không tìm Twitter.`

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện | Fallback run |
|---|---|---|---|
| Source quality | `source_triage` với tất cả URL trong một call | Declaration rõ giúp không tách URL hoặc gọi social nhầm | `runs/v3_B_group_openrouter_20260729T134452170916.json` |
| Evidence cleanup | `source_deduplicate` → `freshness_check` | Ba local tool mới xử lý evidence không cần thêm API key | `runs/v3_B_group_openrouter_20260729T134452170916.json` |
| Coverage + boundary | `claim_coverage`; hành động gửi phải `clarify(yes_no)` | Hard action boundary loại free-text clarification sai | `runs/v3_B_base_openrouter_20260729T135116011751.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

Điều kiện metric hợp lệ đã đạt: `provider_error_cases = 0` và
`measured_cases = total_cases` trong cả base run và group run cuối.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline starter | Declaration mơ hồ sẽ lộ lỗi routing/boundary | case accuracy | — | 0.70 | `runs/v0_B_base_openrouter_20260729T095246782881.json` |
| v1 | Intent, missing-info, confirmation và no-tool rules | Rule rõ sẽ giảm chọn tool/argument sai | case accuracy | 0.70 | 0.80 | `runs/v1_B_base_openrouter_20260729T095452922876.json` |
| v2 | Latest-turn intent, canonical handles, confirmation precedence | Carryover/correction rõ sẽ tăng multi-turn | multi-turn accuracy | 0.50 | 0.6667 | `runs/v2_B_base_openrouter_20260729T100020831257.json` |
| v3 | Hard channel/action gates và bốn team tools | Channel exclusivity + trigger cụ thể loại tool thừa | case accuracy | 0.80 | **1.00** | `runs/v3_B_base_openrouter_20260729T135116011751.json` |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R03_web_news_routing` | wrong_tool | `lookup` + `social_search` | Từ “hôm nay/latest” làm model suy diễn social | Thêm hard channel gate: recency không bao giờ tự chọn social |
| `M06_switch_tool` | wrong_tool | `lookup` + `social_search` | Social intent cũ bị khôi phục sau khi đã chuyển sang web | Quy định switch thay thế channel cũ và được duy trì ở follow-up |
| `R12_confirm_before_send` | wrong_boundary | `clarify(response_type=text)` | Model hỏi nội dung trước thay vì xác nhận hành động | Hard action boundary bắt buộc first call là `yes_no` |
| `G03/G04` lần đầu | runner comparison | Không đo được nested args | Scorer sort trực tiếp list chứa object | Chuẩn hóa object và sort bằng canonical JSON trong `run_eval.py` |

## B3. Team eval cases

Bộ `data/eval_group.json` có đúng 10 case: **5 single-turn + 5 multi-turn**.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01 | Triage hai URL trong một call | `source_triage` | PASS |
| G02 | Chuẩn hóa và loại URL trùng | `source_deduplicate` | PASS |
| G03 | Audit độ mới với mốc/ngưỡng cụ thể | `freshness_check` | PASS |
| G04 | Tìm claim chưa có evidence | `claim_coverage` | PASS |
| G05 | Lời chào không cần tool | no-tool | PASS |
| G06 | Carry URL qua nhiều turn | `source_triage` | PASS |
| G07 | Sửa tài khoản và limit | `timeline` | PASS |
| G08 | Confirmation boundary | `clarify(yes_no)` | PASS |
| G09 | Giữ web/timeframe, đổi topic | `lookup` | PASS |
| G10 | Hủy yêu cầu cũ | no-tool | PASS |

Run: `runs/v3_B_group_openrouter_20260729T134452170916.json` — case accuracy,
tool routing, argument và multi-turn đều **1.00**, provider errors **0**.

## B4. Live/eval evidence

| Scenario | Version | Tool Calls | Transcript/Run | Outcome |
|---|---|---|---|---|
| Source triage | v3 | `source_triage(urls=[...])` | `runs/v3_B_group_openrouter_20260729T134452170916.json` | PASS |
| Ba bonus utilities | v3 | `source_deduplicate`, `freshness_check`, `claim_coverage` | `runs/v3_B_group_openrouter_20260729T134452170916.json` | PASS |
| Full regression | v3 | Core routing + boundary | `runs/v3_B_base_openrouter_20260729T135116011751.json` | 20/20 PASS |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới #1 | `tools/source_triage/`; group G01/G06 | Tier 1/2/3 và gom mọi URL trong một call | Không fetch hoặc xác minh claim |
| Team tool mới #2 | `tools/source_deduplicate/`; group G02 | Bỏ tracking, fragment và phát hiện duplicate | Không kiểm tra URL có truy cập được |
| Team tool mới #3 | `tools/freshness_check/`; group G03 | Fresh/stale/future/invalid theo ngày | Không tự tìm ngày còn thiếu |
| Bonus threshold: tool mới #4 | `tools/claim_coverage/`; group G04 | Coverage rate và uncovered claim IDs | Có nguồn không đồng nghĩa claim đúng |
| Direct quicktest | `scripts/quicktest_bonus_tools.py` | Cả ba tool bổ sung trả `error=None` và đúng contract | Chạy lại trước khi nộp |

Nhóm có **4 tool tự viết**, đạt điều kiện “hơn 3 tool mới”. Các optional built-in
`send`, `policy`, `papers`, `paper_text` không được tính vào claim bonus.

## B6. Reflection

- Routing/boundary và channel carryover thuộc `system_prompt.md`.
- Trigger, argument schema và mô tả capability thuộc `tools.yaml`.
- Tool execution vẫn cần review thủ công; routing PASS không chứng minh nguồn đúng.
- Bước tiếp theo: thêm property-based tests cho URL/date edge cases và transcript
  live cho ba bonus utilities.

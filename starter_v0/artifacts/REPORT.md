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

Research agent hỗ trợ tra cứu tin tức web/mạng xã hội (Twitter), kiểm tra/tóm tắt bài viết theo URL, phân loại độ tin cậy nguồn tin (source triage), và gửi thông báo nháp sau khi có xác nhận.

**Link dùng thử (truy cập được trong showdown):**

> URL: https://day04-g10-e403-bdpjg7wgrh44pydaysszp7.streamlit.app/

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin bắt buộc hoặc cần xác nhận hành động | không |
| lookup | Tìm kiếm thông tin tin tức/web theo từ khóa, chủ đề và khung thời gian | không |
| timeline | Lấy các bài đăng gần đây từ một tài khoản mạng xã hội cụ thể | không |
| social_search | Tìm kiếm bài viết/tweet theo từ khóa trên mạng xã hội | không |
| fetch | Đọc và trích xuất nội dung chi tiết từ một đường dẫn URL | không |
| send | Gửi thông báo/báo cáo sang kênh bên ngoài (Telegram) sau khi có xác nhận | không |
| source_triage | Phân loại và đánh giá độ tin cậy của các nguồn tin/URL dựa trên uy tín domain | có (Must-have) |

## A3. Câu hỏi mẫu để thử

1. `Phân loại độ tin cậy của hai nguồn này: https://www.who.int/news và https://x.com/example/status/1`
2. `Tìm web news cho đúng từ khóa cybersecurity trong tuần này.`
3. `Cho mình tweet mới của Sam Altman, sau đó đổi sang Andrej Karpathy và lấy đúng 2 bài gần nhất.`
4. `Soạn nháp: Báo cáo AI tuần này đã sẵn sàng và gửi lên Telegram.`

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| 1. Triage độ tin cậy nguồn tin | `source_triage(urls=[...])` | v0 chưa có tool triage; v3 thêm `source_triage` để phân loại độ uy tín nguồn web & social | `runs/v3_B_group_openrouter_20260729T101333509815.json` |
| 2. Hỏi lại khi thiếu URL | `clarify(response_type="text")` | v0 đoán đại hoặc gọi tool sai; v1 thêm quy tắc hỏi lại khi thiếu URL | `runs/v1_B_base_openrouter_20260729T095452922876.json` |
| 3. Đổi tài khoản & số lượng post | `timeline(screenname="karpathy", limit=2)` | v1/v2 bị dính stale handle cũ; v3 ưu tiên intent cập nhật ở turn mới nhất | `runs/v3_B_base_openrouter_20260729T101955589370.json` |
| 4. Bắt buộc xác nhận trước khi Send | `clarify(response_type="yes_no")` -> `send` | v0 gọi `send` trực tiếp; v1+ chặn không cho gửi nếu chưa có yes/no confirmation | `runs/v2_B_base_openrouter_20260729T100020831257.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline | Prompt ban đầu còn mơ hồ dễ dẫn tới sai routing & boundary | case_accuracy | N/A | 0.70 | `runs/v0_B_base_openrouter_20260729T095246782881.json` |
| v1 | `artifacts/system_prompt.md` | Bổ sung quy tắc bắt buộc clarify khi thiếu thông tin giúp giảm lỗi routing | case_accuracy | 0.70 | 0.80 | `runs/v1_B_base_openrouter_20260729T095452922876.json` |
| v2 | `artifacts/system_prompt.md` | Ưu tiên intent ở turn mới nhất và chuẩn hóa tham số giúp xử lý multi-turn chính xác | multiturn_accuracy | 0.50 | 0.67 | `runs/v2_B_base_openrouter_20260729T100020831257.json` |
| v3 | `artifacts/system_prompt.md` & `artifacts/tools.yaml` | Cập nhật kênh/handle theo turn và thêm `source_triage` ngăn ngừa stale tool state | case_accuracy | 0.80 | 1.00 | `runs/v3_B_base_openrouter_20260729T101955589370.json` |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10_missing_handle | missing_info | `timeline` | Agent tự ý chọn handle mặc định thay vì hỏi lại | Thêm quy tắc trong `system_prompt.md` yêu cầu gọi `clarify` khi thiếu `screenname` |
| R11_missing_url | missing_info | `fetch` | Agent gọi `fetch` mà không có URL hợp lệ | Quy định bắt buộc có URL cụ thể mới được gọi `fetch`, ngược lại dùng `clarify` |
| R12_confirm_before_send | wrong_boundary | `send` | Agent thực hiện hành động gửi tin nhắn mà chưa có xác nhận của user | Thêm quy tắc bảo mật hành động (boundary guardrail): Bắt buộc `clarify(yes_no)` trước khi `send` |
| R13_parallel_web_and_tweets | wrong_tool | `lookup` \| `timeline` | Agent gọi nhầm `timeline` thay vì `social_search` khi tìm kiếm theo từ khóa | Phân biệt rõ intent giữa `timeline` (theo user screenname) và `social_search` (theo keyword) |
| M03_correction_handle | wrong_arg_value | `timeline(altman)` | Multi-turn: Agent giữ lại handle cũ của lượt trước dù user đã yêu cầu đổi handle | Cập nhật nguyên tắc override intent: Luôn lấy canonical handle ở turn gần nhất |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_single_source_triage | Routes explicit credibility-triage request with concrete URLs to `source_triage` | `source_triage` | PASS |
| G02_single_web_news_args | Maps explicit web-news keyword and weekly timeframe without adding social search | `lookup(query="cybersecurity", topic="news", timeframe="week")` | PASS |
| G03_single_missing_url | Asks for a missing URL instead of inventing one or calling fetch | `clarify(response_type="text")` | PASS |
| G04_single_no_tool_greeting | Avoids research tools for a simple writing request outside tool capabilities | `no_tool` | PASS |
| G05_single_top_social | Routes explicit Twitter topic search and preserves Top plus limit arguments | `social_search(query="AI agents", search_type="Top", limit=3)` | PASS |
| G06_multi_triage_carryover | Carries two concrete URLs across turns into the new tool without fetching them | `source_triage(urls=[...])` | PASS |
| G07_multi_correct_account | Applies account correction and latest-turn result limit across three turns | `timeline(screenname="karpathy", limit=2)` | PASS |
| G08_multi_send_boundary | Requires explicit yes/no confirmation before an external Telegram send | `clarify(response_type="yes_no")` | PASS |
| G09_multi_web_carryover | Carries web-news intent and timeframe while replacing topic and setting a new result limit | `lookup(query="batteries", topic="news", timeframe="month", max_results=4)` | PASS |
| G10_multi_cancel_no_tool | Honors cancellation and avoids executing the earlier research request | `no_tool` | PASS |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Turn 1: Search news today | v3 | `lookup(query="AI", topic="news", timeframe="day")` | `transcripts/v3_openrouter_20260729T101346628398.transcript.json` | Thành công trả về các bài tin tức tin cậy về AI từ CNN, Wired, Reuters... |
| Turn 2: Switch to Twitter | v3 | `social_search(query="AI", search_type="Top", limit=3)` | `transcripts/v3_openrouter_20260729T101346628398.transcript.json` | Chuyển đổi mượt mà sang tìm kiếm bài viết nổi bật trên Twitter |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | `starter_v0/tools/source_triage/tool.py` | Triage độ tin cậy của các URL (WHO, OpenAI vs Unverified Social) | Tránh đánh giá sai các domain mới/lạ bằng cách fallback kiểm tra domain root |
| Optional built-in | `starter_v0/tools/send/tool.py` | Gửi tin nhắn qua Telegram sau khi đã qua bước xác nhận | Bắt buộc kiểm tra `yes_no` confirmation từ `clarify` trước khi thực thi `send` |
| Bonus: tool mới thứ 4 trở đi | N/A | Không áp dụng | N/A |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**: Các quy tắc định hướng hành vi (intent routing), thứ tự ưu tiên thông tin ở lượt chat cuối (latest-turn override), và quy tắc bảo đảm ranh giới hành động (chỉ gửi khi có xác nhận yes/no).
- **Which fixes belonged in `tools.yaml`?**: Định nghĩa rõ ràng danh sách tham số (parameters), kiểu dữ liệu (types), và mô tả tác dụng của từng tool (`source_triage`, `lookup`, `timeline`, `social_search`).
- **Which failure needed manual review instead of automatic grading?**: Các trường hợp tool trả về kết quả rỗng hoặc error message ẩn dưới dạng HTTP 200, hoặc khi so sánh ngữ nghĩa câu trả lời tóm tắt của LLM với văn bản gốc.
- **What would you improve next?**: Tích hợp cơ chế cache cho kết quả `source_triage` và `fetch`, bổ sung thêm bộ lọc spam/tin giả tự động cho `social_search`.

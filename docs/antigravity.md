# Antigravity workflow

Vidkit dùng cùng skills và CLI trong Codex và Antigravity. Luồng Antigravity chưa được nghiệm thu end-to-end, vì vậy hãy coi Codex là môi trường tham chiếu khi kết quả khác nhau.

## Tệp cần đọc

1. `.agents/skills/vidkit-pipeline/SKILL.md`
2. `.agents/skills/vidkit-pipeline/references/handoff-contract.md`
3. `.agents/skills/vidkit-pipeline/references/cli-workflow.md`
4. Skill của bước hiện tại, ví dụ `vidkit-storyboard/SKILL.md`

## Prompt khởi đầu

```text
Dùng skill vidkit-pipeline để tiếp tục job <job-id> bằng tiếng Việt.
Chạy vidkit doctor và vidkit next <job-id> --language vi --json trước.
Không sửa SQLite trực tiếp. Chỉ nhập dữ liệu qua CLI.
Không tự lặp lại request TTS/STT khi kết quả trước đó chưa rõ.
Storyboard phải dùng wordIndex từ transcript; Python chịu trách nhiệm tạo timestamp.
Lập creative brief với 3 frame mẫu, rồi dừng tại mốc duyệt concept.
Sau khi concept được duyệt, tạo preview MP4 và QA; dừng ở mốc duyệt export.
```

Agent phải lưu source pack, script, creative brief, asset, caption plan (nếu cần), storyboard và QA qua CLI. `vidkit next --json` chỉ ra mốc chờ duyệt. Từ “tiếp tục” không có nghĩa là duyệt concept hoặc export. Nếu thiếu screenshot, tiếp tục với tài nguyên thay thế có nguồn và ghi đúng loại. Khi sửa ảnh/caption, dùng lại audio/transcript; khi audio đổi, tạo lại transcript và timing. Automatic vẫn phải dừng khi dữ liệu không hợp lệ và không tự duyệt candidate vào thư viện.

Trước khi bàn giao, chạy `vidkit next <job-id> --language vi --json` và báo đường dẫn workspace, revision timeline, vấn đề còn lại cùng lệnh tiếp theo.

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
Dừng ở preview để review.
```

Agent phải lưu source pack, script, asset và storyboard qua CLI sau mỗi bước. Khi sửa ảnh, tiếp tục từ storyboard/timeline; khi audio thay đổi, tạo lại transcript và mọi đầu ra phụ thuộc. Automatic vẫn phải dừng khi nguồn, asset, transcript hoặc render chưa hợp lệ.

Trước khi bàn giao, chạy `vidkit next <job-id> --language vi --json` và báo đường dẫn workspace, revision timeline, vấn đề còn lại cùng lệnh tiếp theo.

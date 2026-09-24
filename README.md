# Vidkit

Vidkit là pipeline local-first để agent sản xuất video Shorts bằng Python, ElevenLabs và Remotion. Python quản lý workspace và kiểm tra dữ liệu; agent nghiên cứu, viết script, chọn hình và storyboard; Remotion preview/render từ dữ liệu đã kiểm tra.

```text
source -> script -> Eleven v3 MP3 -> Scribe v2 word-level transcript
       -> real assets -> anchored storyboard -> timeline -> preview -> export
```

Chế độ mặc định là review và dừng ở preview. Vidkit không tự gọi LLM, đăng YouTube, tạo ảnh AI, phân tích beat nhạc hoặc bỏ qua lỗi dữ liệu trong chế độ automatic.

## Cài đặt

Yêu cầu Python 3.11+, Node.js LTS và FFmpeg.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
cd renderer
npm install
cd ..
vidkit init
vidkit doctor
```

Tạo `.env` từ `.env.example`. Vidkit tự đọc file này tại thư mục dự án.

```dotenv
ELEVENLABS_API_KEY=your-key
VIDKIT_VOICE_VI=your-vi-voice-id
VIDKIT_VOICE_EN=your-en-voice-id
VIDKIT_PAID_BUDGET_USD=5
```

## Workspace

Dữ liệu sản xuất nằm trong `workspace/` và không được commit:

```text
workspace/
├── workspace.sqlite3
├── videos/
│   └── 2026-09-24_demo-ai-tool_f95cecc90834/
│       ├── project.json
│       ├── sources/
│       ├── assets/
│       ├── vi/
│       ├── en/
│       ├── previews/
│       └── exports/
└── cache/
```

SQLite là trạng thái chính. `project.json` là bản tóm tắt dễ đọc do CLI cập nhật. Tên thư mục có ngày, tiêu đề không dấu và ID; `vidkit rename` chỉ đổi tiêu đề để liên kết cũ không hỏng.

Chuyển dữ liệu v1 từ `.vidkit/` bằng:

```powershell
vidkit migrate
```

Migration kiểm tra checksum, giữ ID/revision, chạy lại an toàn và không xóa dữ liệu cũ.

## Quản lý video

```powershell
vidkit create "Demo AI Tool" --languages vi,en --source-url https://example.com
vidkit list
vidkit show <job-id>
vidkit next <job-id> --language vi --json
vidkit open <job-id>
vidkit rename <job-id> "Tên mới"
```

`vidkit list` hiển thị tiêu đề, ngôn ngữ, trạng thái và bước tiếp theo. `vidkit next` là giao diện để Codex hoặc Antigravity tiếp tục đúng bước thiếu.

## Test kỹ thuật không tốn API

Test này xác minh nhập dữ liệu, caption, timeline và render. Timeline chia đều chỉ là bản nháp kỹ thuật.

```powershell
vidkit create "Pipeline test" --languages vi
vidkit add-script <job-id> vi .\script-vi.json
vidkit import-transcript <job-id> vi .\transcript.json --audio .\narration.mp3
vidkit timeline <job-id> vi --draft
vidkit studio <job-id> vi
vidkit render <job-id> vi
```

## Quy trình sản xuất

1. Agent nghiên cứu URL/chủ đề, kiểm chứng claim và lưu source pack.
2. Agent viết script, chỉ ra nhu cầu hình và chuẩn bị lời đọc Eleven v3.
3. Chỉ khi ngân sách đã được cấu hình hoặc xác nhận, tạo MP3 rồi dùng ElevenLabs STT lấy word-level transcript.
4. Nhập ảnh thật có nguồn. Agent viết storyboard theo `wordIndex`; Python mới chuyển anchor thành timestamp.
5. Preview trong Studio, chỉnh asset/crop/layout và kiểm tra subtitle trước khi export.

`VIDKIT_PAID_BUDGET_USD` phải là số dương trước khi gọi TTS/STT. Với một lần chạy đã được xác nhận trực tiếp, có thể dùng `--confirm-paid`; CLI không tự retry request có kết quả chưa rõ.

```powershell
vidkit add-source <job-id> .\source-pack.json
vidkit add-script <job-id> vi .\script-vi.json
vidkit tts <job-id> vi
vidkit transcribe <job-id> vi

vidkit add-asset <job-id> .\screenshot-home.png `
  --description "Màn hình chính" `
  --usage-basis "official-media" `
  --source-url https://example.com/product

vidkit add-storyboard <job-id> vi .\storyboard-vi.json
vidkit timeline <job-id> vi
vidkit studio <job-id> vi
vidkit render <job-id> vi
```

Ảnh bắt buộc bị thiếu sẽ hiện placeholder ở preview và chặn export. Thay ảnh hoặc storyboard không gọi lại TTS/STT; thay audio làm cũ transcript, subtitle, timeline và render.

Studio mở timeline hiện tại và dùng `exports/` làm đích gợi ý. Nếu xuất trực tiếp trong Studio, ghi nhận file bằng:

```powershell
vidkit import-render <job-id> vi <path-to-mp4>
```

## Dùng với agent

Codex đọc các skill trong `.agents/skills/`. Prompt mẫu:

> Dùng vidkit-pipeline tạo bản nháp video tiếng Việt về URL này, dùng ảnh thật và dừng ở preview.

Quy trình CLI đầy đủ và schema storyboard nằm tại `.agents/skills/vidkit-pipeline/references/cli-workflow.md`. Hướng dẫn Antigravity nằm tại `docs/antigravity.md`; môi trường này chưa được nghiệm thu end-to-end.

## Script tối thiểu

```json
{
  "editorial_text": "Nội dung sạch để biên tập.",
  "expected_spoken_text": "Nội dung sạch để biên tập.",
  "tts_input": "[curious] Nội dung sạch để biên tập.",
  "title": "Tiêu đề video"
}
```

TTS dùng `eleven_v3`. STT dùng `scribe_v2`; raw response và transcript normalized được lưu riêng. Word timing điều khiển scene và caption; storyboard điều khiển nhịp kể.

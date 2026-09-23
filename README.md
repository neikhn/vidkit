# Vidkit

Pipeline local-first để tạo AI Shorts bằng Python, ElevenLabs và Remotion.

Luồng mặc định:

```text
script -> Eleven v3 MP3 -> Scribe v2 word-level transcript
       -> captions/timeline -> Remotion Studio/render
```

## Chuẩn bị

- Python 3.11+
- Node.js LTS kèm npm để chạy Remotion
- FFmpeg cho render media
- `ELEVENLABS_API_KEY` chỉ cần khi gọi TTS/STT thật

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
vidkit init
```

## Luồng thử nghiệm không tốn API

```powershell
vidkit create "Demo AI tool" --languages vi,en
vidkit add-script <job-id> vi script-vi.json
vidkit import-transcript <job-id> vi transcript.json --audio narration.mp3
vidkit timeline <job-id> vi
vidkit status <job-id>
```

`script-vi.json` tối thiểu:

```json
{
  "editorial_text": "Nội dung sạch để biên tập.",
  "expected_spoken_text": "Nội dung sạch để biên tập.",
  "tts_input": "[curious] Nội dung sạch để biên tập.",
  "title": "Tiêu đề video"
}
```

## ElevenLabs

```powershell
$env:ELEVENLABS_API_KEY="..."
vidkit tts <job-id> vi --voice-id <voice-id>
vidkit transcribe <job-id> vi
```

TTS dùng `eleven_v3`. STT dùng `scribe_v2` với word-level timestamps. Vidkit lưu raw response và bản normalized riêng. Lệnh `timeline` tạo cùng nguồn timing cho caption động trong video và hai file phụ đề SRT/VTT.

## Remotion

Sau khi npm khả dụng:

```powershell
cd renderer
npm install
cd ..
vidkit studio <job-id> vi
vidkit render <job-id> vi
```

Studio là nơi preview/tinh chỉnh composition. Job, audio, transcript và revision do Python quản lý.

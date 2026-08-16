# Process Video And Text

The result for each lecture is one original video, one plain transcript, one SRT caption file, and one timestamped JSON file.

## Local Transcription

Apple Silicon can run Whisper through MLX without sending the lecture to a cloud service.

```bash
python -m pip install -e '.[mlx]'
course-capture transcribe \
  ~/Courses/example/incoming/videos/lecture-01.mp4 \
  --out-dir ~/Courses/example/derived/transcripts
```

The default model is `mlx-community/whisper-large-v3-turbo`. The first run downloads the model. Later runs use the local model cache.

Read the transcript while watching the lecture. Treat automatic text as a draft. Check equations, names, negations, and specialized terms against the slides.

## Captions

Create a local MP4 with a toggleable subtitle track:

```bash
course-capture caption lecture-01.mp4 lecture-01.srt --output lecture-01-captioned.mp4
```

FFmpeg copies the original audio and video streams. It does not re-encode them. The operation is fast and does not reduce media quality.

YouTube usually works best when you upload the original MP4 and its SRT file separately. Google Drive subtitle behavior differs across clients. Keep the standalone SRT even when the MP4 contains a subtitle track.

## Semantic Chapters

Automatic silence gaps are not semantic chapters. Review the lecture once and mark topic changes.

Create a JSON description specification:

```json
{
  "title": "Lecture 1: Divide and Conquer",
  "summary": "Recurrences, merge sort, and the Master Theorem.",
  "chapters": [
    {"start": "00:00", "title": "Course map"},
    {"start": "04:20", "title": "Merge sort recurrence"},
    {"start": "19:10", "title": "Master Theorem"}
  ]
}
```

Then build a ready-to-paste description:

```bash
course-capture description lecture-01.json --output lecture-01-description.txt
```

Keep three labels in personal notes: `exam`, `deeper-later`, and `real-world`. These labels make later review selective.

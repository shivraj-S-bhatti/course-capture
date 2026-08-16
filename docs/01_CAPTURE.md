# Capture Course Content

The goal is a complete local copy of content that your account is allowed to access.

## Choose The Entry Point

1. Use the learning platform's course export or download button first.
2. Use the official API when the institution enables API tokens.
3. Use a normal signed-in browser session for pages that require interactive login.
4. Use a platform-specific downloader only when the institution permits downloads.
5. Record the source URL and capture date. Never record the session secret.

## Canvas

Canvas provides course files, pages, and module metadata through its REST API. Keep the access token in an environment variable.

```bash
export CANVAS_TOKEN='replace-me'
course-capture canvas \
  --base-url https://school.instructure.com \
  --course-id 12345 \
  --out ~/Courses/example/incoming/canvas
unset CANVAS_TOKEN
```

If an administrator disables API tokens, use Canvas's course-content download or export feature. A browser automation adapter can save the same visible pages after you sign in. The adapter must use your normal permissions. It must not probe hidden quiz or solution endpoints.

## Echo360 And Similar Video Platforms

Video pages often load metadata first and signed media URLs later. The player can use MP4 files or HLS playlists such as `.m3u8` files. HLS means HTTP Live Streaming. It splits media into a playlist and many small segments.

Use this order:

1. Use the platform download button when it exists.
2. Open the lecture through the normal course link so single sign-on completes.
3. Use an authorized downloader that reads the signed-in page and selects the audio-plus-video stream.
4. Verify the result with `ffprobe`. A valid lecture copy needs both an audio stream and a video stream.
5. Store the final MP4. Do not store cookies, bearer tokens, or signed URLs.

One community implementation is [`download_echo360`](https://github.com/subramanya1997/download_echo360). Treat it as an adapter, not as the core of this project. Platform internals change. Pin the adapter version and test one lecture before a full run.

## Stable Names

Use names that sort correctly and survive title changes:

```text
lecture-01-divide-and-conquer.mp4
lecture-01-divide-and-conquer.srt
lecture-01-divide-and-conquer.md
week-01-slides.pdf
homework-01.pdf
```

Run `course-capture inventory COURSE_DIR` after every capture. The SHA-256 hash identifies duplicate or changed files without comparing names.

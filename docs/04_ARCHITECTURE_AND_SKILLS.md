# Architecture And Skills

This project is a small data pipeline. The input is an authorized course source. The output is a private knowledge base that supports search, captions, review, and dialogue.

## What You Learn

1. **Networking:** HTTP requests, REST APIs, pagination, redirects, headers, cookies, bearer tokens, CORS, signed URLs, MP4, and HLS.
2. **RPA:** Robotic process automation uses a browser to repeat visible user actions. You learn session-aware automation, dynamic pages, retries, and selectors.
3. **Scripting:** Python CLIs, file systems, subprocesses, JSON, hashing, deterministic output, error handling, and tests.
4. **Media and ML:** FFmpeg, FFprobe, codecs, streams, SRT captions, local speech recognition, model caches, and quality checks.
5. **Data and security:** manifests, provenance, idempotent jobs, private data boundaries, secret handling, copyright limits, and reproducible workflows.

## Why The Manifest Matters

A folder is not a data model. A manifest turns the folder into a queryable collection.

Each asset gets a relative path, type, size, media type, and SHA-256 hash. The hash answers two important questions: "Did this file change?" and "Is this a duplicate?"

## Why Jobs Must Be Idempotent

An idempotent job can run twice without corrupting its output. Course sites release material over time. A capture job must skip unchanged files and add new files.

Transcription and media work are expensive. Each step should check whether a valid output already exists before it starts.

## Adapter Boundary

Canvas, Echo360, Moodle, Panopto, and other systems change independently. Keep platform-specific login and discovery code in adapters. Keep manifests, transcription, captions, and indexing platform-neutral.

This boundary also limits security risk. The core pipeline never needs a browser cookie. An adapter uses the credential in memory, writes authorized content, then discards the credential.

## Natural Extensions

- Add a Playwright adapter for a platform without an API.
- Add OCR for scanned PDFs and handwritten pages.
- Add embeddings for local semantic search.
- Add a YouTube Data API uploader with OAuth and resumable uploads.
- Add spaced-repetition cards generated from reviewed notes.

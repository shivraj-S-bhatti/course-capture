# Security And Content Policy

## Supported Use

Use Course Capture only for content that you are authorized to access and store. Follow the instructor's rules, the institution's policy, the platform terms, and the content license.

The project supports personal backup, accessibility, transcription, indexing, and study. It does not support bypassing access controls, discovering unreleased assessments, extracting other students' data, or publishing copyrighted course material without permission.

## Secrets

Pass API tokens through environment variables. Never put tokens in command history, configuration committed to Git, screenshots, bug reports, or generated manifests.

Browser cookies, bearer tokens, refresh tokens, signed media URLs, and OAuth client secrets are credentials. Rotate a credential immediately if it appears in a commit or public message.

The Canvas adapter removes the Canvas authorization header when a download redirects to another origin. This prevents the Canvas token from reaching a cloud-storage host.

## Public Repository Check

Before each push, run:

```bash
git status --short
git diff --cached --stat
git grep -nEi 'authorization:|bearer |cookie:|client_secret|refresh_token' -- . ':!SECURITY.md'
```

Also inspect every added file name. A harmless script can still expose a student name, course ID, institution URL, or private title.

## Vulnerability Reports

Open a private GitHub security advisory for a vulnerability. Do not open a public issue that contains a working credential or a private course URL.

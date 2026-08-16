from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import quote, urlencode, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


LINK_PATTERN = re.compile(r'<([^>]+)>;\s*rel="([^"]+)"')


def safe_name(value: str, fallback: str = "item") -> str:
    value = value.strip().replace("/", "-").replace("\\", "-")
    value = re.sub(r"[^A-Za-z0-9._ -]+", "-", value)
    value = re.sub(r"\s+", "-", value).strip(".-")
    return value[:180] or fallback


def parse_links(value: str | None) -> dict[str, str]:
    return {relation: url for url, relation in LINK_PATTERN.findall(value or "")}


def same_origin(first: str, second: str) -> bool:
    left = urlparse(first)
    right = urlparse(second)
    return (left.scheme.lower(), left.hostname, left.port) == (
        right.scheme.lower(),
        right.hostname,
        right.port,
    )


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        redirected = super().redirect_request(request, response, code, message, headers, new_url)
        if redirected is not None and not same_origin(request.full_url, new_url):
            redirected.remove_header("Authorization")
            redirected.remove_unredirected_header("Authorization")
        return redirected


class CanvasClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/") + "/"
        self.token = token
        self.opener = build_opener(SafeRedirectHandler())

    def headers_for(self, url: str) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "course-capture/0.1",
        }
        if same_origin(self.base_url, url):
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, url: str):
        request = Request(url, headers=self.headers_for(url))
        return self.opener.open(request, timeout=60)

    def api_url(self, path: str, parameters: list[tuple[str, str]] | None = None) -> str:
        url = urljoin(self.base_url, path.lstrip("/"))
        if parameters:
            url += "?" + urlencode(parameters)
        return url

    def get_json_url(self, url: str):
        with self._request(url) as response:
            return json.loads(response.read().decode("utf-8")), dict(response.headers)

    def get_json(self, path: str, parameters: list[tuple[str, str]] | None = None):
        return self.get_json_url(self.api_url(path, parameters))[0]

    def get_all(self, path: str, parameters: list[tuple[str, str]] | None = None) -> list[object]:
        query = list(parameters or []) + [("per_page", "100")]
        url: str | None = self.api_url(path, query)
        items: list[object] = []
        while url:
            payload, headers = self.get_json_url(url)
            if not isinstance(payload, list):
                raise ValueError(f"Expected a list from Canvas: {url}")
            items.extend(payload)
            url = parse_links(headers.get("Link")).get("next")
        return items

    def download(self, url: str, output: Path) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with self._request(url) as response, output.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)


def export_course(
    base_url: str,
    course_id: str,
    out_dir: Path,
    token_env: str = "CANVAS_TOKEN",
) -> dict[str, int]:
    token = os.environ.get(token_env)
    if not token:
        raise RuntimeError(f"Environment variable {token_env} is not set")
    client = CanvasClient(base_url, token)
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    course_path = f"api/v1/courses/{quote(str(course_id), safe='')}"
    modules = client.get_all(f"{course_path}/modules", [("include[]", "items")])
    (out_dir / "modules.json").write_text(json.dumps(modules, indent=2) + "\n", encoding="utf-8")

    page_summaries = client.get_all(f"{course_path}/pages")
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    pages_downloaded = 0
    for summary in page_summaries:
        if not isinstance(summary, dict) or not summary.get("url"):
            continue
        slug = str(summary["url"])
        page = client.get_json(f"{course_path}/pages/{quote(slug, safe='')}")
        filename = safe_name(slug)
        (pages_dir / f"{filename}.html").write_text(str(page.get("body", "")), encoding="utf-8")
        pages_downloaded += 1
    (out_dir / "pages.json").write_text(json.dumps(page_summaries, indent=2) + "\n", encoding="utf-8")

    files = client.get_all(f"{course_path}/files")
    files_dir = out_dir / "files"
    files_dir.mkdir(exist_ok=True)
    files_downloaded = 0
    for item in files:
        if not isinstance(item, dict) or not item.get("url"):
            continue
        filename = safe_name(str(item.get("filename") or item.get("display_name") or "file"))
        identifier = safe_name(str(item.get("id", "unknown")))
        client.download(str(item["url"]), files_dir / f"{identifier}-{filename}")
        files_downloaded += 1
    (out_dir / "files.json").write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8")

    return {
        "modules": len(modules),
        "pages": pages_downloaded,
        "files": files_downloaded,
    }

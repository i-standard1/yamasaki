#!/usr/bin/env python3
"""mkdocs serve と承認APIサーバを同時起動する。

使い方:
    python scripts/docs_serve.py

- mkdocs serve を :8000 で起動
- 承認APIを :8765 で起動 (環境変数 REVIEW_API_PORT で変更可)
- Ctrl+C で両方停止
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
API_PORT = int(os.environ.get("REVIEW_API_PORT", "8765"))
# localhost と 127.0.0.1 の両方を許可（ブラウザがどちらで開いてもCORSを通す）
ALLOWED_ORIGINS = set(
    filter(
        None,
        os.environ.get(
            "MKDOCS_ORIGIN",
            "http://localhost:8000,http://127.0.0.1:8000",
        ).split(","),
    )
)
REVIEW_ID_RE = re.compile(r"^[a-zA-Z0-9\-_]+$")


def marker_pattern(review_id: str) -> re.Pattern:
    """該当 ID のマーカー全体（open〜close）をマッチする正規表現。

    - グループ1: type 属性の値（"delete" 等、なければ None）
    - グループ2: マーカー内の本文
    """
    escaped = re.escape(review_id)
    return re.compile(
        rf"<!--\s*review:pending\s+id={escaped}"
        r"(?:\s+type=(\w+))?"
        r"\s*-->\s*\n?"
        r"(.*?)"
        r"\n?\s*<!--\s*/review\s*-->",
        re.DOTALL,
    )


WAS_NOW_RE = re.compile(
    r"\s*<!--\s*review:was\s*-->\s*\n?"
    r"(?:.*?)"  # 旧内容は破棄
    r"\n?\s*<!--\s*review:now\s*-->\s*\n?"
    r"(.*?)\s*$",
    re.DOTALL,
)


def _resolve_replacement(marker_type: str | None, body: str) -> str:
    """承認時に残すべき本文を返す。

    - type=delete → 空文字（本文ごと削除）
    - was/now 含む → now の本文だけ残す
    - それ以外 → 本文をそのまま残す
    """
    if (marker_type or "").lower() == "delete":
        return ""
    wn = WAS_NOW_RE.fullmatch(body)
    if wn:
        return wn.group(1)
    return body


class ApproveHandler(BaseHTTPRequestHandler):
    def _set_cors(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            # フォールバック（誤って開いた場合でも原因を分かりやすく）
            self.send_header(
                "Access-Control-Allow-Origin",
                next(iter(ALLOWED_ORIGINS), "http://localhost:8000"),
            )
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Vary", "Origin")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/approve":
            self.send_error(404, "Not Found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            rel_file = str(payload["file"])
            review_id = str(payload["review_id"])
        except Exception as e:  # noqa: BLE001
            self._respond_json(400, {"error": f"invalid payload: {e}"})
            return

        if not REVIEW_ID_RE.match(review_id):
            self._respond_json(400, {"error": "invalid review_id"})
            return

        # パストラバーサル防御
        try:
            target = (DOCS_DIR / rel_file).resolve()
        except (OSError, RuntimeError) as e:
            self._respond_json(400, {"error": f"bad path: {e}"})
            return
        docs_root = DOCS_DIR.resolve()
        if not (target == docs_root or str(target).startswith(str(docs_root) + os.sep)):
            self._respond_json(403, {"error": "path outside docs/"})
            return
        if target.suffix != ".md":
            self._respond_json(403, {"error": "not a markdown file"})
            return
        if not target.exists():
            self._respond_json(404, {"error": "file not found"})
            return

        # マーカー除去（3 種の type に応じて本文の扱いを分岐）
        text = target.read_text(encoding="utf-8")
        pattern = marker_pattern(review_id)
        count = 0

        def _sub(m: re.Match) -> str:
            nonlocal count
            count += 1
            return _resolve_replacement(m.group(1), m.group(2))

        new_text = pattern.sub(_sub, text)
        if count == 0:
            self._respond_json(404, {"error": "marker not found"})
            return

        # 削除で連続改行が3行以上になる場合は2行に圧縮
        new_text = re.sub(r"\n{3,}", "\n\n", new_text)

        target.write_text(new_text, encoding="utf-8")
        self._respond_json(200, {"removed": count, "file": rel_file})

    def _respond_json(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self._set_cors()
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args) -> None:  # noqa: A002
        sys.stderr.write(f"[approve-api] {format % args}\n")


def start_api_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", API_PORT), ApproveHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[approve-api] listening on http://127.0.0.1:{API_PORT}", flush=True)
    return server


def start_mkdocs() -> subprocess.Popen:
    print("[mkdocs] starting mkdocs serve ...", flush=True)
    return subprocess.Popen(["mkdocs", "serve"], cwd=str(ROOT))


def main() -> None:
    api = start_api_server()
    mk = start_mkdocs()

    def shutdown(signum=None, frame=None) -> None:
        print("\n[docs-serve] shutting down ...", flush=True)
        try:
            api.shutdown()
        except Exception:  # noqa: BLE001
            pass
        if mk.poll() is None:
            mk.terminate()
            try:
                mk.wait(timeout=5)
            except subprocess.TimeoutExpired:
                mk.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    mk.wait()
    shutdown()


if __name__ == "__main__":
    main()

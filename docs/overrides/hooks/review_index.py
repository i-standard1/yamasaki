"""MkDocs hook: 全 Markdown から未承認マーカーを集めて review-pending.md を仮想生成する。

追加 (add) / 変更 (change) / 削除 (delete) の 3 種を判別して一覧表示する。
"""

from __future__ import annotations

import re
from pathlib import Path

from mkdocs.structure.files import File

MARKER_RE = re.compile(
    r"<!--\s*review:pending\s+id=([a-zA-Z0-9\-_]+)"
    r"(?:\s+type=(\w+))?"
    r"\s*-->\s*\n?"
    r"(.*?)"
    r"\n?\s*<!--\s*/review\s*-->",
    re.DOTALL,
)

WAS_NOW_RE = re.compile(
    r"\s*<!--\s*review:was\s*-->\s*\n?"
    r"(.*?)"
    r"\n?\s*<!--\s*review:now\s*-->\s*\n?"
    r"(.*?)\s*$",
    re.DOTALL,
)

EXCERPT_MAX = 80

TYPE_LABELS = {
    "add": "➕ 追加",
    "change": "🔁 変更",
    "delete": "🗑 削除",
}


def _detect_type(marker_type: str, body: str) -> str:
    if marker_type.lower() == "delete":
        return "delete"
    if WAS_NOW_RE.fullmatch(body):
        return "change"
    return "add"


def _excerpt(body: str, kind: str) -> str:
    """一覧用の抜粋テキストを生成する。change の場合は new 側を優先表示。"""
    text = body
    if kind == "change":
        m = WAS_NOW_RE.fullmatch(body)
        if m:
            text = m.group(2)
    excerpt = " ".join(text.strip().split())
    if len(excerpt) > EXCERPT_MAX:
        excerpt = excerpt[:EXCERPT_MAX] + "…"
    return excerpt


def _collect(docs_dir: Path, files) -> list[dict]:
    entries: list[dict] = []
    for f in files:
        if not f.src_path.endswith(".md"):
            continue
        if f.src_path == "review-pending.md":
            continue
        full_path = docs_dir / f.src_path
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in MARKER_RE.finditer(text):
            kind = _detect_type(m.group(2) or "", m.group(3))
            entries.append(
                {
                    "id": m.group(1),
                    "file": f.src_path,
                    "kind": kind,
                    "excerpt": _excerpt(m.group(3), kind),
                }
            )
    return entries


def _render(entries: list[dict]) -> str:
    counts = {"add": 0, "change": 0, "delete": 0}
    for e in entries:
        counts[e["kind"]] = counts.get(e["kind"], 0) + 1

    lines = [
        "# 🔴 未承認レビュー一覧",
        "",
        f"現在 **{len(entries)} 件** の未承認マーカーがあります。",
        "",
        f"- ➕ 追加: {counts['add']} 件 / 🔁 変更: {counts['change']} 件 / 🗑 削除: {counts['delete']} 件",
        "",
    ]
    if not entries:
        lines.append("✅ 未承認マーカーはありません。")
        return "\n".join(lines) + "\n"

    lines.append("| 種別 | ID | ファイル | 抜粋 |")
    lines.append("|------|----|---------|------|")
    for e in entries:
        url_path = e["file"].removesuffix(".md") + "/"
        link = f'<a href="/{url_path}#{e["id"]}">{e["file"]}</a>'
        excerpt_safe = e["excerpt"].replace("|", "\\|")
        label = TYPE_LABELS.get(e["kind"], e["kind"])
        lines.append(f'| {label} | `{e["id"]}` | {link} | {excerpt_safe} |')
    return "\n".join(lines) + "\n"


def on_files(files, config):
    docs_dir = Path(config["docs_dir"])
    entries = _collect(docs_dir, files)
    content = _render(entries)

    files_list = [f for f in files if f.src_path != "review-pending.md"]

    generated = File.generated(
        config=config,
        src_uri="review-pending.md",
        content=content,
    )
    files_list.append(generated)

    try:
        from mkdocs.structure.files import Files

        return Files(files_list)
    except ImportError:
        return files_list

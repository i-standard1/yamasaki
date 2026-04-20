"""MkDocs hook: 全 Markdown から未承認マーカーとキーワード残存を集めて
review-pending.md を仮想生成する。

- 未承認マーカー: `<!-- review:pending ... -->` の3種 (add / change / delete)
- キーワード残存: プロジェクト直下 `review-keywords.yml` で定義された各パターン
  （要確認・確定タグ残存・TODO 等。辞書にエントリを追加するだけで増やせる）
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
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

SEVERITY_LABELS = {
    "info": "ℹ info",
    "warn": "⚠ warn",
}


def _detect_type(marker_type: str, body: str) -> str:
    if marker_type.lower() == "delete":
        return "delete"
    if WAS_NOW_RE.fullmatch(body):
        return "change"
    return "add"


def _excerpt(body: str, kind: str) -> str:
    """レビューマーカーの抜粋テキスト。change の場合は new 側を優先表示。"""
    text = body
    if kind == "change":
        m = WAS_NOW_RE.fullmatch(body)
        if m:
            text = m.group(2)
    excerpt = " ".join(text.strip().split())
    if len(excerpt) > EXCERPT_MAX:
        excerpt = excerpt[:EXCERPT_MAX] + "…"
    return excerpt


def _load_keywords(config) -> list[dict]:
    """review-keywords.yml を読み込み、各エントリを正規表現コンパイルして返す。"""
    yml_path = Path(config["config_file_path"]).parent / "review-keywords.yml"
    if not yml_path.exists():
        return []
    try:
        with yml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return []
    compiled: list[dict] = []
    for item in data.get("keywords") or []:
        pattern = item.get("pattern")
        if not pattern:
            continue
        try:
            regex = re.compile(pattern)
        except re.error:
            continue
        compiled.append(
            {
                "id": item.get("id") or "",
                "label": item.get("label") or "(unnamed)",
                "icon": item.get("icon") or "🔖",
                "severity": (item.get("severity") or "info").lower(),
                "description": item.get("description") or "",
                "regex": regex,
                "pattern": pattern,
            }
        )
    return compiled


def _line_excerpt(line: str) -> str:
    excerpt = " ".join(line.strip().split())
    if len(excerpt) > EXCERPT_MAX:
        excerpt = excerpt[:EXCERPT_MAX] + "…"
    return excerpt


def _collect(docs_dir: Path, files, keywords: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    """全 .md を走査し、レビューマーカーとキーワード残存を同時収集する。"""
    entries: list[dict] = []
    keyword_hits: dict[str, list[dict]] = {k["id"]: [] for k in keywords}
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
        if keywords:
            for line_no, line in enumerate(text.split("\n"), 1):
                for k in keywords:
                    if k["regex"].search(line):
                        keyword_hits[k["id"]].append(
                            {
                                "file": f.src_path,
                                "line": line_no,
                                "excerpt": _line_excerpt(line),
                            }
                        )
    return entries, keyword_hits


def _render(entries: list[dict], keywords: list[dict], keyword_hits: dict[str, list[dict]]) -> str:
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
    else:
        lines.append("| 種別 | ID | ファイル | 抜粋 |")
        lines.append("|------|----|---------|------|")
        for e in entries:
            url_path = e["file"].removesuffix(".md") + "/"
            link = f'<a href="/{url_path}#{e["id"]}" target="_blank" rel="noopener noreferrer">{e["file"]}</a>'
            excerpt_safe = e["excerpt"].replace("|", "\\|")
            label = TYPE_LABELS.get(e["kind"], e["kind"])
            lines.append(f'| {label} | `{e["id"]}` | {link} | {excerpt_safe} |')

    # キーワード残存セクション（review-keywords.yml 由来）
    if keywords:
        lines.extend(["", "", "## 🔎 キーワード残存一覧", ""])
        lines.append(
            "`review-keywords.yml` で定義したパターンが `docs/` 配下で一致した行を"
            "キーワードごとに一覧します。辞書にエントリを追加すれば検知対象を増やせます。"
        )
        for k in keywords:
            hits = keyword_hits.get(k["id"], [])
            sev = SEVERITY_LABELS.get(k["severity"], k["severity"])
            lines.extend(["", f'### {k["icon"]} {k["label"]}（{len(hits)} 件・{sev}）', ""])
            if k["description"].strip():
                lines.append(k["description"].strip())
                lines.append("")
            lines.append(f'正規表現: `{k["pattern"]}`')
            lines.append("")
            if not hits:
                lines.append("✅ 該当なし。")
                continue
            lines.append("| ファイル | 行 | 抜粋 |")
            lines.append("|---------|---:|------|")
            for h in hits:
                url_path = h["file"].removesuffix(".md") + "/"
                link = f'<a href="/{url_path}" target="_blank" rel="noopener noreferrer">{h["file"]}</a>'
                excerpt_safe = h["excerpt"].replace("|", "\\|")
                lines.append(f'| {link} | {h["line"]} | {excerpt_safe} |')

    return "\n".join(lines) + "\n"


def on_files(files, config):
    docs_dir = Path(config["docs_dir"])
    keywords = _load_keywords(config)
    entries, keyword_hits = _collect(docs_dir, files, keywords)
    content = _render(entries, keywords, keyword_hits)

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

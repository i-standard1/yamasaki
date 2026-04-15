"""MkDocs hook: レビュー未承認マーカーをスタイル付き div＋承認ボタンに変換する。

対応する 3 種のマーカー:

1. 追加（additive）
    <!-- review:pending id=r-... -->
    追加された段落
    <!-- /review -->

2. 変更（change）: 旧内容と新内容を持つ
    <!-- review:pending id=r-... -->
    <!-- review:was -->
    旧段落
    <!-- review:now -->
    新段落
    <!-- /review -->

3. 削除（delete）: 承認で本文ごと消える
    <!-- review:pending id=r-... type=delete -->
    削除される段落
    <!-- /review -->

`md_in_html` 拡張有効前提（mkdocs.yml 側で設定）。
"""

from __future__ import annotations

import re

# 外側のマーカー: id と optional type を捕獲
MARKER_RE = re.compile(
    r"<!--\s*review:pending\s+id=([a-zA-Z0-9\-_]+)"
    r"(?:\s+type=(\w+))?"
    r"\s*-->\s*\n?"
    r"(.*?)"
    r"\n?\s*<!--\s*/review\s*-->",
    re.DOTALL,
)

# 内側の was/now 区切り
WAS_NOW_RE = re.compile(
    r"\s*<!--\s*review:was\s*-->\s*\n?"
    r"(.*?)"
    r"\n?\s*<!--\s*review:now\s*-->\s*\n?"
    r"(.*?)\s*$",
    re.DOTALL,
)


def _approve_button(review_id: str, file_path: str) -> str:
    return (
        f'<button class="review-approve" data-review-id="{review_id}" '
        f'data-file="{file_path}">✓ 承認</button>'
    )


def _render_add(review_id: str, file_path: str, content: str) -> str:
    return (
        f'<div class="review-pending review-add" id="{review_id}" '
        f'data-review-id="{review_id}" data-file="{file_path}" markdown="1">\n\n'
        f"{_approve_button(review_id, file_path)}\n\n"
        f"{content.strip()}\n\n"
        f"</div>"
    )


def _render_change(
    review_id: str, file_path: str, was: str, now: str
) -> str:
    return (
        f'<div class="review-pending review-change" id="{review_id}" '
        f'data-review-id="{review_id}" data-file="{file_path}" markdown="1">\n\n'
        f"{_approve_button(review_id, file_path)}\n\n"
        f'<details class="review-was" markdown="1">\n'
        f"<summary>変更前を見る</summary>\n\n"
        f'<div class="review-was-body" markdown="1">\n\n'
        f"{was.strip()}\n\n"
        f"</div>\n\n"
        f"</details>\n\n"
        f"{now.strip()}\n\n"
        f"</div>"
    )


def _render_delete(review_id: str, file_path: str, content: str) -> str:
    return (
        f'<div class="review-pending review-delete" id="{review_id}" '
        f'data-review-id="{review_id}" data-file="{file_path}" markdown="1">\n\n'
        f"{_approve_button(review_id, file_path)}\n\n"
        f'<div class="review-delete-label">🗑 削除予定</div>\n\n'
        f'<div class="review-delete-body" markdown="1">\n\n'
        f"{content.strip()}\n\n"
        f"</div>\n\n"
        f"</div>"
    )


def on_page_markdown(markdown: str, page, config, files):
    """各ページの Markdown ソースに対してマーカーを div に変換する。"""
    file_path = page.file.src_path

    def replace(match: re.Match) -> str:
        review_id = match.group(1)
        marker_type = (match.group(2) or "").lower()
        body = match.group(3)

        # 削除マーカー
        if marker_type == "delete":
            return _render_delete(review_id, file_path, body)

        # was/now を持つか判定
        wn = WAS_NOW_RE.fullmatch(body)
        if wn:
            return _render_change(review_id, file_path, wn.group(1), wn.group(2))

        # 追加
        return _render_add(review_id, file_path, body)

    return MARKER_RE.sub(replace, markdown)

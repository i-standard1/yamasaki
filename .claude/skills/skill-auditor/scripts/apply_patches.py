#!/usr/bin/env python3
"""
apply_patches.py — パッチ適用ツール

improvement-planner が生成したパッチを SKILL.md の description に適用する。
dry-run モードで差分表示、--apply で実際に書き込み。

依存: Python 3.9+ 標準ライブラリのみ
"""

import argparse
import json
import re
import sys
from pathlib import Path


def load_patches(patches_path: Path) -> list[dict]:
    """patches.json を読み込み"""
    with open(patches_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("patches", [])


def find_skill_md(skills_dir: Path, skill_name: str) -> Path | None:
    """スキル名から SKILL.md のパスを解決"""
    candidate = skills_dir / skill_name / "SKILL.md"
    if candidate.exists():
        return candidate

    # ディレクトリ名がスキル名と一致しない場合、frontmatter で検索
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
            continue
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            if f"name: {skill_name}" in content:
                return skill_md

    return None


def extract_description(content: str) -> tuple[str, int, int]:
    """frontmatter から description を抽出し、開始行と終了行を返す"""
    lines = content.split("\n")
    desc_start = -1
    desc_end = -1
    in_desc = False
    in_frontmatter = False

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip() == "---":
            if desc_start >= 0 and desc_end < 0:
                desc_end = i
            break

        if in_frontmatter:
            if line.startswith("description:"):
                in_desc = True
                desc_start = i
                # インライン値がある場合
                val = line.split(":", 1)[1].strip()
                if val and val != "|":
                    desc_end = i + 1
                    in_desc = False
                continue

            if in_desc:
                # 新しいトップレベルキー（インデントなし）
                if line and not line[0].isspace() and ":" in line:
                    desc_end = i
                    in_desc = False
                    continue

    return (
        "\n".join(lines[desc_start:desc_end]) if desc_start >= 0 else "",
        desc_start,
        desc_end,
    )


def apply_patch_to_content(
    content: str, current_desc: str, proposed_desc: str
) -> str | None:
    """description 部分を新しい内容に置換"""
    if not current_desc or not proposed_desc:
        return None

    # frontmatter 内の description ブロックを置換
    # 安全のため、current_description の一部でマッチ
    current_lines = current_desc.strip().split("\n")
    if len(current_lines) < 1:
        return None

    # description: | 形式の場合
    if "description: |" in content or "description:|" in content:
        old_block, start, end = extract_description(content)
        if start < 0:
            return None

        lines = content.split("\n")
        # proposed_desc を description: | 形式に整形
        new_desc_lines = ["description: |"]
        for pline in proposed_desc.strip().split("\n"):
            new_desc_lines.append(f"  {pline}")

        new_lines = lines[:start] + new_desc_lines + lines[end:]
        return "\n".join(new_lines)

    return None


def preview_patch(patch: dict, skills_dir: Path) -> None:
    """パッチの差分をプレビュー表示"""
    patch_id = patch.get("patch_id", "?")
    priority = patch.get("priority", "?")
    targets = patch.get("target_skills", [])
    problem = patch.get("problem", "")
    current = patch.get("current_description", "")
    proposed = patch.get("proposed_description", "")
    cascade = patch.get("cascade_check", {})

    print(f"\n{'='*60}")
    print(f"  {patch_id} [{priority.upper()}] — {', '.join(targets)}")
    print(f"  Problem: {problem}")
    print(f"  Cascade risk: {cascade.get('risk_level', 'unknown')}")
    if cascade.get("affected_skills"):
        print(f"  Affected: {', '.join(cascade['affected_skills'])}")
    print(f"{'='*60}")

    print(f"\n--- CURRENT ---")
    print(current[:300] if current else "(empty)")
    print(f"\n+++ PROPOSED +++")
    print(proposed[:300] if proposed else "(empty)")

    for target in targets:
        skill_md = find_skill_md(skills_dir, target)
        if skill_md:
            print(f"\n  File: {skill_md}")
        else:
            print(f"\n  WARNING: SKILL.md not found for '{target}'")


def apply_single_patch(patch: dict, skills_dir: Path) -> bool:
    """単一パッチを適用"""
    targets = patch.get("target_skills", [])
    current = patch.get("current_description", "")
    proposed = patch.get("proposed_description", "")

    if not proposed:
        print(f"  SKIP: No proposed description")
        return False

    success = True
    for target in targets:
        skill_md = find_skill_md(skills_dir, target)
        if not skill_md:
            print(f"  ERROR: SKILL.md not found for '{target}'")
            success = False
            continue

        content = skill_md.read_text(encoding="utf-8")
        new_content = apply_patch_to_content(content, current, proposed)

        if new_content is None:
            print(f"  ERROR: Could not apply patch to '{target}'")
            success = False
            continue

        skill_md.write_text(new_content, encoding="utf-8")
        print(f"  APPLIED: {skill_md}")

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Apply or preview skill improvement patches"
    )
    parser.add_argument("--patches", required=True, help="patches.json file path")
    parser.add_argument("--skills-dir", required=True, help=".claude/skills/ directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview only (default)",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Actually apply patches"
    )
    parser.add_argument(
        "--priority",
        choices=["high", "medium", "low", "all"],
        default="all",
        help="Filter patches by priority",
    )
    args = parser.parse_args()

    patches_path = Path(args.patches)
    skills_dir = Path(args.skills_dir)

    if not patches_path.exists():
        print(f"ERROR: {patches_path} not found", file=sys.stderr)
        sys.exit(1)

    patches = load_patches(patches_path)

    # 優先度フィルタ
    if args.priority != "all":
        patches = [p for p in patches if p.get("priority") == args.priority]

    print(f"Patches: {len(patches)} ({args.priority})")

    if args.apply and not args.dry_run:
        print("\n*** APPLYING PATCHES ***\n")
        applied = 0
        for patch in patches:
            patch_id = patch.get("patch_id", "?")
            print(f"\nApplying {patch_id}...")
            if apply_single_patch(patch, skills_dir):
                applied += 1
        print(f"\nApplied: {applied}/{len(patches)}")
    else:
        print("\n*** DRY RUN (preview only) ***\n")
        for patch in patches:
            preview_patch(patch, skills_dir)
        print(f"\nTo apply: re-run with --apply (remove --dry-run)")


if __name__ == "__main__":
    main()

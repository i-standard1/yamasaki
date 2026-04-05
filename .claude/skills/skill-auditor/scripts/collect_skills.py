#!/usr/bin/env python3
"""
collect_skills.py — スキル定義収集・トークン計測

.claude/skills/ 配下の全 SKILL.md を走査し、frontmatter・description・
コンテキスト依存・トークン予算を構造化して出力する。

依存: Python 3.9+ 標準ライブラリのみ
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def estimate_tokens(text: str) -> int:
    """トークン数を推定（単語数 × 1.3、日本語は文字数 × 0.5 を加算）"""
    # 英語単語
    words = len(re.findall(r"[a-zA-Z]+", text))
    # 日本語文字（ひらがな・カタカナ・漢字）
    jp_chars = len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", text))
    return int(words * 1.3 + jp_chars * 0.5)


def count_instructions(text: str) -> int:
    """指示文の数をカウント（命令形・「〜すること」「〜してください」等）"""
    patterns = [
        r"してください",
        r"すること[。\n]",
        r"しないこと[。\n]",
        r"使用する[。\n]",
        r"実行する[。\n]",
        r"[A-Z][a-z]+ (the|this|each|all|every)",  # 英語命令形
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text))
    return count


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """YAML frontmatter をパース（PyYAML 不要の簡易パーサー）"""
    frontmatter = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()

            current_key = None
            current_value_lines = []

            for line in fm_text.split("\n"):
                # インデントされた行（継続行）
                if line.startswith("  ") or line.startswith("\t"):
                    if current_key:
                        current_value_lines.append(line.strip("- ").strip())
                    continue

                # 前のキーを保存
                if current_key:
                    val = "\n".join(current_value_lines).strip()
                    if val.startswith("|"):
                        val = val[1:].strip()
                    frontmatter[current_key] = val
                    current_value_lines = []

                # 新しいキー
                if ":" in line:
                    key, _, value = line.partition(":")
                    current_key = key.strip()
                    value = value.strip()
                    if value and value != "|":
                        current_value_lines = [value]
                    else:
                        current_value_lines = []

            # 最後のキー
            if current_key:
                val = "\n".join(current_value_lines).strip()
                if val.startswith("|"):
                    val = val[1:].strip()
                frontmatter[current_key] = val

    return frontmatter, body


def parse_context_required(content: str) -> list[str]:
    """context.required のリストを frontmatter 内からのみ抽出"""
    refs = []

    # frontmatter ブロックのみを対象にする
    if not content.startswith("---"):
        return refs
    parts = content.split("---", 2)
    if len(parts) < 3:
        return refs
    fm_text = parts[1]

    in_context = False
    in_required = False

    for line in fm_text.split("\n"):
        stripped = line.strip()
        if stripped == "context:":
            in_context = True
            continue
        if in_context and stripped == "required:":
            in_required = True
            continue
        if in_context and stripped.startswith("on_error:"):
            in_required = False
            continue
        if in_required and stripped.startswith("- "):
            refs.append(stripped[2:].strip())
        elif in_required and not stripped.startswith(" ") and stripped and ":" in stripped:
            in_required = False
            in_context = False

    return refs


def check_context_exists(refs: list[str], skills_dir: Path) -> list[dict]:
    """コンテキスト参照先の存在確認"""
    results = []
    for ref in refs:
        ref_path = skills_dir / ref
        results.append({
            "ref": ref,
            "exists": ref_path.exists(),
        })
    return results


def collect_skills(skills_dir: str) -> dict:
    """全スキル定義を収集"""
    skills_path = Path(skills_dir)
    skills = []
    total_description_tokens = 0
    issues = []

    for skill_dir in sorted(skills_path.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith("_"):
            continue  # _shared は除外

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        content = skill_md.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)
        context_refs = parse_context_required(content)

        name = frontmatter.get("name", skill_dir.name)
        description = frontmatter.get("description", "")

        token_count = estimate_tokens(description)
        instruction_count = count_instructions(description)
        total_description_tokens += token_count

        # コンテキスト参照チェック
        context_check = check_context_exists(context_refs, skills_path)
        missing_refs = [c["ref"] for c in context_check if not c["exists"]]
        if missing_refs:
            issues.append({
                "skill": name,
                "issue": "missing_context_refs",
                "details": missing_refs,
            })

        # on_error ハンドラの有無
        has_error_handler = "on_error:" in content

        # agents/ ディレクトリの有無
        agents_dir = skill_dir / "agents"
        has_agents = agents_dir.exists() and any(agents_dir.iterdir()) if agents_dir.exists() else False

        skills.append({
            "name": name,
            "directory": str(skill_dir),
            "description": description,
            "description_token_count": token_count,
            "instruction_density": instruction_count,
            "context_required": context_refs,
            "context_check": context_check,
            "has_error_handler": has_error_handler,
            "has_agents": has_agents,
            "body_line_count": len(body.split("\n")),
        })

    # _shared ファイル一覧
    shared_dir = skills_path / "_shared"
    shared_files = []
    if shared_dir.exists():
        shared_files = [f.name for f in sorted(shared_dir.iterdir()) if f.is_file()]

    return {
        "collected_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "skills_dir": str(skills_path),
        "summary": {
            "total_skills": len(skills),
            "total_description_tokens": total_description_tokens,
            "shared_files": len(shared_files),
            "issues_found": len(issues),
        },
        "attention_budget": {
            "total_tokens": total_description_tokens,
            "status": (
                "healthy" if total_description_tokens <= 2000
                else "caution" if total_description_tokens <= 3000
                else "warning"
            ),
        },
        "skills": skills,
        "shared_files": shared_files,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Collect skill definitions and measure token budgets"
    )
    parser.add_argument(
        "--skills-dir",
        required=True,
        help="Path to .claude/skills/ directory",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file path",
    )
    args = parser.parse_args()

    skills_dir = os.path.abspath(args.skills_dir)
    output_path = Path(args.output)

    print(f"Collecting skills from: {skills_dir}")

    result = collect_skills(skills_dir)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    summary = result["summary"]
    budget = result["attention_budget"]
    print(f"Skills: {summary['total_skills']}")
    print(f"Total description tokens: {summary['total_description_tokens']} ({budget['status']})")
    print(f"Shared files: {summary['shared_files']}")
    if summary["issues_found"] > 0:
        print(f"Issues: {summary['issues_found']}")
        for issue in result["issues"]:
            print(f"  - {issue['skill']}: {issue['issue']} {issue['details']}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()

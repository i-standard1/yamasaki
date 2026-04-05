#!/usr/bin/env python3
"""
collect_transcripts.py — セッショントランスクリプト収集・パーサー

Claude Code のセッション JSONL を走査し、スキルルーティング分析に
必要な情報を構造化して出力する。

依存: Python 3.9+ 標準ライブラリのみ（外部パッケージ不要）
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Claude Code 組み込みコマンド（スキル判定から除外）
BUILTIN_COMMANDS = {
    "help", "clear", "model", "permissions", "config", "doctor",
    "memory", "compact", "cost", "status", "logout", "login",
    "init", "review", "bug", "pr-comments", "terminal-setup",
    "listen", "vim", "ide", "mcp", "approved-tools", "fast",
}


def encode_project_path(project_dir: str) -> str:
    """プロジェクトパスを Claude Code のディレクトリ命名規則に変換"""
    return "-" + project_dir.lstrip("/").replace("/", "-")


def find_session_dir(project_dir: str) -> Path | None:
    """プロジェクトに対応するセッションディレクトリを検索"""
    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.exists():
        return None

    encoded = encode_project_path(project_dir)
    target = claude_projects / encoded
    if target.exists():
        return target

    # 部分一致フォールバック（シンボリックリンク等）
    for d in claude_projects.iterdir():
        if d.is_dir() and encoded in d.name:
            return d

    return None


def parse_session_jsonl(filepath: Path) -> dict:
    """単一セッション JSONL をパースして構造化"""
    session_id = filepath.stem
    turns = []
    metadata = {
        "session_id": session_id,
        "file_path": str(filepath),
        "version": None,
        "entrypoint": None,
        "cwd": None,
        "git_branch": None,
    }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type")

                # メタデータ抽出（最初のユーザーメッセージから）
                if entry_type == "user" and metadata["version"] is None:
                    metadata["version"] = entry.get("version")
                    metadata["entrypoint"] = entry.get("entrypoint")
                    metadata["cwd"] = entry.get("cwd")
                    metadata["git_branch"] = entry.get("gitBranch")

                # ユーザーメッセージ
                if entry_type == "user":
                    msg = entry.get("message", {})
                    content_parts = msg.get("content", [])
                    text_parts = []
                    for part in content_parts:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif isinstance(part, str):
                            text_parts.append(part)

                    if text_parts:
                        turns.append({
                            "turn_index": len(turns),
                            "type": "user",
                            "uuid": entry.get("uuid"),
                            "timestamp": entry.get("timestamp"),
                            "text": "\n".join(text_parts)[:500],  # 500文字で切り詰め
                        })

                # アシスタントメッセージ（ツール呼び出し抽出）
                elif entry_type == "assistant":
                    msg = entry.get("message", {})
                    content_parts = msg.get("content", [])
                    usage = msg.get("usage", {})
                    model = msg.get("model", "")

                    tool_calls = []
                    for part in content_parts:
                        if isinstance(part, dict) and part.get("type") == "tool_use":
                            tool_name = part.get("name", "")
                            tool_input = part.get("input", {})

                            tool_entry = {
                                "tool_name": tool_name,
                            }

                            # Skill ツール → スキル発火
                            if tool_name == "Skill":
                                skill_name = tool_input.get("skill", "")
                                tool_entry["skill_invoked"] = skill_name
                                tool_entry["skill_args"] = tool_input.get("args")

                            # Agent ツール → サブエージェント起動
                            elif tool_name == "Agent":
                                tool_entry["agent_description"] = tool_input.get(
                                    "description", ""
                                )
                                tool_entry["agent_subtype"] = tool_input.get(
                                    "subagent_type"
                                )
                                tool_entry["agent_model"] = tool_input.get("model")

                            tool_calls.append(tool_entry)

                    if tool_calls:
                        turns.append({
                            "turn_index": len(turns),
                            "type": "assistant_tools",
                            "uuid": entry.get("uuid"),
                            "timestamp": entry.get("timestamp"),
                            "model": model,
                            "tool_calls": tool_calls,
                            "usage": {
                                "input_tokens": usage.get("input_tokens", 0),
                                "output_tokens": usage.get("output_tokens", 0),
                                "cache_read": usage.get(
                                    "cache_read_input_tokens", 0
                                ),
                            },
                        })

    except (OSError, PermissionError) as e:
        print(f"  WARNING: Could not read {filepath}: {e}", file=sys.stderr)
        return None

    if not turns:
        return None

    metadata["turn_count"] = len(turns)
    return {
        "metadata": metadata,
        "turns": turns,
    }


def collect_all_sessions(project_dir: str) -> dict:
    """全セッションを収集"""
    session_dir = find_session_dir(project_dir)
    if session_dir is None:
        return {
            "error": f"No session directory found for project: {project_dir}",
            "searched_path": str(
                Path.home() / ".claude" / "projects" / encode_project_path(project_dir)
            ),
            "sessions": [],
            "summary": {"total_sessions": 0, "total_turns": 0},
        }

    sessions = []
    jsonl_files = sorted(session_dir.glob("*.jsonl"))

    for jsonl_file in jsonl_files:
        # サブエージェントディレクトリ内の JSONL は除外
        if "subagents" in str(jsonl_file):
            continue
        parsed = parse_session_jsonl(jsonl_file)
        if parsed is not None:
            sessions.append(parsed)

    # スキル発火サマリー
    skill_fires = {}
    total_turns = 0
    for session in sessions:
        total_turns += session["metadata"]["turn_count"]
        for turn in session["turns"]:
            if turn["type"] == "assistant_tools":
                for tc in turn.get("tool_calls", []):
                    if "skill_invoked" in tc:
                        name = tc["skill_invoked"]
                        skill_fires[name] = skill_fires.get(name, 0) + 1

    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "project_dir": project_dir,
        "session_dir": str(session_dir),
        "summary": {
            "total_sessions": len(sessions),
            "total_turns": total_turns,
            "skill_fire_counts": skill_fires,
        },
        "sessions": sessions,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Collect Claude Code session transcripts for skill auditing"
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Absolute path to the project directory",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file path",
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    output_path = Path(args.output)

    print(f"Collecting transcripts for: {project_dir}")

    result = collect_all_sessions(project_dir)

    # 出力ディレクトリ作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    summary = result["summary"]
    print(f"Sessions: {summary['total_sessions']}")
    print(f"Turns: {summary['total_turns']}")
    print(f"Skill fires: {json.dumps(summary['skill_fire_counts'], ensure_ascii=False)}")
    print(f"Output: {output_path}")

    if summary["total_sessions"] == 0:
        print(
            f"\nWARNING: No sessions found. Searched: {result.get('searched_path', 'N/A')}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

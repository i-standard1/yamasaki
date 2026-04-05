#!/usr/bin/env python3
"""
generate_report.py — HTML レポート生成 + health-history 更新

Phase 3-5 の中間成果物を統合し、視覚的な HTML レポートを生成する。
health-history.json に今回の実行結果を追記して経時変化を追跡する。

依存: Python 3.9+ 標準ライブラリのみ
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from string import Template


def load_json(path: Path) -> dict | None:
    """JSON ファイルを安全に読み込み"""
    if not path.exists():
        print(f"WARNING: {path} not found", file=sys.stderr)
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_routing_batches(run_dir: Path) -> list:
    """routing/ 配下の全バッチ結果を統合"""
    routing_dir = run_dir / "routing"
    if not routing_dir.exists():
        return []

    all_judgments = []
    for batch_file in sorted(routing_dir.glob("batch_*.json")):
        data = load_json(batch_file)
        if data and isinstance(data, list):
            all_judgments.extend(data)
        elif data and isinstance(data, dict) and "judgments" in data:
            all_judgments.extend(data["judgments"])
    return all_judgments


def compute_metrics(portfolio: dict, routing_judgments: list) -> dict:
    """主要指標を算出"""
    accuracy = portfolio.get("routing_accuracy", {})
    total = accuracy.get("total_evaluated", 0)
    correct = accuracy.get("correct", 0)

    return {
        "routing_precision": round(correct / total, 3) if total > 0 else 0,
        "total_evaluated": total,
        "correct": correct,
        "false_negatives": accuracy.get("false_negative", 0),
        "false_positives": accuracy.get("false_positive", 0),
        "confused": accuracy.get("confused", 0),
        "coverage_gaps": len(portfolio.get("coverage_gaps", [])),
        "competition_pairs": len(portfolio.get("competition_matrix", [])),
        "dead_skills": len(portfolio.get("dead_skills", [])),
        "attention_budget_status": portfolio.get("attention_budget", {}).get(
            "status", "unknown"
        ),
        "total_description_tokens": portfolio.get("attention_budget", {}).get(
            "total_tokens", 0
        ),
    }


def update_health_history(history_path: Path, metrics: dict, run_id: str) -> None:
    """health-history.json に今回の結果を追記"""
    history = []
    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = []

    entry = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **metrics,
    }
    history.append(entry)

    # 直近 50 回分のみ保持
    history = history[-50:]

    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def generate_skill_cards_html(portfolio: dict) -> str:
    """スキル別ヘルスカードの HTML を生成"""
    budget = portfolio.get("attention_budget", {})
    per_skill = budget.get("per_skill", [])

    if not per_skill:
        return "<p>No per-skill data available.</p>"

    rows = []
    for skill in sorted(per_skill, key=lambda s: s.get("fire_count", 0), reverse=True):
        name = skill.get("name", "?")
        tokens = skill.get("token_count", 0)
        fires = skill.get("fire_count", 0)
        density = skill.get("instruction_density", 0)
        rows.append(
            f"<tr><td>{name}</td><td>{tokens}</td>"
            f"<td>{density}</td><td>{fires}</td></tr>"
        )

    return f"""
    <table>
      <thead><tr><th>Skill</th><th>Tokens</th><th>Instructions</th><th>Fires</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    """


def generate_competition_html(portfolio: dict) -> str:
    """Competition Matrix の HTML を生成"""
    matrix = portfolio.get("competition_matrix", [])
    if not matrix:
        return "<p>No competition pairs detected.</p>"

    rows = []
    for pair in matrix:
        risk_class = "danger" if pair.get("confused_count", 0) >= 2 else "warning"
        rows.append(
            f'<tr class="{risk_class}">'
            f"<td>{pair.get('skill_a', '?')}</td>"
            f"<td>{pair.get('skill_b', '?')}</td>"
            f"<td>{pair.get('type', '?')}</td>"
            f"<td>{pair.get('similarity_score', 0):.2f}</td>"
            f"<td>{pair.get('confused_count', 0)}</td></tr>"
        )

    return f"""
    <table>
      <thead><tr><th>Skill A</th><th>Skill B</th><th>Type</th><th>Similarity</th><th>Confused</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    """


def generate_patches_html(patches: dict) -> str:
    """パッチ提案の HTML を生成"""
    patch_list = patches.get("patches", [])
    if not patch_list:
        return "<p>No improvement patches proposed.</p>"

    cards = []
    for p in patch_list:
        priority_class = p.get("priority", "low")
        cascade = p.get("cascade_check", {})
        risk = cascade.get("risk_level", "safe")
        cards.append(f"""
        <div class="patch-card {priority_class}">
          <h4>{p.get('patch_id', '?')} — {p.get('type', '?')} [{priority_class.upper()}]</h4>
          <p><strong>Target:</strong> {', '.join(p.get('target_skills', []))}</p>
          <p><strong>Problem:</strong> {p.get('problem', '')}</p>
          <div class="diff">
            <div class="diff-old"><strong>Current:</strong><pre>{p.get('current_description', '')}</pre></div>
            <div class="diff-new"><strong>Proposed:</strong><pre>{p.get('proposed_description', '')}</pre></div>
          </div>
          <p><strong>Cascade Risk:</strong> <span class="risk-{risk}">{risk}</span>
             — Affected: {', '.join(cascade.get('affected_skills', []) or ['none'])}</p>
          <p><em>{p.get('rationale', '')}</em></p>
        </div>
        """)

    return "\n".join(cards)


def generate_html(
    template_path: Path,
    portfolio: dict,
    patches: dict,
    metrics: dict,
    run_id: str,
) -> str:
    """テンプレートにデータを注入して HTML を生成"""
    if template_path.exists():
        template_str = template_path.read_text(encoding="utf-8")
    else:
        # テンプレートがない場合はインラインフォールバック
        template_str = FALLBACK_TEMPLATE

    t = Template(template_str)
    return t.safe_substitute(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        routing_precision=f"{metrics['routing_precision']:.1%}",
        total_evaluated=metrics["total_evaluated"],
        correct=metrics["correct"],
        false_negatives=metrics["false_negatives"],
        false_positives=metrics["false_positives"],
        confused=metrics["confused"],
        coverage_gaps=metrics["coverage_gaps"],
        competition_pairs=metrics["competition_pairs"],
        dead_skills=metrics["dead_skills"],
        attention_status=metrics["attention_budget_status"],
        total_tokens=metrics["total_description_tokens"],
        skill_cards=generate_skill_cards_html(portfolio),
        competition_matrix=generate_competition_html(portfolio),
        patches_html=generate_patches_html(patches),
    )


FALLBACK_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Skill Audit Report — $run_id</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 2rem; background: #f8f9fa; }
  .header { background: #1a1a2e; color: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
  .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
  .metric-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .metric-card h3 { margin: 0 0 0.5rem; color: #666; font-size: 0.9rem; }
  .metric-card .value { font-size: 2rem; font-weight: bold; }
  .metric-card .value.good { color: #2d6a4f; }
  .metric-card .value.warn { color: #e76f51; }
  table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; }
  th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #f1f3f5; font-weight: 600; }
  tr.danger { background: #fff5f5; }
  tr.warning { background: #fffbeb; }
  .patch-card { background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #aaa; }
  .patch-card.high { border-left-color: #e63946; }
  .patch-card.medium { border-left-color: #f4a261; }
  .patch-card.low { border-left-color: #2a9d8f; }
  .diff { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }
  .diff pre { background: #f8f9fa; padding: 1rem; border-radius: 4px; white-space: pre-wrap; font-size: 0.85rem; }
  .diff-old pre { border-left: 3px solid #e63946; }
  .diff-new pre { border-left: 3px solid #2d6a4f; }
  .risk-safe { color: #2d6a4f; }
  .risk-caution { color: #f4a261; }
  .risk-danger { color: #e63946; }
  h2 { color: #1a1a2e; margin-top: 2rem; }
</style>
</head>
<body>
<div class="header">
  <h1>Skill Audit Report</h1>
  <p>Run: $run_id | Generated: $timestamp</p>
</div>

<div class="metrics">
  <div class="metric-card"><h3>Routing Precision</h3><div class="value">$routing_precision</div></div>
  <div class="metric-card"><h3>Total Evaluated</h3><div class="value">$total_evaluated</div></div>
  <div class="metric-card"><h3>False Negatives</h3><div class="value warn">$false_negatives</div></div>
  <div class="metric-card"><h3>Confused</h3><div class="value warn">$confused</div></div>
  <div class="metric-card"><h3>Coverage Gaps</h3><div class="value">$coverage_gaps</div></div>
  <div class="metric-card"><h3>Competition Pairs</h3><div class="value warn">$competition_pairs</div></div>
  <div class="metric-card"><h3>Attention Budget</h3><div class="value">$total_tokens tok ($attention_status)</div></div>
  <div class="metric-card"><h3>Dead Skills</h3><div class="value">$dead_skills</div></div>
</div>

<h2>Skill Health Cards</h2>
$skill_cards

<h2>Competition Matrix</h2>
$competition_matrix

<h2>Improvement Patches</h2>
$patches_html

</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML audit report and update health history"
    )
    parser.add_argument("--run-dir", required=True, help="Run directory path")
    parser.add_argument("--template", default=None, help="HTML template path")
    parser.add_argument("--history", default=None, help="Health history JSON path")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    run_id = run_dir.name
    output_path = Path(args.output)

    # 中間成果物の読み込み
    portfolio = load_json(run_dir / "portfolio.json") or {}
    patches = load_json(run_dir / "patches.json") or {}
    routing_judgments = load_routing_batches(run_dir)

    # 指標算出
    metrics = compute_metrics(portfolio, routing_judgments)

    # HTML 生成
    template_path = Path(args.template) if args.template else Path("nonexistent")
    html = generate_html(template_path, portfolio, patches, metrics, run_id)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {output_path}")
    print(f"Routing precision: {metrics['routing_precision']:.1%}")
    print(f"False negatives: {metrics['false_negatives']}")
    print(f"Competition pairs: {metrics['competition_pairs']}")
    print(f"Patches proposed: {len(patches.get('patches', []))}")

    # health-history 更新
    if args.history:
        history_path = Path(args.history)
        update_health_history(history_path, metrics, run_id)
        print(f"Health history updated: {history_path}")


if __name__ == "__main__":
    main()

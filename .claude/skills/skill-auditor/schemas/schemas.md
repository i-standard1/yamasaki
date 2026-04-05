# Skill Auditor JSON Schemas

サブエージェントの出力フォーマットを定義する JSON Schema 集。
各エージェントはこのスキーマに準拠した JSON を出力すること。

---

## 1. TranscriptEntry

collect_transcripts.py が出力するセッション単位の構造。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TranscriptEntry",
  "type": "object",
  "required": ["metadata", "turns"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["session_id", "turn_count"],
      "properties": {
        "session_id": { "type": "string" },
        "file_path": { "type": "string" },
        "version": { "type": ["string", "null"] },
        "entrypoint": { "type": ["string", "null"] },
        "cwd": { "type": ["string", "null"] },
        "git_branch": { "type": ["string", "null"] },
        "turn_count": { "type": "integer" }
      }
    },
    "turns": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["turn_index", "type"],
        "properties": {
          "turn_index": { "type": "integer" },
          "type": { "enum": ["user", "assistant_tools"] },
          "uuid": { "type": "string" },
          "timestamp": { "type": "string" },
          "text": { "type": "string" },
          "model": { "type": "string" },
          "tool_calls": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["tool_name"],
              "properties": {
                "tool_name": { "type": "string" },
                "skill_invoked": { "type": "string" },
                "skill_args": { "type": ["string", "null"] },
                "agent_description": { "type": "string" },
                "agent_subtype": { "type": ["string", "null"] },
                "agent_model": { "type": ["string", "null"] }
              }
            }
          },
          "usage": {
            "type": "object",
            "properties": {
              "input_tokens": { "type": "integer" },
              "output_tokens": { "type": "integer" },
              "cache_read": { "type": "integer" }
            }
          }
        }
      }
    }
  }
}
```

---

## 2. SkillProfile

collect_skills.py が出力するスキル単位の構造。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SkillProfile",
  "type": "object",
  "required": ["name", "description", "description_token_count"],
  "properties": {
    "name": { "type": "string" },
    "directory": { "type": "string" },
    "description": { "type": "string" },
    "description_token_count": { "type": "integer" },
    "instruction_density": { "type": "integer" },
    "context_required": { "type": "array", "items": { "type": "string" } },
    "context_check": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "ref": { "type": "string" },
          "exists": { "type": "boolean" }
        }
      }
    },
    "has_error_handler": { "type": "boolean" },
    "has_agents": { "type": "boolean" },
    "body_line_count": { "type": "integer" }
  }
}
```

---

## 3. RoutingJudgment

routing-analyst エージェントが出力する判定単位の構造。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RoutingJudgment",
  "type": "object",
  "required": ["session_id", "turn_index", "judgment", "confidence"],
  "properties": {
    "session_id": { "type": "string" },
    "turn_index": { "type": "integer" },
    "user_message_summary": { "type": "string", "maxLength": 50 },
    "actual_skill": { "type": ["string", "null"] },
    "expected_skill": { "type": ["string", "null"] },
    "judgment": {
      "enum": [
        "correct", "false_negative", "false_positive",
        "confused", "no_skill_needed", "explicit_invocation",
        "coverage_gap"
      ]
    },
    "confidence": { "enum": ["high", "medium", "low"] },
    "reasoning": { "type": "string", "maxLength": 200 }
  }
}
```

---

## 4. PortfolioMetrics

portfolio-analyst エージェントが出力する構造。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PortfolioMetrics",
  "type": "object",
  "required": ["run_summary", "attention_budget", "routing_accuracy"],
  "properties": {
    "run_summary": {
      "type": "object",
      "properties": {
        "total_sessions": { "type": "integer" },
        "total_turns": { "type": "integer" },
        "total_skills": { "type": "integer" },
        "analysis_timestamp": { "type": "string", "format": "date-time" }
      }
    },
    "attention_budget": {
      "type": "object",
      "properties": {
        "total_tokens": { "type": "integer" },
        "status": { "enum": ["healthy", "caution", "warning"] },
        "per_skill": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "token_count": { "type": "integer" },
              "instruction_density": { "type": "integer" },
              "fire_count": { "type": "integer" }
            }
          }
        }
      }
    },
    "competition_matrix": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "skill_a": { "type": "string" },
          "skill_b": { "type": "string" },
          "type": { "enum": ["nested", "adjacent", "overlapping"] },
          "similarity_score": { "type": "number", "minimum": 0, "maximum": 1 },
          "confused_count": { "type": "integer" },
          "evidence": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "dead_skills": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "status": { "enum": ["dead_candidate", "manual_only", "low_usage"] },
          "fire_count": { "type": "integer" },
          "recommendation": { "type": "string" }
        }
      }
    },
    "coverage_gaps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "intent_category": { "type": "string" },
          "occurrence_count": { "type": "integer" },
          "example_messages": { "type": "array", "items": { "type": "string" } },
          "proposed_skill": { "type": ["string", "null"] }
        }
      }
    },
    "routing_accuracy": {
      "type": "object",
      "properties": {
        "total_evaluated": { "type": "integer" },
        "correct": { "type": "integer" },
        "false_negative": { "type": "integer" },
        "false_positive": { "type": "integer" },
        "confused": { "type": "integer" },
        "no_skill_needed": { "type": "integer" },
        "explicit_invocation": { "type": "integer" },
        "coverage_gap": { "type": "integer" },
        "precision": { "type": "number" },
        "recall": { "type": "number" }
      }
    }
  }
}
```

---

## 5. ImprovementPatch

improvement-planner エージェントが出力するパッチ単位の構造。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ImprovementPatch",
  "type": "object",
  "required": ["patch_id", "priority", "type", "target_skills"],
  "properties": {
    "patch_id": { "type": "string", "pattern": "^PATCH-\\d{3}$" },
    "priority": { "enum": ["high", "medium", "low"] },
    "type": {
      "enum": [
        "description_rewrite", "boundary_clarification",
        "keyword_injection", "scope_reduction",
        "coordinated_patch", "deprecation"
      ]
    },
    "target_skills": { "type": "array", "items": { "type": "string" } },
    "problem": { "type": "string" },
    "evidence": {
      "type": "object",
      "properties": {
        "judgment_category": { "type": "string" },
        "occurrence_count": { "type": "integer" },
        "session_refs": { "type": "array", "items": { "type": "string" } }
      }
    },
    "current_description": { "type": "string" },
    "proposed_description": { "type": "string" },
    "cascade_check": {
      "type": "object",
      "properties": {
        "affected_skills": { "type": "array", "items": { "type": "string" } },
        "similarity_before": { "type": "number" },
        "similarity_after": { "type": "number" },
        "risk_level": { "enum": ["safe", "caution", "danger"] }
      }
    },
    "rationale": { "type": "string" }
  }
}
```

---

## 6. AuditReport

generate_report.py が使用する統合レポート構造。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AuditReport",
  "type": "object",
  "required": ["run_id", "timestamp", "metrics"],
  "properties": {
    "run_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "metrics": {
      "type": "object",
      "properties": {
        "routing_precision": { "type": "number" },
        "total_evaluated": { "type": "integer" },
        "correct": { "type": "integer" },
        "false_negatives": { "type": "integer" },
        "false_positives": { "type": "integer" },
        "confused": { "type": "integer" },
        "coverage_gaps": { "type": "integer" },
        "competition_pairs": { "type": "integer" },
        "dead_skills": { "type": "integer" },
        "attention_budget_status": { "type": "string" },
        "total_description_tokens": { "type": "integer" }
      }
    }
  }
}
```

---

## 7. HealthHistory

health-history.json のエントリ構造。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "HealthHistoryEntry",
  "type": "object",
  "required": ["run_id", "timestamp", "routing_precision"],
  "properties": {
    "run_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "routing_precision": { "type": "number" },
    "total_evaluated": { "type": "integer" },
    "correct": { "type": "integer" },
    "false_negatives": { "type": "integer" },
    "false_positives": { "type": "integer" },
    "confused": { "type": "integer" },
    "coverage_gaps": { "type": "integer" },
    "competition_pairs": { "type": "integer" },
    "dead_skills": { "type": "integer" },
    "attention_budget_status": { "type": "string" },
    "total_description_tokens": { "type": "integer" }
  }
}
```

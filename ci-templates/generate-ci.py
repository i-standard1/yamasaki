#!/usr/bin/env python3
"""
CI ワークフロー自動生成スクリプト

CLAUDE.md の技術スタック設定を読み取り、プロジェクトに最適な
.github/workflows/ci.yml を生成する。

使い方:
  python3 ci-templates/generate-ci.py [--claude-md path] [--output path] [--repo-structure monorepo|separated|single]

init-spec スキルから自動的に呼ばれるが、単体でも実行可能。
"""

import argparse
import re
import sys
import textwrap
from pathlib import Path


# ============================================================
# 技術スタック → CI コマンドのマッピング
# ============================================================

LINT_COMMANDS = {
    # Node.js 系
    "express": "npm run lint",
    "nestjs": "npm run lint",
    "next.js": "npm run lint",
    "nuxt": "npm run lint",
    "vue": "npm run lint",
    "react": "npm run lint",
    # Python 系
    "django": "ruff check . || flake8 .",
    "fastapi": "ruff check . || flake8 .",
    # Ruby 系
    "rails": "bundle exec rubocop",
    # Go
    "go": "golangci-lint run",
    # Java
    "spring-boot": "./gradlew checkstyleMain || mvn checkstyle:check",
}

TYPECHECK_COMMANDS = {
    # TypeScript 系（tsc --noEmit）
    "express": "npx tsc --noEmit",
    "nestjs": "npx tsc --noEmit",
    "next.js": "npx tsc --noEmit",
    "nuxt": "npx nuxi typecheck",
    "vue": "npx vue-tsc --noEmit",
    "react": "npx tsc --noEmit",
    # Python 系（mypy）
    "django": "mypy . --ignore-missing-imports || true",
    "fastapi": "mypy . --ignore-missing-imports || true",
    # Go（ビルド時に型チェック）
    "go": "go build ./...",
    # Java
    "spring-boot": "./gradlew compileJava || mvn compile",
}

UNIT_TEST_COMMANDS = {
    "jest": {
        "run": "npx jest --ci --coverage --json --outputFile=jest-results.json",
        "result_check": 'python3 -c "import json; r=json.load(open(\'jest-results.json\')); print(\'true\' if r.get(\'success\', False) else \'false\')"',
        "result_file": "jest-results.json",
        "artifacts": ["jest-results.json", "coverage/"],
    },
    "vitest": {
        "run": "npx vitest run --coverage --reporter=json --outputFile=vitest-results.json",
        "result_check": 'python3 -c "import json; r=json.load(open(\'vitest-results.json\')); print(\'true\' if r.get(\'success\', False) else \'false\')"',
        "result_file": "vitest-results.json",
        "artifacts": ["vitest-results.json", "coverage/"],
    },
    "pytest": {
        "run": "pytest --tb=short --junitxml=pytest-results.xml -q",
        "result_check": "echo $?",
        "result_file": "pytest-results.xml",
        "artifacts": ["pytest-results.xml", "htmlcov/"],
    },
    "rspec": {
        "run": "bundle exec rspec --format documentation --format json --out rspec-results.json",
        "result_check": 'python3 -c "import json; r=json.load(open(\'rspec-results.json\')); print(\'true\' if r.get(\'summary\',{}).get(\'failure_count\',1)==0 else \'false\')"',
        "result_file": "rspec-results.json",
        "artifacts": ["rspec-results.json", "coverage/"],
    },
    "go-test": {
        "run": "go test -v -coverprofile=coverage.out ./... 2>&1 | tee test-output.txt",
        "result_check": "echo $?",
        "result_file": "test-output.txt",
        "artifacts": ["test-output.txt", "coverage.out"],
    },
}

E2E_TEST_COMMANDS = {
    "playwright": {
        "install": "npx playwright install --with-deps",
        "install_deps_only": "npx playwright install-deps",
        "run": "npx playwright test",
        "cache_key_files": "playwright.config.*",
        "cache_path": "~/.cache/ms-playwright",
        "artifacts": ["playwright-report/", "test-results/"],
    },
    "cypress": {
        "install": "npx cypress install",
        "install_deps_only": "npx cypress install",
        "run": "npx cypress run",
        "cache_key_files": "cypress.config.*",
        "cache_path": "~/.cache/Cypress",
        "artifacts": ["cypress/screenshots/", "cypress/videos/"],
    },
}

PACKAGE_MANAGERS = {
    "npm": {"install": "npm ci", "cache": "npm", "lockfile": "package-lock.json"},
    "yarn": {"install": "yarn install --frozen-lockfile", "cache": "yarn", "lockfile": "yarn.lock"},
    "pnpm": {"install": "pnpm install --frozen-lockfile", "cache": "pnpm", "lockfile": "pnpm-lock.yaml"},
    "pip": {"install": "pip install -r requirements.txt", "cache": "pip", "lockfile": "requirements.txt"},
    "poetry": {"install": "poetry install", "cache": "pip", "lockfile": "poetry.lock"},
    "bundler": {"install": "bundle install", "cache": "bundler", "lockfile": "Gemfile.lock"},
    "go": {"install": "go mod download", "cache": "go", "lockfile": "go.sum"},
}

SETUP_ACTIONS = {
    "npm": ("actions/setup-node@v4", "node-version", "22"),
    "yarn": ("actions/setup-node@v4", "node-version", "22"),
    "pnpm": ("actions/setup-node@v4", "node-version", "22"),
    "pip": ("actions/setup-python@v5", "python-version", "3.12"),
    "poetry": ("actions/setup-python@v5", "python-version", "3.12"),
    "bundler": ("ruby/setup-ruby@v1", "ruby-version", "3.3"),
    "go": ("actions/setup-go@v5", "go-version", "1.22"),
}


# ============================================================
# CLAUDE.md パーサー
# ============================================================

def parse_claude_md(path: str) -> dict:
    """CLAUDE.md から技術スタック設定を読み取る"""
    text = Path(path).read_text(encoding="utf-8")
    fields = {}
    for key in ["project_type", "backend", "frontend", "db", "auth",
                 "test_unit", "test_e2e", "api_style"]:
        # "- key: value" 形式を探す（コメントやプレースホルダーは除外）
        m = re.search(rf"^\s*-\s*{key}\s*:\s*(.+)$", text, re.MULTILINE)
        if m:
            val = m.group(1).strip()
            # HTMLコメントやプレースホルダーを除外
            if val.startswith("<!--") or val.startswith("例:") or not val:
                fields[key] = None
            else:
                fields[key] = val.split("#")[0].strip()  # インラインコメント除去
        else:
            fields[key] = None
    return fields


def detect_package_manager(project_root: str, backend: str = "") -> str:
    """プロジェクトルートからパッケージマネージャを推定。ファイルがなければ backend から推定。"""
    root = Path(project_root)
    # 1. ロックファイルから検出（最も信頼性が高い）
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "package-lock.json").exists() or (root / "package.json").exists():
        return "npm"
    if (root / "poetry.lock").exists() or (root / "pyproject.toml").exists():
        return "poetry"
    if (root / "requirements.txt").exists():
        return "pip"
    if (root / "Gemfile.lock").exists() or (root / "Gemfile").exists():
        return "bundler"
    if (root / "go.mod").exists():
        return "go"
    # 2. ファイルがなければ backend の値から推定
    backend_key = resolve_backend_key(backend)
    backend_to_pm = {
        "rails": "bundler",
        "django": "pip",
        "fastapi": "poetry",
        "express": "npm",
        "nestjs": "npm",
        "spring-boot": "go",  # gradle/maven は別枠だが go mod に近い
        "go": "go",
    }
    return backend_to_pm.get(backend_key, "npm")


def detect_repo_structure(project_root: str) -> str:
    """モノレポ / 分離 / 単体を自動判定"""
    root = Path(project_root)
    # apps/ や packages/ があればモノレポ
    if (root / "apps").is_dir() or (root / "packages").is_dir():
        return "monorepo"
    # turbo.json や nx.json があればモノレポ
    if (root / "turbo.json").exists() or (root / "nx.json").exists():
        return "monorepo"
    return "single"


def resolve_backend_key(backend: str) -> str:
    """CLAUDE.md の backend 値を正規化（バージョン番号除去）"""
    if not backend:
        return ""
    # "rails 7.1" → "rails", "next.js 14" → "next.js"
    key = backend.split()[0].lower().rstrip(",")
    return key


def resolve_frontend_key(frontend: str) -> str:
    if not frontend or frontend.lower() == "none":
        return ""
    return frontend.split()[0].lower().rstrip(",")


# ============================================================
# YAML ジェネレータ
# ============================================================

class CIGenerator:
    def __init__(self, config: dict, pkg_mgr: str, repo_structure: str):
        self.config = config
        self.pkg_mgr = pkg_mgr
        self.repo_structure = repo_structure
        self.backend_key = resolve_backend_key(config.get("backend"))
        self.frontend_key = resolve_frontend_key(config.get("frontend"))
        self.test_unit = config.get("test_unit", "").lower() if config.get("test_unit") else ""
        self.test_e2e = config.get("test_e2e", "").lower() if config.get("test_e2e") else ""
        self.has_frontend = bool(self.frontend_key)
        self.has_backend = bool(self.backend_key)

        # パッケージマネージャ情報
        self.pm = PACKAGE_MANAGERS.get(pkg_mgr, PACKAGE_MANAGERS["npm"])
        self.setup_action = SETUP_ACTIONS.get(pkg_mgr, SETUP_ACTIONS["npm"])

    def _indent(self, text: str, level: int) -> str:
        return textwrap.indent(textwrap.dedent(text).strip(), "  " * level)

    def _lint_cmd(self, key: str) -> str:
        return LINT_COMMANDS.get(key, f"echo 'No lint configured for {key}'")

    def _typecheck_cmd(self, key: str) -> str:
        return TYPECHECK_COMMANDS.get(key, f"echo 'No typecheck configured for {key}'")

    def generate(self) -> str:
        if self.repo_structure == "monorepo":
            return self._gen_monorepo()
        elif self.repo_structure == "separated-front":
            return self._gen_separated_front()
        elif self.repo_structure == "separated-back":
            return self._gen_separated_back()
        else:
            return self._gen_single()

    # ----------------------------------------------------------
    # 共通パーツ
    # ----------------------------------------------------------

    def _header(self) -> str:
        return textwrap.dedent(f"""\
        # 自動生成: ci-templates/generate-ci.py
        # 技術スタック: backend={self.config.get('backend','none')} frontend={self.config.get('frontend','none')}
        #              test_unit={self.test_unit or 'none'} test_e2e={self.test_e2e or 'none'}
        # リポ構成: {self.repo_structure}
        #
        # 再生成: python3 ci-templates/generate-ci.py
        name: CI
        on:
          pull_request:
            types: [opened, synchronize]

        permissions:
          contents: read
          pull-requests: write
        """)

    def _setup_steps(self, extra_setup: str = "") -> str:
        action, version_key, version_val = self.setup_action
        lines = f"""\
      - uses: actions/checkout@v4
      - uses: {action}
        with:
          {version_key}: '{version_val}'"""
        if self.pm.get("cache"):
            lines += f"\n          cache: '{self.pm['cache']}'"
        lines += f"\n      - run: {self.pm['install']}"
        if extra_setup:
            lines += f"\n{extra_setup}"
        return lines

    def _unit_job(self, name: str = "Unit Tests", workdir: str = "", needs: str = "lint") -> str:
        if not self.test_unit or self.test_unit not in UNIT_TEST_COMMANDS:
            return ""
        tc = UNIT_TEST_COMMANDS[self.test_unit]
        cd_prefix = f"cd {workdir} && " if workdir else ""
        cd_line = f"\n          cd {workdir}" if workdir else ""
        artifact_prefix = f"{workdir}/" if workdir else ""
        artifacts = "\n            ".join(f"{artifact_prefix}{a}" for a in tc["artifacts"])
        job_id = f"unit-{workdir.split('/')[-1]}" if workdir else "unit"

        # テスト結果判定: Python可の場合はJSON解析、そうでなければexit code
        if "json" in tc["result_check"]:
            result_check = textwrap.dedent(f"""\
              if [ -f {tc['result_file']} ]; then
                SUCCESS=$({tc['result_check']} 2>/dev/null || echo "false")
              else
                SUCCESS="false"
              fi
              echo "success=${{SUCCESS}}" >> $GITHUB_OUTPUT""")
        else:
            result_check = ""

        run_cmd = tc["run"]
        # exit code ベースのフレームワーク
        if "json" not in tc["result_check"]:
            fail_step = ""
            run_block = textwrap.dedent(f"""\
        - name: Run {self.test_unit}{cd_line}
          run: |
            {cd_prefix}{run_cmd}""")
        else:
            run_block = textwrap.dedent(f"""\
        - name: Run {self.test_unit}
          id: test
          run: |{cd_line}
            {cd_prefix}{run_cmd} 2>&1 | tee unit-output.txt || true
            {textwrap.indent(result_check, '            ').strip()}""")
            fail_step = textwrap.dedent("""\
        - name: Fail if tests failed
          if: steps.test.outputs.success != 'true'
          run: exit 1""")

        return textwrap.dedent(f"""\
  {job_id}:
    name: {name}
    needs: [{needs}]
    runs-on: ubuntu-latest
    steps:
{self._setup_steps()}
      {run_block.strip()}
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: {job_id}-results
          path: |
            {artifacts}
          retention-days: 30
      {fail_step.strip()}
""")

    def _e2e_job(self, needs: str = "unit", workdir: str = "", start_cmds: str = "") -> str:
        if not self.test_e2e or self.test_e2e == "none" or self.test_e2e not in E2E_TEST_COMMANDS:
            return ""
        ec = E2E_TEST_COMMANDS[self.test_e2e]
        cd_prefix = f"cd {workdir} && " if workdir else ""
        artifact_prefix = f"{workdir}/" if workdir else ""
        artifacts = "\n            ".join(f"{artifact_prefix}{a}" for a in ec["artifacts"])
        cache_key_extra = f", '{workdir}/{ec['cache_key_files']}'" if workdir else f"'{ec['cache_key_files']}'"

        start_section = ""
        if start_cmds:
            start_section = f"\n{start_cmds}\n"

        return textwrap.dedent(f"""\
  e2e:
    name: E2E Tests ({self.test_e2e.capitalize()})
    needs: [{needs}]
    runs-on: ubuntu-latest
    steps:
{self._setup_steps()}

      - name: Cache {self.test_e2e} browsers
        id: e2e-cache
        uses: actions/cache@v4
        with:
          path: {ec['cache_path']}
          key: {self.test_e2e}-${{{{ runner.os }}}}-${{{{ hashFiles('{self.pm["lockfile"]}', {cache_key_extra}) }}}}
      - name: Install {self.test_e2e} browsers
        if: steps.e2e-cache.outputs.cache-hit != 'true'
        run: {ec['install']}
      - name: Install {self.test_e2e} deps only
        if: steps.e2e-cache.outputs.cache-hit == 'true'
        run: {ec['install_deps_only']}
{start_section}
      - name: Run {self.test_e2e}
        id: e2e-run
        run: |
          {cd_prefix}{ec['run']} 2>&1 | tee e2e-output.txt
          echo "exit_code=$?" >> $GITHUB_OUTPUT
        env:
          CI: true

      - name: Upload E2E evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-evidence
          path: |
            {artifacts}
          retention-days: 30
""")

    def _ai_review_job(self, needs: str = "e2e") -> str:
        return textwrap.dedent(f"""\
  ai-review:
    name: AI Review
    needs: [{needs}]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{{{ github.event.pull_request.head.ref }}}}
          fetch-depth: 0

      - name: Build prompt and call Claude API
        id: review
        env:
          ANTHROPIC_API_KEY: ${{{{ secrets.ANTHROPIC_API_KEY }}}}
          REVIEW_MODEL: ${{{{ vars.REVIEW_MODEL || 'claude-sonnet-4-5-20250929' }}}}
          PR_TITLE: ${{{{ github.event.pull_request.title }}}}
          PR_BODY: ${{{{ github.event.pull_request.body }}}}
          BASE_REF: ${{{{ github.event.pull_request.base.ref }}}}
        run: |
          git diff "origin/${{BASE_REF}}...HEAD" > /tmp/pr-diff.txt

          python3 - <<'PYTHON_SCRIPT'
          import json, os, re, urllib.request

          template = open('.github/review-prompt.md').read()
          diff = open('/tmp/pr-diff.txt').read()[:10000]
          title = os.environ.get('PR_TITLE', '')
          body = os.environ.get('PR_BODY', '')

          design_intent = ''
          try:
              design_intent = open('DESIGN_INTENT.md').read()
          except FileNotFoundError:
              pass

          prompt = (template
              .replace('{{{{TITLE}}}}', title)
              .replace('{{{{BODY}}}}', body)
              .replace('{{{{DIFF}}}}', diff)
              .replace('{{{{DESIGN_INTENT}}}}', design_intent))

          payload = json.dumps({{
              "model": os.environ.get('REVIEW_MODEL', 'claude-sonnet-4-5-20250929'),
              "max_tokens": 2000,
              "messages": [{{"role": "user", "content": prompt}}]
          }}).encode()

          req = urllib.request.Request(
              'https://api.anthropic.com/v1/messages',
              data=payload,
              headers={{
                  'content-type': 'application/json',
                  'x-api-key': os.environ['ANTHROPIC_API_KEY'],
                  'anthropic-version': '2023-06-01',
              }}
          )

          try:
              with urllib.request.urlopen(req) as res:
                  data = json.loads(res.read())
          except urllib.error.HTTPError as e:
              print(f"API Error: {{e.code}}")
              with open('/tmp/review-comment.txt', 'w') as f:
                  f.write(f'API Error: {{e.code}}')
              with open('/tmp/fixes.txt', 'w') as f:
                  f.write('')
              with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                  f.write('approved=false\\n')
              exit(0)

          text = data.get('content', [{{}}])[0].get('text', '')
          fence_match = re.search(r'```(?:json)?\\s*\\n?(.*?)\\n?```', text, re.DOTALL)
          json_str = fence_match.group(1).strip() if fence_match else text.strip()

          try:
              review = json.loads(json_str)
          except json.JSONDecodeError:
              review = {{"approved": False, "comment": "Review parse failed", "fixes_needed": []}}

          with open('/tmp/review-comment.txt', 'w') as f:
              f.write(review.get('comment', ''))
          with open('/tmp/fixes.txt', 'w') as f:
              f.write('\\n'.join(review.get('fixes_needed', [])))
          with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
              f.write(f'approved={{str(review.get("approved", False)).lower()}}\\n')
          PYTHON_SCRIPT

      - name: Post review comment
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const approved = '${{{{ steps.review.outputs.approved }}}}' === 'true';
            let comment = '', fixes = '';
            try {{ comment = fs.readFileSync('/tmp/review-comment.txt', 'utf8'); }} catch {{ comment = 'Manual review required.'; }}
            try {{ fixes = fs.readFileSync('/tmp/fixes.txt', 'utf8').trim(); }} catch {{}}

            let body = `## 🤖 AI Review\\n\\n`;
            body += approved ? '✅ **Approved**\\n\\n' : '⚠️ **Changes Requested**\\n\\n';
            body += comment + '\\n\\n';
            if (fixes) {{
              body += `### Fixes Needed\\n`;
              fixes.split('\\n').filter(f => f).forEach(f => {{ body += `- ${{f}}\\n`; }});
            }}

            const comments = await github.rest.issues.listComments({{
              issue_number: context.issue.number, owner: context.repo.owner, repo: context.repo.repo,
            }});
            const botComment = comments.data.find(c => c.user.type === 'Bot' && c.body.includes('AI Review'));
            if (botComment) {{
              await github.rest.issues.updateComment({{ comment_id: botComment.id, owner: context.repo.owner, repo: context.repo.repo, body }});
            }} else {{
              await github.rest.issues.createComment({{ issue_number: context.issue.number, owner: context.repo.owner, repo: context.repo.repo, body }});
            }}
""")

    def _spec_health_job(self) -> str:
        return textwrap.dedent("""\
  spec-health:
    name: Spec Health Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check spec-map.yml
        id: check
        run: |
          if [ -f spec-map.yml ]; then
            echo "exists=true" >> $GITHUB_OUTPUT
          else
            echo "exists=false" >> $GITHUB_OUTPUT
          fi
      - name: Validate spec-map consistency
        if: steps.check.outputs.exists == 'true'
        run: |
          python3 -c "
          import yaml, sys
          with open('spec-map.yml') as f:
              data = yaml.safe_load(f) or {}
          issues = []
          for req_id, entry in data.items():
              if not isinstance(entry, dict): continue
              sv = entry.get('spec_version', 0)
              for item in entry.get('implementation', []) or []:
                  if isinstance(item, dict) and item.get('confirmed', 0) < sv:
                      issues.append(f'{req_id}: {item.get(\"path\",\"?\")}')
              for item in entry.get('tests', []) or []:
                  if isinstance(item, dict) and item.get('confirmed', 0) < sv:
                      issues.append(f'{req_id}: {item.get(\"path\",\"?\")}')
          if issues:
              print('::warning::Spec-Code mismatch: ' + '; '.join(issues))
              sys.exit(1)
          "
""")

    def _summary_job(self, job_ids: list) -> str:
        needs_str = ", ".join(job_ids)
        results_lines = "\n".join(
            f"              '{jid}': '${{{{ needs.{jid}.result }}}}'"
            + ("," if i < len(job_ids) - 1 else "")
            for i, jid in enumerate(job_ids)
        )
        return textwrap.dedent(f"""\
  summary:
    name: PR Summary
    needs: [{needs_str}]
    if: always()
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - name: Post summary comment
        uses: actions/github-script@v7
        with:
          script: |
            const results = {{
{results_lines}
            }};

            const icon = r => r === 'success' ? '✅' : r === 'skipped' ? '⏭️' : '❌';
            const label = r => r === 'success' ? 'Pass' : r === 'skipped' ? 'Skip' : 'Fail';
            const artifactUrl = `${{{{context.serverUrl}}}}/${{{{context.repo.owner}}}}/${{{{context.repo.repo}}}}/actions/runs/${{{{context.runId}}}}`;

            let body = `## 🧪 CI Pipeline Results\\n\\n`;
            body += `| Stage | Result |\\n|-------|--------|\\n`;
            for (const [name, result] of Object.entries(results)) {{
              body += `| ${{name}} | ${{icon(result)}} ${{label(result)}} |\\n`;
            }}
            body += `\\n📦 **Artifacts:** [Download](${{artifactUrl}})\\n`;

            const comments = await github.rest.issues.listComments({{
              issue_number: context.issue.number, owner: context.repo.owner, repo: context.repo.repo,
            }});
            const botComment = comments.data.find(c => c.user.type === 'Bot' && c.body.includes('CI Pipeline Results'));
            if (botComment) {{
              await github.rest.issues.updateComment({{ comment_id: botComment.id, owner: context.repo.owner, repo: context.repo.repo, body }});
            }} else {{
              await github.rest.issues.createComment({{ issue_number: context.issue.number, owner: context.repo.owner, repo: context.repo.repo, body }});
            }}
""")

    # ----------------------------------------------------------
    # 構成別ジェネレータ
    # ----------------------------------------------------------

    def _gen_single(self) -> str:
        """単体リポ（フロント or バック 1つ）"""
        jobs = []
        job_ids = ["lint"]

        # lint
        key = self.backend_key or self.frontend_key
        lint_cmd = self._lint_cmd(key)
        tc_cmd = self._typecheck_cmd(key)

        out = self._header()
        out += textwrap.dedent(f"""\
jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
{self._setup_steps()}
      - name: Lint
        run: {lint_cmd}
      - name: Type check
        run: {tc_cmd}

""")

        # unit
        unit = self._unit_job(needs="lint")
        if unit:
            out += unit
            job_ids.append("unit")
            last_test = "unit"
        else:
            last_test = "lint"

        # e2e
        e2e = self._e2e_job(needs=last_test)
        if e2e:
            out += e2e
            job_ids.append("e2e")
            last_test = "e2e"

        # spec health
        out += self._spec_health_job()
        job_ids.append("spec-health")

        # ai review
        out += self._ai_review_job(needs=last_test)
        job_ids.append("ai-review")

        # summary
        out += self._summary_job(job_ids)
        return out

    def _gen_monorepo(self) -> str:
        """モノレポ（apps/web + apps/api 等）"""
        out = self._header()

        # lint: front + back
        out += textwrap.dedent(f"""\
jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
{self._setup_steps()}
      - name: Lint (frontend)
        run: npm run lint --workspace=apps/web
      - name: Lint (backend)
        run: npm run lint --workspace=apps/api
      - name: Type check (frontend)
        run: {self._typecheck_cmd(self.frontend_key)} --project apps/web/tsconfig.json
      - name: Type check (backend)
        run: {self._typecheck_cmd(self.backend_key)} --project apps/api/tsconfig.json

""")
        job_ids = ["lint"]

        # unit-front
        unit_front = self._unit_job(name="Unit Tests (Frontend)", workdir="apps/web", needs="lint")
        if unit_front:
            out += unit_front
            job_ids.append("unit-front")

        # unit-back
        unit_back = self._unit_job(name="Unit Tests (Backend)", workdir="apps/api", needs="lint")
        if unit_back:
            # Fix job ID
            unit_back = unit_back.replace("unit-web:", "unit-front:").replace("  unit-api:", "  unit-back:")
            out += unit_back
            job_ids.append("unit-back")

        # e2e (needs both units)
        unit_needs = [j for j in job_ids if j.startswith("unit")]
        e2e_needs = ", ".join(unit_needs) if unit_needs else "lint"

        start_cmds = textwrap.dedent("""\
      - name: Start backend
        run: |
          cd apps/api
          npm run start:dev &
          npx wait-on http://localhost:3001/api/health --timeout 30000
        env:
          NODE_ENV: test

      - name: Start frontend
        run: |
          cd apps/web
          npm run dev &
          npx wait-on http://localhost:3000 --timeout 30000
        env:
          NODE_ENV: test""")

        e2e = self._e2e_job(needs=e2e_needs, workdir="apps/web", start_cmds=start_cmds)
        if e2e:
            out += e2e
            job_ids.append("e2e")
            last_test = "e2e"
        else:
            last_test = unit_needs[-1] if unit_needs else "lint"

        out += self._spec_health_job()
        job_ids.append("spec-health")

        out += self._ai_review_job(needs=last_test)
        job_ids.append("ai-review")

        out += self._summary_job(job_ids)
        return out

    def _gen_separated_front(self) -> str:
        """分離リポ・フロント"""
        out = self._header()

        key = self.frontend_key
        out += textwrap.dedent(f"""\
env:
  BACKEND_REPO: ${{{{ github.repository_owner }}}}/CHANGE-ME-backend
  BACKEND_HEALTH: 'http://localhost:3001/api/health'

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
{self._setup_steps()}
      - name: Lint
        run: {self._lint_cmd(key)}
      - name: Type check
        run: {self._typecheck_cmd(key)}

""")
        job_ids = ["lint"]

        unit = self._unit_job(needs="lint")
        if unit:
            out += unit
            job_ids.append("unit")
            last_test = "unit"
        else:
            last_test = "lint"

        # e2e with backend checkout
        start_cmds = textwrap.dedent("""\
      - name: Detect backend branch
        id: backend-branch
        run: |
          BRANCH="${{ github.head_ref }}"
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \\
            -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" \\
            "https://api.github.com/repos/${{ env.BACKEND_REPO }}/branches/${BRANCH}")
          if [ "$STATUS" = "200" ]; then
            echo "ref=${BRANCH}" >> $GITHUB_OUTPUT
          else
            echo "ref=main" >> $GITHUB_OUTPUT
          fi

      - name: Checkout backend
        uses: actions/checkout@v4
        with:
          repository: ${{ env.BACKEND_REPO }}
          ref: ${{ steps.backend-branch.outputs.ref }}
          path: backend

      - name: Install backend deps
        run: cd backend && """ + self.pm["install"] + """

      - name: Start backend
        run: |
          cd backend
          npm run start:dev &
          npx wait-on ${{ env.BACKEND_HEALTH }} --timeout 30000
        env:
          NODE_ENV: test""")

        e2e = self._e2e_job(needs=last_test, start_cmds=start_cmds)
        if e2e:
            out += e2e
            job_ids.append("e2e")
            last_test = "e2e"

        out += self._spec_health_job()
        job_ids.append("spec-health")

        out += self._ai_review_job(needs=last_test)
        job_ids.append("ai-review")

        out += self._summary_job(job_ids)
        return out

    def _gen_separated_back(self) -> str:
        """分離リポ・バック（E2Eなし）"""
        out = self._header()

        key = self.backend_key
        out += textwrap.dedent(f"""\
jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
{self._setup_steps()}
      - name: Lint
        run: {self._lint_cmd(key)}
      - name: Type check
        run: {self._typecheck_cmd(key)}

""")
        job_ids = ["lint"]

        unit = self._unit_job(needs="lint")
        if unit:
            out += unit
            job_ids.append("unit")
            last_test = "unit"
        else:
            last_test = "lint"

        out += self._spec_health_job()
        job_ids.append("spec-health")

        out += self._ai_review_job(needs=last_test)
        job_ids.append("ai-review")

        out += self._summary_job(job_ids)
        return out


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Generate CI workflow from CLAUDE.md")
    parser.add_argument("--claude-md", default="CLAUDE.md", help="Path to CLAUDE.md")
    parser.add_argument("--output", default=".github/workflows/ci.yml", help="Output path")
    parser.add_argument("--repo-structure", choices=["monorepo", "separated-front", "separated-back", "single", "auto"],
                        default="auto", help="Repository structure")
    parser.add_argument("--project-root", default=".", help="Project root for auto-detection")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing file")
    args = parser.parse_args()

    # CLAUDE.md 解析
    config = parse_claude_md(args.claude_md)

    # 未設定チェック
    missing = [k for k, v in config.items() if not v and k in ("test_unit",)]
    if missing:
        print(f"⚠️  CLAUDE.md に未設定の項目があります: {', '.join(missing)}", file=sys.stderr)
        print("  init-spec で技術スタックを設定してから再実行してください。", file=sys.stderr)
        sys.exit(1)

    # パッケージマネージャ検出
    pkg_mgr = detect_package_manager(args.project_root, config.get("backend", ""))

    # リポ構成判定
    if args.repo_structure == "auto":
        repo_structure = detect_repo_structure(args.project_root)
    else:
        repo_structure = args.repo_structure

    print(f"📋 検出結果:", file=sys.stderr)
    print(f"   backend:    {config.get('backend', 'none')}", file=sys.stderr)
    print(f"   frontend:   {config.get('frontend', 'none')}", file=sys.stderr)
    print(f"   test_unit:  {config.get('test_unit', 'none')}", file=sys.stderr)
    print(f"   test_e2e:   {config.get('test_e2e', 'none')}", file=sys.stderr)
    print(f"   pkg_mgr:    {pkg_mgr}", file=sys.stderr)
    print(f"   structure:  {repo_structure}", file=sys.stderr)

    # 生成
    gen = CIGenerator(config, pkg_mgr, repo_structure)
    yml = gen.generate()

    if args.dry_run:
        print(yml)
    else:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(yml, encoding="utf-8")
        print(f"✅ {args.output} を生成しました", file=sys.stderr)


if __name__ == "__main__":
    main()

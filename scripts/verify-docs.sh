#!/usr/bin/env bash
set -euo pipefail

required=(
  "README.md"
  "README.txt"
  "CHANGELOG.md"
  "CONTRIBUTING.md"
  "LICENSE"
  "LICENSE-CODE"
  "LICENSE-DOCS"
  ".gitignore"
  "AGENTS.md"
  "USER-MANUAL.md"
  "SECURITY.md"
  "SUPPORT.md"
  "CODE_OF_CONDUCT.md"
  ".github/PULL_REQUEST_TEMPLATE.md"
  ".github/ISSUE_TEMPLATE/bug_report.md"
  ".github/ISSUE_TEMPLATE/feature_request.md"
  ".github/ISSUE_TEMPLATE/config.yml"
  "docs/RECONCILIATION.md"
  "docs/MILESTONES.md"
  "docs/IMPLEMENTATION_PLAN.md"
  "docs/github-discussions-seed.md"
  "MILESTONE_0_7_DONE.md"
  "docs/index.html"
  "pyproject.toml"
  "townlight_notice/__init__.py"
  "townlight_notice/main.py"
  "townlight_notice/accessibility_review.py"
  "townlight_notice/archive_packet.py"
  "townlight_notice/notice_registry.py"
  "townlight_notice/deadline_tracker.py"
  "townlight_notice/statutory_rules.py"
  "townlight_notice/notice_templates.py"
  "townlight_notice/publication_check.py"
  "townlight_notice/channel_plan.py"
  "townlight_notice/subscriber_delivery.py"
  "townlight_notice/records_export.py"
  "townlight_notice/public_ui.py"
)

echo "==> Required-artifact check"
for file in "${required[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "FAIL: missing required artifact: $file" >&2
    exit 1
  fi
done

echo "==> Current-facing shipped/planned truth check"
current_files=("README.md" "README.txt" "USER-MANUAL.md" "docs/index.html")
bad_markers=(
  "official legal sufficiency decisions are available"
  "legal advice is available"
  "official publication is available"
  "live LLM calls are available"
  "publication-system write-back is available"
  "system-of-record integrations are available"
  "production staff-review queues are available"
)

DOCS_PYTHON="${TOWNLIGHT_NOTICE_RELEASE_PYTHON:-python}"
"${DOCS_PYTHON}" - <<'PY'
from pathlib import Path

current_files = ("README.md", "README.txt", "USER-MANUAL.md", "docs/index.html")
bad_markers = (
    "official legal sufficiency decisions are available",
    "legal advice is available",
    "official publication is available",
    "live LLM calls are available",
    "publication-system write-back is available",
    "system-of-record integrations are available",
    "production staff-review queues are available",
)

for filename in current_files:
    text = Path(filename).read_text(encoding="utf-8").casefold()
    for marker in bad_markers:
        if marker.casefold() in text:
            raise SystemExit(
                f"FAIL: stale/planned-as-shipped marker '{marker}' found in {filename}"
            )
PY

echo "VERIFY-DOCS: PASSED"

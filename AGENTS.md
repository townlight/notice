<a id="civicnotice-agent-board"></a>

# Townlight Notice Agent Board

## Source of Truth

- Upstream suite spec: `townlight/townlight/docs/CivicSuiteUnifiedSpec.md`, especially the Townlight Notice catalog entry and suite-wide non-negotiables.
- Townlight Notice supports central notice registry stubs, deadline tracking, publication readiness tracking, channel planning, and public-records-aware export checklists.
- Staff own every decision.

## Hard Boundaries

- Townlight Notice never decides legal sufficiency, publishes official notices, provides legal advice, writes back to publication systems, or updates a notice system of record.
- Townlight Notice v0.2.0 must not call live LLMs or live agenda systems.
- deadline tracking, publication readiness tracking, channel planning, and records exports must be marked staff-review-required where applicable.
- Townlight Notice depends on Townlight Core; Townlight Core must never depend on Townlight Notice.
- Townlight Notice may reference Townlight Meetings meeting concepts only through released APIs or deterministic sample data in v0.2.0.

## Verification

Run `bash scripts/verify-release.sh` before every push or release.

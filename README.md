<a id="townlight_notice"></a>

# Townlight Notice

## Windows staff workflow — 0.3.0 candidate

This candidate is prepared; exact signed-installer acceptance is pending. It supports a fresh profile, not an in-place upgrade of an unmarked legacy database. The existing compatibility profile path is retained and existing data is refused before initialization.

1. Sign in with an account allowed to use Notice and open Public Notices. Create a draft with title, actual notice text, type, event date, staff-selected calendar lead days and staff-verified statutory basis. Save it. Its deadline workpaper uses the shared Core reminder helper; it does not establish legal sufficiency.
2. Select the saved notice, read the deadline workpaper and source, enter review notes, then record staff review. Approve that saved revision only after the responsible staff member has checked the law, timing, content and channels. Mechanical rule success never removes the staff-review requirement.
3. Perform official publication outside Townlight. Retain the actual proof file (up to 5 MB each and 10 MB total for the current approved content), posting location and actual posting date/time including time zone. A filename, target system name or checklist alone is not posting proof.
4. Create the archive after approval and proof. The archive contains the actual notice, retained proof bytes, review/approval history and a per-file SHA-256/size manifest. Write and verify the ZIP export to preserve a usable file. ZIP entry timestamps are fixed for deterministic packaging; the record contains the recorded posting and audit times.
5. For a Records handoff, enter the intended Records request UUID and select Attach archive to Records. This requires Records authority as well as Notice authority. Townlight retains an exact managed copy, verifies its hash, attaches it through the canonical Records writer and reports the request/archive identity and hash. Repeating the same handoff does not create a duplicate attachment. Open the request in Records and read back the attached archive. Disclosure still requires Records review/release authority.

Saved notices and history can be reopened from Public Notices. A content edit clears the prior review, approval and current proof selection; historical events/proof/archives remain retained. A stale open revision is rejected so staff must refresh and review the saved content. Missing review, approval or actual proof blocks the corresponding step. Back up/restore the matching complete new-format profile through System Health; installed restart/recovery acceptance remains required for this candidate.

This replaces the disconnected standalone Public Notices controls. The separate Meetings notice/template/proof workflow remains available for meeting-specific records; it does not silently approve a different Notice draft. Staff remain responsible for legal sufficiency, official publication and the official record. No subscriber message or official notice is sent automatically.

## Standalone package boundary

The standalone FastAPI routes below remain registry/deadline/proof workpapers and deterministic planning helpers. The Windows authenticated lifecycle above is provided by the suite runtime using Notice's durable workflow store; it is not a claim that every standalone helper performs an archive or Records transfer. Fixed rule packs are review aids and are not administered jurisdiction/effective-date legal rules. Subscriber/channel/accessibility/export helpers retain their documented planning boundaries.


Townlight Notice is the Townlight module for public hearing notices, legal notices, bid notices, vacancy notices, statutory publication deadlines, statutory rule checks, notice drafting templates, accessibility and language-readiness review, publication-readiness review, channel planning, subscriber delivery planning, archive/handoff packets, and notice-record export checklists.

Release state: the latest **published GitHub release is `v0.1.1`**. The current in-tree source is **`v0.3.0`**, the notice-compliance foundation aligned to the `townlight-core 1.3.0.dev2` release wheel; `v0.3.0` is **bundled source, not yet published as a GitHub release** (it ships only through the Windows Local city-core profile's commit-pinned bundle). This repo provides a FastAPI package, health/root endpoints, documentation gates, deterministic sample notice registry, Townlight Core-backed statutory deadline plans, deterministic statutory rule checks, notice drafting templates, accessibility and language-readiness review packets, optional database-backed registry/deadline/publication-proof workpapers, publication-readiness checklists, channel-planning helpers, subscriber delivery planning, archive/handoff packets, notice/records export checklist, and accessible public sample UI at `/townlight_notice`. It does **not** ship legal sufficiency decisions, legal advice, live LLM calls, official notice publication, publication-system write-back, or notice system-of-record integrations.

<a id="what-townlight_notice-does"></a>

## What Townlight Notice Does

- Create sample notice registry stubs.
- Build statutory publication deadline reminder plans using the shared Townlight Core notice helper.
- Check notice packets against deterministic staff-review rule packs for common notice types.
- Build staff-editable notice templates with required fields and unresolved placeholders.
- Build accessibility, plain-language, and human-approved translation readiness packets.
- Persist notice registry, deadline-plan, and publication-proof workpapers when `TOWNLIGHT_NOTICE_WORKPAPER_DB_URL` is configured.
- Store staff-reviewed publication proof packets linked to upstream Clerk, procurement, board, or manual source records.
- Assemble publication-readiness checklists for staff review.
- Plan notice channels and accessibility-review needs.
- Build subscriber delivery plans without sending notices or storing subscriber PII.
- Assemble archive/handoff packets for Clerk, Procure, Boards, Records, and manual staff files.
- Produce notice and records export checklists.
- Demonstrate a public notice-support UI at `/townlight_notice`.

<a id="what-townlight_notice-does-not-do"></a>

## What Townlight Notice Does Not Do

- It does not decide legal sufficiency.
- It does not publish official notices.
- It does not provide legal advice.
- It does not call live LLMs in v0.3.0.
- It does not write back to publication systems.
- It does not replace a notice system of record.

## API Surface

- `GET /` returns the shipped/planned boundary.
- `GET /health` returns package and Townlight Core versions.
- `GET /townlight_notice` returns the accessible public sample UI.
- `GET /docs` opens the interactive FastAPI API documentation for local deployments.
- `GET /openapi.json` returns the machine-readable API schema, including accepted request and error shapes.
- `POST /api/v1/townlight_notice/registry` returns a sample notice registry stub.
- `GET /api/v1/townlight_notice/registry/{record_id}` retrieves a persisted notice registry record.
- `POST /api/v1/townlight_notice/deadlines` returns statutory deadline reminders.
- `GET /api/v1/townlight_notice/deadlines/{plan_id}` retrieves a persisted deadline plan.
- `POST /api/v1/townlight_notice/rule-check` checks a notice packet against deterministic staff-review rules.
- `POST /api/v1/townlight_notice/templates` returns a staff-editable notice template.
- `POST /api/v1/townlight_notice/publication-proof` stores a durable publication proof workpaper.
- `GET /api/v1/townlight_notice/publication-proof/{proof_id}` retrieves a persisted publication proof workpaper.
- `POST /api/v1/townlight_notice/publication-check` returns a publication-readiness checklist.
- `POST /api/v1/townlight_notice/accessibility-review` returns accessibility and language-readiness flags.
- `POST /api/v1/townlight_notice/channels` returns channel planning flags.
- `POST /api/v1/townlight_notice/subscribers/plan` returns a subscriber delivery plan.
- `POST /api/v1/townlight_notice/archive-packet` returns archive and handoff readiness for a notice file.
- `POST /api/v1/townlight_notice/export` returns a notice and records export checklist.

<a id="start-and-smoke-check-townlight_notice"></a>

## Start and Smoke-Check Townlight Notice

Install the package with its development dependencies, start the ASGI app target `townlight_notice.main:app`, and open the local `/health` and `/townlight_notice` routes. A fresh user can reach the core stateless API and public sample UI without a database, model server, account, or API key.

Minimal workflow to smoke-check after startup:

1. Confirm `/health` reports `service: townlight_notice`, version `0.3.0`, and Townlight Core `1.2.0`.
2. Post a registry stub to `/api/v1/townlight_notice/registry` without a database and confirm the response includes `record_id: null`, registry notes, and the staff-responsibility disclaimer.
3. Open `/docs` or `/openapi.json` to inspect accepted fields, then post a rule check to `/api/v1/townlight_notice/rule-check` with a supported notice type, event date, publication dates, channels, content fields, and statutory basis. Unsupported notice types return a 422 response with supported choices.
4. Open `/townlight_notice` and confirm the page is a static public sample with boundary copy, not an official publication workflow.

## Persistence and Durable Writes

Without `TOWNLIGHT_NOTICE_WORKPAPER_DB_URL`, Townlight Notice runs in deterministic stateless mode: registry and deadline POST requests return transient payloads, persisted GET routes return actionable 503 responses, and publication-proof storage is unavailable.

With `TOWNLIGHT_NOTICE_WORKPAPER_DB_URL`, registry, deadline, and publication-proof workpapers are durable. Persistence-backed write routes also require `TOWNLIGHT_NOTICE_TRUSTED_WRITE_TOKEN` and the matching `X-Townlight-Notice-Write-Token` request header. This is a minimal trusted-mode guard for local deployments; it is not a replacement for a production identity system.

## Local Development

```bash
python -m pip install build
# Use a clean Core checkout matching config/core-source.json before publication.
python scripts/install-core-candidate.py --core-source ../core
python -m pip install -e ".[dev]"
python -m pytest -q
bash scripts/verify-release.sh
```

The release gate requires `TOWNLIGHT_NOTICE_POSTGRES_TEST_URL` so PostgreSQL persistence coverage cannot be skipped. Use a disposable test database: persistence tests reset its Notice schema. The bootstrap verifies the clean Core commit and saves `.qa/core-candidate.json`; the gate checks that receipt against the pin and the installed wheel's artifact hash. Once the pinned commit is publicly available, omitting `--core-source` fetches that exact commit. Plain unit tests may still run without PostgreSQL for local development.

## Prepared package installation

The renamed distributions are not yet published on a package index. Use the
matching verified candidate wheel directory, not a renamed historical release
URL. Installation of these Python packages is a developer/package check;
the signed Windows MSI and its installed acceptance remain separate.

In a new Windows virtual environment, replace the example wheel-directory path
with the directory accompanying this candidate and verify its SHA256 manifest:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
$candidateWheels = (Resolve-Path 'C:\path\to\candidate-wheels').Path
python -m pip install (Join-Path $candidateWheels 'townlight_core-1.3.0.dev2-py3-none-any.whl')
python -m pip install (Join-Path $candidateWheels 'townlight_notice-0.3.0-py3-none-any.whl')
python -c "import townlight_notice; from importlib.metadata import version; print(version('townlight-notice'))"
```

Expected principal import: `townlight_notice`; expected distribution version:
`0.3.0`. Use a fresh empty database/profile for workflow testing. Existing
city data and the previous release remain untouched; no in-place upgrade or
old-import compatibility shim is supplied.

## License

Code: AGPL-3.0-only. See [LICENSE](LICENSE); historical grants are retained under docs/licensing/history.
Documentation: CC BY 4.0 ([LICENSE-DOCS](LICENSE-DOCS)).

Current owned candidate code: AGPL-3.0-only, without additional permissions. Historical grants retained under docs/licensing/history.

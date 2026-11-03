from datetime import date, timedelta
import hashlib
import io
import json
import zipfile

import pytest
from sqlalchemy import create_engine

from townlight_notice.workflow import NoticeDraft, NoticeWorkflow, Conflict
from townlight_notice.statutory_rules import RULE_PACKS, check_statutory_notice_requirements


@pytest.fixture
def workflow(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'notices.db'}")
    store = NoticeWorkflow(engine)
    yield store
    store.engine.dispose()


def draft(body="The hearing is Friday at City Hall."):
    return NoticeDraft(title="Hearing", body=body, notice_type="public hearing",
                       statutory_basis="Staff-reviewed authority", event_date=date(2026, 12, 1),
                       lead_days=10)


def test_real_proof_and_archive_survive_reconnect(workflow):
    saved = workflow.create(draft(), "clerk-a")
    saved = workflow.review(saved["notice_id"], saved["sequence"], "clerk-b", "Checked date and authority")
    saved = workflow.approve(saved["notice_id"], saved["sequence"], "clerk-b")
    proof = b"Actual synthetic posting receipt bytes\n"
    saved = workflow.proof(saved["notice_id"], saved["sequence"], "clerk-a", filename="receipt.txt",
                           content=proof, location="City Hall board", published_at="2026-11-02T12:00:00-07:00")
    archived = workflow.archive(saved["notice_id"], saved["sequence"], "clerk-a")
    reopened = NoticeWorkflow(workflow.engine)
    artifact = reopened.get_archive(archived["archive_id"])
    assert hashlib.sha256(artifact["content"]).hexdigest() == artifact["sha256"]
    with zipfile.ZipFile(io.BytesIO(artifact["content"])) as bundle:
        record = json.loads(bundle.read("notice.json"))
        assert record["notice"]["state"] == "archived"
        assert record["notice"]["archive_id"] == archived["archive_id"]
        assert record["notice"]["document"]["body"] == draft().body
        manifest = json.loads(bundle.read("manifest.json"))
        for item in manifest["files"]:
            assert hashlib.sha256(bundle.read(item["path"])).hexdigest() == item["sha256"]
        assert proof in [bundle.read(name) for name in bundle.namelist()]
        assert {event["actor"] for event in record["history"]} == {"clerk-a", "clerk-b"}
    assert reopened.get(saved["notice_id"])["state"] == "archived"


def test_revision_invalidates_review_and_approval_and_stale_write_fails(workflow):
    initial = workflow.create(draft(), "clerk")
    reviewed = workflow.review(initial["notice_id"], 1, "reviewer", "Reviewed")
    approved = workflow.approve(initial["notice_id"], reviewed["sequence"], "reviewer")
    revised = workflow.edit(initial["notice_id"], approved["sequence"], draft("Changed Friday to Monday."), "clerk")
    assert revised["state"] == "draft" and revised["approval"] is None
    with pytest.raises(Conflict):
        workflow.edit(initial["notice_id"], 1, draft(), "clerk")
    with pytest.raises(ValueError):
        workflow.approve(initial["notice_id"], revised["sequence"], "reviewer")
    with pytest.raises(ValueError):
        workflow.proof(initial["notice_id"], revised["sequence"], "clerk", filename="receipt.txt",
                       content=b"proof", location="Board", published_at="2026-11-02T12:00:00-07:00")
    assert len(workflow.history(initial["notice_id"])) == 4


def test_missing_proof_blocks_archive_and_invalid_proof_is_not_saved(workflow):
    saved = workflow.create(draft(), "clerk")
    saved = workflow.review(saved["notice_id"], 1, "reviewer", "Reviewed")
    saved = workflow.approve(saved["notice_id"], saved["sequence"], "reviewer")
    with pytest.raises(ValueError):
        workflow.archive(saved["notice_id"], saved["sequence"], "clerk")
    for filename, content, timestamp in [("../outside.txt", b"x", "2026-11-02"),
                                         ("proof.txt", b"", "2026-11-02"),
                                         ("proof.txt", b"x", "not a date")]:
        with pytest.raises(ValueError):
            workflow.proof(saved["notice_id"], saved["sequence"], "clerk", filename=filename,
                           content=content, location="Board", published_at=timestamp)
    assert len(workflow.history(saved["notice_id"])) == 3


def test_mechanical_rule_success_never_waives_human_review():
    rule = RULE_PACKS["planning hearing"]
    event = date(2026, 12, 1)
    result = check_statutory_notice_requirements(notice_type="planning hearing", event_date=event,
        publication_dates=(event-timedelta(days=rule.minimum_lead_days),), channels=rule.required_channels,
        content_fields=rule.required_content, statutory_basis="Unverified arbitrary text")
    assert result.staff_review_required is True

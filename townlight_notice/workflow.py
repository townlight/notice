"""Staff-owned notice revisions, approval, retained proof and exact-byte archives.

No official publication, legal determination, model call or outbound delivery.
All mutations require the sequence the clerk actually reviewed.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import PureWindowsPath
from uuid import uuid4
import zipfile

from pydantic import BaseModel, ConfigDict, Field
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from townlight_notice.notice_registry import DISCLAIMER
from townlight_notice.deadline_tracker import build_deadline_plan


def deadline_workpaper(document):
    plan = build_deadline_plan(notice_type=document.notice_type,
        event_date=document.event_date, lead_days=document.lead_days)
    return {"reminders": list(plan.reminders), "staff_review_required": True,
            "basis": "Staff-selected calendar-day interval; verify applicable law and publication timing."}


class NoticeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=100000)
    notice_type: str = Field(min_length=1, max_length=160)
    statutory_basis: str = Field(min_length=1, max_length=5000)
    event_date: date
    lead_days: int = Field(ge=0, le=365)


class Conflict(ValueError):
    """The record changed since it was read; refresh before another mutation."""


metadata = sa.MetaData(schema="townlight_notice")
heads = sa.Table("workflow_heads", metadata,
    sa.Column("notice_id", sa.String(36), primary_key=True),
    sa.Column("sequence", sa.Integer, nullable=False))
events = sa.Table("workflow_events", metadata,
    sa.Column("notice_id", sa.String(36), primary_key=True),
    sa.Column("sequence", sa.Integer, primary_key=True),
    sa.Column("action", sa.String(40), nullable=False),
    sa.Column("actor", sa.String(160), nullable=False),
    sa.Column("created_at", sa.String(40), nullable=False),
    sa.Column("snapshot", sa.JSON, nullable=False))
proofs = sa.Table("workflow_proofs", metadata,
    sa.Column("proof_id", sa.String(36), primary_key=True),
    sa.Column("notice_id", sa.String(36), nullable=False),
    sa.Column("sha256", sa.String(64), nullable=False),
    sa.Column("content", sa.LargeBinary, nullable=False))
archives = sa.Table("workflow_archives", metadata,
    sa.Column("archive_id", sa.String(36), primary_key=True),
    sa.Column("notice_id", sa.String(36), nullable=False),
    sa.Column("sequence", sa.Integer, nullable=False),
    sa.Column("sha256", sa.String(64), nullable=False),
    sa.Column("content", sa.LargeBinary, nullable=False))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")


def sha(content):
    return hashlib.sha256(content).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def actor_name(actor):
    if not isinstance(actor, str) or not actor.strip() or len(actor) > 160:
        raise ValueError("A mapped staff identity is required.")
    return actor.strip()


class NoticeWorkflow:
    def __init__(self, engine, *, initialize=True):
        self.engine = engine.execution_options(schema_translate_map={"townlight_notice": None}) if engine.dialect.name == "sqlite" else engine
        if initialize:
            if self.engine.dialect.name == "postgresql":
                with self.engine.begin() as connection:
                    connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS townlight_notice"))
            metadata.create_all(self.engine)

    def create(self, document: NoticeDraft, actor: str):
        actor = actor_name(actor)
        notice_id = str(uuid4())
        snapshot = {"notice_id": notice_id, "sequence": 1, "state": "draft",
            "document": document.model_dump(mode="json"), "deadline_workpaper": deadline_workpaper(document), "review": None, "approval": None,
            "proofs": [], "archive_id": None, "disclaimer": DISCLAIMER}
        with self.engine.begin() as connection:
            connection.execute(heads.insert().values(notice_id=notice_id, sequence=1))
            self._event(connection, snapshot, "create", actor)
        return snapshot

    @staticmethod
    def _event(connection, snapshot, action, actor):
        connection.execute(events.insert().values(notice_id=snapshot["notice_id"],
            sequence=snapshot["sequence"], action=action, actor=actor_name(actor),
            created_at=now(), snapshot=snapshot))

    def _change(self, notice_id, expected_sequence, actor, action, change):
        actor = actor_name(actor)
        if not isinstance(expected_sequence, int) or isinstance(expected_sequence, bool):
            raise ValueError("Supply the current sequence number.")
        try:
            with self.engine.begin() as connection:
                head = connection.execute(sa.select(heads).where(
                    heads.c.notice_id == notice_id).with_for_update()).mappings().first()
                if head is None:
                    raise LookupError("Notice not found.")
                if head["sequence"] != expected_sequence:
                    raise Conflict("Notice changed. Refresh and review the saved version before retrying.")
                row = connection.execute(sa.select(events.c.snapshot).where(
                    events.c.notice_id == notice_id, events.c.sequence == expected_sequence)).scalar_one()
                snapshot = json.loads(json.dumps(row))
                snapshot["sequence"] += 1
                change(snapshot, connection)
                updated = connection.execute(heads.update().where(heads.c.notice_id == notice_id,
                    heads.c.sequence == expected_sequence).values(sequence=snapshot["sequence"]))
                if updated.rowcount != 1:
                    raise Conflict("Notice changed; no action was saved.")
                self._event(connection, snapshot, action, actor)
            return snapshot
        except IntegrityError as error:
            raise Conflict("Notice changed; refresh before retrying.") from error

    def get(self, notice_id):
        with self.engine.connect() as connection:
            row = connection.execute(sa.select(events.c.snapshot).where(
                events.c.notice_id == notice_id).order_by(events.c.sequence.desc()).limit(1)).scalar_one_or_none()
        if row is None:
            raise LookupError("Notice not found.")
        return row

    def inventory(self):
        with self.engine.connect() as connection:
            return list(connection.execute(sa.select(events.c.snapshot).join(heads,
                sa.and_(events.c.notice_id == heads.c.notice_id, events.c.sequence == heads.c.sequence))
                .order_by(events.c.notice_id)).scalars())

    def history(self, notice_id):
        with self.engine.connect() as connection:
            rows = connection.execute(sa.select(events).where(events.c.notice_id == notice_id)
                                      .order_by(events.c.sequence)).mappings().all()
        return [dict(row) for row in rows]

    def edit(self, notice_id, sequence, document: NoticeDraft, actor):
        def change(snapshot, _):
            snapshot.update(document=document.model_dump(mode="json"), deadline_workpaper=deadline_workpaper(document), state="draft", review=None,
                            approval=None, proofs=[], archive_id=None)
        return self._change(notice_id, sequence, actor, "edit", change)

    def review(self, notice_id, sequence, actor, note):
        if not note.strip() or len(note) > 5000:
            raise ValueError("Record what the staff reviewer checked (up to 5000 characters).")
        def change(snapshot, _):
            if snapshot["state"] not in {"draft", "reviewed"}:
                raise ValueError("Edit the notice before a new review.")
            snapshot.update(state="reviewed", review={"actor": actor_name(actor), "at": now(),
                "note": note.strip(), "document_sha256": sha(canonical(snapshot["document"]))})
        return self._change(notice_id, sequence, actor, "review", change)

    def approve(self, notice_id, sequence, actor):
        def change(snapshot, _):
            digest = sha(canonical(snapshot["document"]))
            if snapshot["state"] != "reviewed" or snapshot["review"]["document_sha256"] != digest:
                raise ValueError("Review the current notice before staff approval.")
            snapshot.update(state="approved", approval={"actor": actor_name(actor), "at": now(),
                "document_sha256": digest, "legal_sufficiency_automated": False})
        return self._change(notice_id, sequence, actor, "approve", change)

    def proof(self, notice_id, sequence, actor, *, filename, content, location, published_at):
        if (not filename or len(filename) > 150 or PureWindowsPath(filename).name != filename
                or any(character in filename for character in '/\\:<>"|?*')
                or any(ord(character) < 32 for character in filename)
                or filename.endswith((' ', '.')) or PureWindowsPath(filename).is_reserved()
                or filename in {'.', '..'}):
            raise ValueError("Supply a plain evidence filename without a path.")
        if not isinstance(content, bytes) or not content or len(content) > 5_000_000:
            raise ValueError("Supply actual posting-proof bytes (at most 5 MB per file).")
        timestamp = datetime.fromisoformat(published_at)
        if timestamp.tzinfo is None:
            raise ValueError("Posting timestamp must include its time zone.")
        if not location.strip() or len(location) > 2000:
            raise ValueError("Record the actual posting location.")
        proof_id, digest = str(uuid4()), sha(content)
        def change(snapshot, connection):
            if snapshot["state"] not in {"approved", "proof-recorded"}:
                raise ValueError("Approve the current draft before recording publication proof.")
            if sum(item["size_bytes"] for item in snapshot["proofs"]) + len(content) > 10_000_000:
                raise ValueError("Posting proof exceeds the supported 10 MB archive evidence limit.")
            connection.execute(proofs.insert().values(proof_id=proof_id, notice_id=notice_id,
                                                       sha256=digest, content=content))
            snapshot["proofs"].append({"proof_id": proof_id, "filename": filename, "sha256": digest,
                "size_bytes": len(content), "location": location.strip(), "published_at": published_at,
                "recorded_by": actor_name(actor), "recorded_at": now(),
                "approved_document_sha256": snapshot["approval"]["document_sha256"]})
            snapshot["state"] = "proof-recorded"
        return self._change(notice_id, sequence, actor, "record-proof", change)

    def archive(self, notice_id, sequence, actor):
        archive_id = str(uuid4())
        def change(snapshot, connection):
            if snapshot["state"] != "proof-recorded" or not snapshot["approval"] or not snapshot["proofs"]:
                raise ValueError("Staff approval and actual posting proof are required before archiving.")
            history = [dict(row) for row in connection.execute(sa.select(events).where(
                events.c.notice_id == notice_id).order_by(events.c.sequence)).mappings()]
            snapshot.update(state="archived", archive_id=archive_id)
            files = {"notice.json": canonical({"notice": snapshot, "history": history,
                "archived_by": actor_name(actor), "archived_at": now()})}
            for item in snapshot["proofs"]:
                row = connection.execute(sa.select(proofs).where(proofs.c.proof_id == item["proof_id"],
                    proofs.c.notice_id == notice_id)).mappings().one()
                if sha(row["content"]) != item["sha256"] or row["sha256"] != item["sha256"]:
                    raise ValueError("Stored proof integrity failed; no archive was created.")
                files[f"proof/{item['proof_id']}/{item['filename']}"] = row["content"]
            manifest = {"schema_version": 1, "notice_id": notice_id, "archive_id": archive_id,
                "files": [{"path": name, "sha256": sha(content), "size_bytes": len(content)}
                          for name, content in files.items()]}
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for name, content in files.items():
                    entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    bundle.writestr(entry, content)
                entry = zipfile.ZipInfo("manifest.json", date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(entry, canonical(manifest))
            content = output.getvalue()
            connection.execute(archives.insert().values(archive_id=archive_id, notice_id=notice_id,
                sequence=snapshot["sequence"], sha256=sha(content), content=content))
        return self._change(notice_id, sequence, actor, "archive", change)

    def get_archive(self, archive_id):
        with self.engine.connect() as connection:
            row = connection.execute(sa.select(archives).where(
                archives.c.archive_id == archive_id)).mappings().first()
        if row is None:
            raise LookupError("Notice archive not found.")
        if sha(row["content"]) != row["sha256"]:
            raise ValueError("Archive integrity failed; do not use this artifact.")
        return dict(row)

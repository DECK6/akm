"""AKM-native local memory runtime.

Durable runtime records and forget fences are Markdown files.  The JSON state
file is deliberately disposable and is rebuilt from those Markdown artifacts.
Nothing in this module writes into AKM's canonical 20/30/40/50 layers.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import secrets
import stat
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


UTC = timezone.utc
RECORD_MARKER = "<!-- akm-memory-record:v1 -->"
FENCE_MARKER = "<!-- akm-memory-forget-fence:v1 -->"
JSON_BLOCK = re.compile(r"```json\s*\n(?P<payload>.*?)\n```", re.DOTALL)
STATES = {"candidate", "active", "superseded", "expired", "forgotten", "rejected"}
EXTRACTION_OUTCOMES = {
    "success",
    "nothing_salient",
    "provider_error",
    "refusal",
    "content_filter",
    "malformed_output",
    "truncated_output",
}
VISIBILITIES = {"public", "non_sensitive", "private", "restricted"}
KINDS = {"fact", "event", "preference", "safety", "commitment", "belief", "procedure"}
STABLE_AUTHORITY_KINDS = {"preference", "safety"}
SAFE_SUMMARY_LIMIT = 240
DELTA_CURSOR_MAX_CHARS = 262_144
DELTA_CURSOR_MAX_SEEN = 10_000
RECORD_FIELDS = {
    "schema_version",
    "id",
    "state",
    "revision",
    "text",
    "safe_summary",
    "kind",
    "entity",
    "scope",
    "visibility",
    "egress_allowed",
    "stable_authority",
    "source",
    "created_at",
    "modified_at",
    "expires_at",
    "supersedes",
    "superseded_by",
    "decision_evidence",
    "history",
}
SCOPE_FIELDS = {"source_id", "project", "profile", "user"}
SOURCE_FIELDS = {"path", "lineage"}
HISTORY_FIELDS = {"change", "at", "evidence", "detail", "related_record_id"}
HISTORY_CHANGES = {"created", "modified", "superseded", "expired", "forgotten"}


class MemoryRuntimeError(RuntimeError):
    """Base class for runtime failures safe to expose to an operator."""


class ValidationError(MemoryRuntimeError):
    """Input or durable artifact failed a fail-closed validation."""


class MemoryNotFound(MemoryRuntimeError):
    """Record is missing or inaccessible; deliberately does not distinguish."""


class ConfirmationRequired(MemoryRuntimeError):
    """Destructive operation lacks a current exact-impact confirmation token."""


class MemoryWriteError(MemoryRuntimeError):
    """Canonical/derived write did not reconcile to a completed receipt."""

    def __init__(self, message: str, receipt_id: str) -> None:
        super().__init__(message)
        self.receipt_id = receipt_id


@dataclass(frozen=True)
class Scope:
    source_id: str
    project: str | None = None
    profile: str | None = None
    user: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValidationError("scope source_id is required")
        for name in ("project", "profile", "user"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValidationError(f"scope {name} must be a non-empty string when supplied")

    def as_dict(self) -> dict[str, str | None]:
        return {
            "source_id": self.source_id,
            "project": self.project,
            "profile": self.profile,
            "user": self.user,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Scope":
        if not isinstance(value, Mapping) or set(value) != SCOPE_FIELDS:
            raise ValidationError("scope must contain exactly source_id/project/profile/user")
        return cls(
            source_id=str(value.get("source_id") or ""),
            project=value.get("project"),
            profile=value.get("profile"),
            user=value.get("user"),
        )


@dataclass(frozen=True)
class ExtractionOutcome:
    outcome: str
    candidates: list[dict[str, Any]]
    detail: str | None = None


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    records: Path
    fences: Path
    derived: Path
    derived_state: Path
    receipts: Path
    previews: Path
    promotion_queue: Path
    cursors: Path
    audit: Path
    usage_audit: Path


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValidationError("timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"invalid timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ValidationError("timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_summary(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= SAFE_SUMMARY_LIMIT:
        return compact
    return compact[: SAFE_SUMMARY_LIMIT - 1].rstrip() + "…"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:80] or "memory"


def _scope_matches(record_scope: Mapping[str, Any], request: Scope) -> bool:
    if not record_scope.get("source_id"):
        return False
    supplied = request.as_dict()
    for field in ("source_id", "project", "profile", "user"):
        expected = record_scope.get(field)
        if expected is not None and supplied.get(field) != expected:
            return False
    return True


def _egress_allowed(record: Mapping[str, Any], external_model: bool) -> bool:
    if not external_model:
        return True
    if record.get("visibility") in {"private", "restricted"}:
        return False
    return bool(record.get("egress_allowed"))


def _delta_event_id(source: str, ordinal: int, event: Mapping[str, Any]) -> str:
    material = {
        "source": source,
        "ordinal": ordinal,
        "record_id": event["record_id"],
        "change": event["change"],
        "at": event["at"],
    }
    return _sha256_bytes(_canonical_json(material).encode("utf-8"))


def _encode_delta_cursor(at: datetime, seen: Iterable[str]) -> str:
    payload = _canonical_json({"at": _iso(at), "seen": sorted(set(seen))}).encode("utf-8")
    return "d1." + base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_delta_cursor(value: str | None) -> tuple[datetime | None, set[str], bool]:
    if value is None:
        return None, set(), False
    if len(value) > DELTA_CURSOR_MAX_CHARS:
        raise ValidationError("delta cursor is too large")
    if not value.startswith("d1."):
        return _parse_time(value), set(), False
    encoded = value[3:]
    if not encoded or not re.fullmatch(r"[A-Za-z0-9_-]+", encoded):
        raise ValidationError("invalid delta cursor")
    try:
        padding = "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(encoded + padding).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("invalid delta cursor") from exc
    if not isinstance(payload, dict) or set(payload) != {"at", "seen"}:
        raise ValidationError("invalid delta cursor")
    if (
        not isinstance(payload["seen"], list)
        or len(payload["seen"]) > DELTA_CURSOR_MAX_SEEN
        or any(
        not isinstance(item, str) or not re.fullmatch(r"[0-9a-f]{64}", item)
        for item in payload["seen"]
        )
    ):
        raise ValidationError("invalid delta cursor")
    return _parse_time(payload["at"]), set(payload["seen"]), True


class MemoryRuntime:
    """Local, scoped memory runtime whose derived index is rebuildable."""

    def __init__(
        self,
        root: str | Path,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        root_path = Path(root).expanduser().resolve()
        self._reject_akm_canonical_root(root_path)
        self._now = now or _utc_now
        self.paths = RuntimePaths(
            root=root_path,
            records=root_path / "records",
            fences=root_path / "fences",
            derived=root_path / "derived",
            derived_state=root_path / "derived" / "state.json",
            receipts=root_path / "receipts",
            previews=root_path / "previews",
            promotion_queue=root_path / "promotion-queue",
            cursors=root_path / "cursors",
            audit=root_path / "audit",
            usage_audit=root_path / "audit" / "usage.jsonl",
        )
        for directory in (
            self.paths.records,
            self.paths.fences,
            self.paths.derived,
            self.paths.receipts,
            self.paths.previews,
            self.paths.promotion_queue,
            self.paths.cursors,
            self.paths.audit,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        root_fd = os.open(self.paths.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            root_stat = os.fstat(root_fd)
            self._root_identity = (root_stat.st_dev, root_stat.st_ino)
        finally:
            os.close(root_fd)

    @staticmethod
    def _reject_akm_canonical_root(root_path: Path) -> None:
        """Do not let local runtime state become an AKM canonical subtree."""
        for ancestor in (root_path, *root_path.parents):
            if (ancestor / "99-system" / "SCHEMA.md").is_file() and (
                ancestor / "99-system" / "ROUTER.md"
            ).is_file():
                raise ValidationError("runtime root must be outside the AKM canonical vault")

    def record_path(self, record_id: str) -> Path:
        self._validate_id(record_id)
        return self.paths.records / f"{record_id}.md"

    def remember(
        self,
        text: str,
        *,
        scope: Scope,
        entity: str,
        kind: str = "fact",
        visibility: str = "non_sensitive",
        egress_allowed: bool = False,
        ttl_seconds: int | None = None,
        stable_authority: bool = False,
        source_path: str,
        source_lineage: Sequence[str],
        extraction_evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = self._required_text(text, "text")
        entity = self._required_text(entity, "entity")
        source_path = self._required_text(source_path, "source_path")
        if kind not in KINDS:
            raise ValidationError(f"unsupported memory kind: {kind}")
        if visibility not in VISIBILITIES:
            raise ValidationError(f"unsupported visibility: {visibility}")
        if not isinstance(source_lineage, Sequence) or isinstance(source_lineage, (str, bytes)):
            raise ValidationError("source_lineage must be a list of non-empty strings")
        lineage = [self._required_text(str(item), "source_lineage item") for item in source_lineage]
        if not lineage:
            raise ValidationError("source_lineage must not be empty")
        if ttl_seconds is not None and (not isinstance(ttl_seconds, int) or ttl_seconds <= 0):
            raise ValidationError("ttl_seconds must be a positive integer")
        if stable_authority and kind not in STABLE_AUTHORITY_KINDS:
            raise ValidationError("stable authority is limited to preference and safety records")
        if stable_authority and ttl_seconds is not None:
            raise ValidationError("stable authority preference/safety records may not have TTL")

        now = self._now()
        identity_payload = {
            "text": text,
            "entity": entity,
            "kind": kind,
            "scope": scope.as_dict(),
            "source_path": source_path,
        }
        record_id = "mem_" + hashlib.sha256(_canonical_json(identity_payload).encode()).hexdigest()[:24]
        path = self.record_path(record_id)
        if path.exists():
            record = self._read_markdown_json(path, RECORD_MARKER)
            if not _scope_matches(record.get("scope", {}), scope):
                raise MemoryNotFound("memory not found")
            receipt = self._completed_noop_receipt("remember-duplicate", record, path)
            return {"record": record, "receipt": receipt, "duplicate": True}

        expires_at = _iso(now + timedelta(seconds=ttl_seconds)) if ttl_seconds else None
        record: dict[str, Any] = {
            "schema_version": "1.0.0",
            "id": record_id,
            "state": "candidate",
            "revision": 1,
            "text": text,
            "safe_summary": _safe_summary(text),
            "kind": kind,
            "entity": entity,
            "scope": scope.as_dict(),
            "visibility": visibility,
            "egress_allowed": bool(egress_allowed),
            "stable_authority": bool(stable_authority),
            "source": {"path": source_path, "lineage": lineage},
            "created_at": _iso(now),
            "modified_at": _iso(now),
            "expires_at": expires_at,
            "supersedes": None,
            "superseded_by": None,
            "decision_evidence": dict(extraction_evidence) if extraction_evidence else None,
            "history": [
                {
                    "change": "created",
                    "at": _iso(now),
                    "evidence": "explicit-remember",
                }
            ],
        }
        receipt_id = self._receipt_id("remember", record_id)
        receipt = self._new_receipt(receipt_id, "remember", [record_id])
        self._write_receipt(receipt)
        try:
            checksum = self._write_record(record)
            receipt.update(
                canonical_status="written",
                canonical_checksum=checksum,
                revision=record["revision"],
            )
            self._write_receipt(receipt)
        except Exception as exc:
            receipt.update(canonical_status="failed", failure=str(exc), reconcile_status="manual")
            self._write_receipt(receipt)
            raise MemoryWriteError("canonical Markdown write failed", receipt_id) from exc
        self._finish_derived_write(receipt, receipt_id)
        return {"record": record, "receipt": receipt, "duplicate": False}

    def approve(
        self,
        record_id: str,
        *,
        scope: Scope,
        decision_evidence: str,
    ) -> dict[str, Any]:
        decision_evidence = self._required_text(decision_evidence, "decision_evidence")
        target = self.get(record_id, scope=scope, include_inactive=True)
        if target["state"] != "candidate":
            raise ValidationError("only candidate records can be explicitly approved")
        now = self._now()
        effective = self._build_state()["records"]
        old_records: list[dict[str, Any]] = []
        for row in effective.values():
            if (
                row["id"] != record_id
                and row.get("state") == "active"
                and row.get("kind") == target.get("kind")
                and row.get("entity") == target.get("entity")
                and row.get("scope") == target.get("scope")
            ):
                original = self._read_record(row["id"])
                original["state"] = "superseded"
                original["superseded_by"] = record_id
                original["modified_at"] = _iso(now)
                original["revision"] += 1
                original["history"].append(
                    {
                        "change": "superseded",
                        "at": _iso(now),
                        "evidence": decision_evidence,
                        "related_record_id": record_id,
                    }
                )
                old_records.append(original)

        target = self._read_record(record_id)
        target["state"] = "active"
        target["modified_at"] = _iso(now)
        target["revision"] += 1
        target["decision_evidence"] = {"approval": decision_evidence}
        if old_records:
            target["supersedes"] = old_records[-1]["id"]
        target["history"].append(
            {
                "change": "modified",
                "at": _iso(now),
                "evidence": decision_evidence,
                "detail": "candidate-approved",
            }
        )
        receipt_id = self._receipt_id("approve", record_id)
        receipt = self._new_receipt(receipt_id, "approve", [row["id"] for row in old_records] + [record_id])
        self._write_receipt(receipt)
        try:
            checksums = {row["id"]: self._write_record(row) for row in old_records}
            checksums[record_id] = self._write_record(target)
            receipt.update(
                canonical_status="written",
                canonical_checksum=checksums,
                revision=target["revision"],
            )
            self._write_receipt(receipt)
        except Exception as exc:
            receipt.update(canonical_status="failed", failure=str(exc), reconcile_status="manual")
            self._write_receipt(receipt)
            raise MemoryWriteError("approval Markdown write failed", receipt_id) from exc
        self._finish_derived_write(receipt, receipt_id)
        return {"record": target, "superseded": [row["id"] for row in old_records], "receipt": receipt}

    def reject(
        self,
        record_id: str,
        *,
        scope: Scope,
        decision_evidence: str,
    ) -> dict[str, Any]:
        target = self.get(record_id, scope=scope, include_inactive=True)
        if target["state"] != "candidate":
            raise ValidationError("only candidate records can be rejected")
        target = self._read_record(record_id)
        now = self._now()
        target["state"] = "rejected"
        target["revision"] += 1
        target["modified_at"] = _iso(now)
        target["decision_evidence"] = {"rejection": self._required_text(decision_evidence, "decision_evidence")}
        target["history"].append(
            {"change": "modified", "at": _iso(now), "evidence": decision_evidence, "detail": "rejected"}
        )
        return self._write_mutation("reject", target)

    def get(
        self,
        record_id: str,
        *,
        scope: Scope,
        include_inactive: bool = False,
        external_model: bool = False,
    ) -> dict[str, Any]:
        self._validate_id(record_id)
        record = self._build_state()["records"].get(record_id)
        if not record or not _scope_matches(record.get("scope", {}), scope):
            raise MemoryNotFound("memory not found")
        if not _egress_allowed(record, external_model):
            raise MemoryNotFound("memory not found")
        if external_model and record.get("state") != "active":
            raise MemoryNotFound("memory not found")
        if not include_inactive and record.get("state") != "active":
            raise MemoryNotFound("memory not found")
        return json.loads(json.dumps(record))

    def recall(
        self,
        *,
        scope: Scope,
        query: str | None = None,
        record_id: str | None = None,
        include_states: Iterable[str] = ("active",),
        external_model: bool = False,
        max_count: int = 20,
    ) -> list[dict[str, Any]]:
        if max_count <= 0 or max_count > 100:
            raise ValidationError("max_count must be between 1 and 100")
        allowed_states = set(include_states)
        if allowed_states != {"active"}:
            raise ValidationError("ordinary recall permits active records only")
        if record_id:
            row = self.get(
                record_id,
                scope=scope,
                include_inactive=False,
                external_model=external_model,
            )
            return [row]
        needle = (query or "").casefold().strip()
        rows = []
        for row in self._build_state()["records"].values():
            if row.get("state") not in allowed_states:
                continue
            if not _scope_matches(row.get("scope", {}), scope):
                continue
            if not _egress_allowed(row, external_model):
                continue
            haystack = " ".join(
                str(row.get(field, "")) for field in ("text", "safe_summary", "entity", "kind")
            ).casefold()
            if needle and needle not in haystack:
                continue
            rows.append(json.loads(json.dumps(row)))
        rows.sort(key=lambda item: (item.get("modified_at", ""), item["id"]), reverse=True)
        return rows[:max_count]

    def forget_preview(
        self,
        *,
        scope: Scope,
        record_ids: Sequence[str] | None = None,
        all_in_scope: bool = False,
        reason: str,
    ) -> dict[str, Any]:
        reason = self._required_text(reason, "reason")
        if not record_ids and not all_in_scope:
            raise ValidationError("record_ids or explicit all_in_scope is required")
        if record_ids and all_in_scope:
            raise ValidationError("choose record_ids or all_in_scope, not both")
        if all_in_scope:
            rows = [
                row
                for row in self._build_state()["records"].values()
                if _scope_matches(row.get("scope", {}), scope) and row.get("state") != "forgotten"
            ]
        else:
            rows = []
            for record_id in record_ids or []:
                try:
                    rows.append(self.get(record_id, scope=scope, include_inactive=True))
                except MemoryNotFound as exc:
                    raise MemoryNotFound("memory not found") from exc
        if not rows:
            raise MemoryNotFound("memory not found")
        rows.sort(key=lambda item: item["id"])
        token = secrets.token_urlsafe(24)
        now = self._now()
        preview = {
            "schema_version": "1.0.0",
            "confirmation_token": token,
            "scope": scope.as_dict(),
            "reason": reason,
            "created_at": _iso(now),
            "expires_at": _iso(now + timedelta(minutes=15)),
            "confirmed_at": None,
            "impact": {
                "count": len(rows),
                "record_ids": [row["id"] for row in rows],
                "states": {row["id"]: row["state"] for row in rows},
                "revisions": {row["id"]: row["revision"] for row in rows},
                "checksums": {
                    row["id"]: self._file_checksum(self.record_path(row["id"])) for row in rows
                },
            },
        }
        self._atomic_json(self.paths.previews / f"{token}.json", preview)
        return preview

    def forget_confirm(self, confirmation_token: str, *, scope: Scope) -> dict[str, Any]:
        if not confirmation_token or not re.fullmatch(r"[A-Za-z0-9_-]+", confirmation_token):
            raise ConfirmationRequired("a valid preview confirmation token is required")
        path = self.paths.previews / f"{confirmation_token}.json"
        if not path.is_file():
            raise ConfirmationRequired("preview confirmation token is missing or expired")
        preview = self._read_json(path)
        if preview.get("scope") != scope.as_dict():
            raise MemoryNotFound("memory not found")
        if preview.get("confirmed_at"):
            raise ConfirmationRequired("preview confirmation token was already consumed")
        if _parse_time(preview["expires_at"]) < self._now():
            raise ConfirmationRequired("preview confirmation token expired")
        for record_id in preview["impact"]["record_ids"]:
            self.get(record_id, scope=scope, include_inactive=True)
            expected = preview["impact"]["checksums"][record_id]
            if self._file_checksum(self.record_path(record_id)) != expected:
                raise ConfirmationRequired("preview is stale; canonical record changed")

        now = self._now()
        receipt_id = self._receipt_id("forget", confirmation_token)
        receipt = self._new_receipt(receipt_id, "forget", preview["impact"]["record_ids"])
        self._write_receipt(receipt)
        try:
            fence_checksums: dict[str, str] = {}
            for record_id in preview["impact"]["record_ids"]:
                record = self._read_record(record_id)
                fence = {
                    "schema_version": "1.0.0",
                    "record_id": record_id,
                    "scope": scope.as_dict(),
                    "reason": preview["reason"],
                    "forgotten_at": _iso(now),
                    "record_revision": record["revision"],
                    "preview_token_hash": _sha256_bytes(confirmation_token.encode()),
                    "active": True,
                    "restored_at": None,
                    "restore_evidence": None,
                }
                fence_path = self.paths.fences / f"{record_id}.md"
                fence_checksums[record_id] = self._write_markdown_json(
                    fence_path, FENCE_MARKER, f"AKM Forget Fence {record_id}", fence
                )
                readback = self._read_markdown_json(fence_path, FENCE_MARKER)
                if readback != fence:
                    raise OSError(f"forget fence readback mismatch: {record_id}")
            preview["confirmed_at"] = _iso(now)
            self._atomic_json(path, preview)
            receipt.update(
                canonical_status="written",
                canonical_checksum=fence_checksums,
                revision=max(preview["impact"]["revisions"].values()),
            )
            self._write_receipt(receipt)
        except Exception as exc:
            receipt.update(canonical_status="failed", failure=str(exc), reconcile_status="manual")
            self._write_receipt(receipt)
            raise MemoryWriteError("forget fence write/readback failed", receipt_id) from exc
        self._finish_derived_write(receipt, receipt_id)
        first = preview["impact"]["record_ids"][0]
        return {
            "forgotten_count": len(preview["impact"]["record_ids"]),
            "record_ids": preview["impact"]["record_ids"],
            "readback": self.get(first, scope=scope, include_inactive=True),
            "receipt": receipt,
        }

    def restore_forgotten(
        self,
        record_id: str,
        *,
        scope: Scope,
        decision_evidence: str,
    ) -> dict[str, Any]:
        record = self.get(record_id, scope=scope, include_inactive=True)
        if record["state"] != "forgotten":
            raise ValidationError("record is not forgotten")
        fence_path = self.paths.fences / f"{record_id}.md"
        fence = self._read_markdown_json(fence_path, FENCE_MARKER)
        fence["active"] = False
        fence["restored_at"] = _iso(self._now())
        fence["restore_evidence"] = self._required_text(decision_evidence, "decision_evidence")
        receipt_id = self._receipt_id("restore", record_id)
        receipt = self._new_receipt(receipt_id, "restore", [record_id])
        self._write_receipt(receipt)
        try:
            checksum = self._write_markdown_json(
                fence_path, FENCE_MARKER, f"AKM Forget Fence {record_id}", fence
            )
            if self._read_markdown_json(fence_path, FENCE_MARKER) != fence:
                raise OSError(f"restore fence readback mismatch: {record_id}")
            receipt.update(
                canonical_status="written",
                canonical_checksum=checksum,
                revision=record["revision"],
            )
            self._write_receipt(receipt)
        except Exception as exc:
            receipt.update(canonical_status="failed", failure=str(exc), reconcile_status="manual")
            self._write_receipt(receipt)
            raise MemoryWriteError("restore fence write/readback failed", receipt_id) from exc
        self._finish_derived_write(receipt, receipt_id)
        return {
            "record": self.get(record_id, scope=scope, include_inactive=True),
            "fence": fence,
            "receipt": receipt,
        }

    def extract_local(
        self,
        input_text: str,
        *,
        scope: Scope,
        persist: bool = False,
    ) -> ExtractionOutcome:
        input_text = self._required_text(input_text, "input_text")
        candidates: list[dict[str, Any]] = []
        for line_number, line in enumerate(input_text.splitlines(), start=1):
            match = re.match(r"^\s*(?:remember|memory)\s*:\s*(.+?)\s*$", line, re.IGNORECASE)
            if not match:
                continue
            text = match.group(1)
            candidate = {
                "text": text,
                "entity": _slug(text),
                "evidence": {"extractor": "local-explicit-marker-v1", "line": line_number},
            }
            if persist:
                remembered = self.remember(
                    text,
                    scope=scope,
                    entity=candidate["entity"],
                    source_path="runtime-input://explicit-marker",
                    source_lineage=[f"local-input-line:{line_number}"],
                    extraction_evidence=candidate["evidence"],
                )
                candidate = remembered["record"]
            candidates.append(candidate)
        if not candidates:
            return ExtractionOutcome("nothing_salient", [])
        return ExtractionOutcome("success", candidates)

    def ingest_provider_boundary(
        self,
        outcome: str,
        *,
        payload: Mapping[str, Any] | None,
        scope: Scope,
        persist: bool = False,
    ) -> ExtractionOutcome:
        if outcome not in EXTRACTION_OUTCOMES:
            raise ValidationError(f"unknown provider outcome: {outcome}")
        if outcome != "success":
            if payload and payload.get("candidates"):
                raise ValidationError("provider outcome may not carry candidates unless it is success")
            return ExtractionOutcome(outcome, [], detail=str(payload.get("detail")) if payload else None)
        if not isinstance(payload, Mapping) or not isinstance(payload.get("candidates"), list):
            return ExtractionOutcome("malformed_output", [], "success payload lacks candidates list")
        candidates: list[dict[str, Any]] = []
        for index, raw in enumerate(payload["candidates"]):
            if not isinstance(raw, Mapping) or not isinstance(raw.get("text"), str):
                return ExtractionOutcome("malformed_output", [], f"candidate {index} is malformed")
            text = raw["text"].strip()
            if not text:
                return ExtractionOutcome("malformed_output", [], f"candidate {index} is empty")
            candidate = {"text": text, "entity": str(raw.get("entity") or _slug(text))}
            if persist:
                candidate = self.remember(
                    text,
                    scope=scope,
                    entity=candidate["entity"],
                    source_path="provider-boundary://supplied-output",
                    source_lineage=["explicit-provider-boundary"],
                    extraction_evidence={"provider_boundary": True, "candidate_index": index},
                )["record"]
            candidates.append(candidate)
        return ExtractionOutcome("success" if candidates else "nothing_salient", candidates)

    def context_pack(
        self,
        *,
        scope: Scope,
        entity_terms: Sequence[str],
        allowed_terms: Sequence[str],
        session_id: str,
        since: str | None = None,
        max_count: int = 5,
        token_budget: int = 400,
        external_model: bool = False,
        deliver: bool = False,
    ) -> dict[str, Any]:
        session_id = self._required_text(session_id, "session_id")
        if max_count < 1 or max_count > 20:
            raise ValidationError("max_count must be between 1 and 20")
        if token_budget < 1 or token_budget > 4000:
            raise ValidationError("token_budget must be between 1 and 4000")
        terms = [self._required_text(term, "entity term") for term in entity_terms]
        allow = {self._required_text(term, "allowed term").casefold() for term in allowed_terms}
        if not terms or any(term.casefold() not in allow for term in terms):
            self._append_usage(
                phase="attempted", record_ids=[], scope=scope, session_id=session_id, detail="term-not-allowlisted"
            )
            return {
                "status": "HOLD",
                "reason": "entity/project term is not allowlisted",
                "items": [],
                "token_estimate": 0,
                "suppressed_duplicates": [],
                "next_cursor": since,
            }
        since_time = _parse_time(since) if since else None
        all_rows = self.recall(scope=scope, external_model=external_model, max_count=100)
        attempted = [
            row
            for row in all_rows
            if any(
                term.casefold()
                in " ".join((row.get("entity", ""), row.get("safe_summary", ""))).casefold()
                for term in terms
            )
            and (since_time is None or _parse_time(row["modified_at"]) > since_time)
        ]
        self._append_usage(
            phase="attempted",
            record_ids=[row["id"] for row in attempted],
            scope=scope,
            session_id=session_id,
        )
        session_slug = _slug(session_id)[:48]
        session_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]
        cursor_path = self.paths.cursors / f"{session_slug}-{session_hash}.json"
        cursor = self._read_json(cursor_path) if cursor_path.is_file() else {"delivered": []}
        delivered_identities = set(cursor.get("delivered", []))
        suppressed: list[str] = []
        selected: list[dict[str, Any]] = []
        token_total = 0
        entity_counts: dict[str, int] = {}
        for row in attempted:
            identity = f"{row['id']}@{row['revision']}"
            if identity in delivered_identities:
                suppressed.append(identity)
                continue
            entity_counts[row["entity"]] = entity_counts.get(row["entity"], 0) + 1
        for row in attempted:
            identity = f"{row['id']}@{row['revision']}"
            if identity in delivered_identities:
                continue
            conflict = "HOLD" if entity_counts.get(row["entity"], 0) > 1 else "none"
            item = {
                "identity": identity,
                "pointer": f"{row['source']['path']}#memory:{row['id']}",
                "safe_summary": row["safe_summary"],
                "freshness": {
                    "modified_at": row["modified_at"],
                    "expires_at": row["expires_at"],
                },
                "conflict": conflict,
                "direct_read": len(row["text"]) > SAFE_SUMMARY_LIMIT,
            }
            estimate = max(1, math.ceil(len(_canonical_json(item)) / 4))
            if len(selected) >= max_count or token_total + estimate > token_budget:
                continue
            selected.append(item)
            token_total += estimate
        self._append_usage(
            phase="selected",
            record_ids=[item["identity"].split("@", 1)[0] for item in selected],
            scope=scope,
            session_id=session_id,
        )
        if deliver:
            delivered_identities.update(item["identity"] for item in selected)
            self._atomic_json(
                cursor_path,
                {
                    "session_id": session_id,
                    "delivered": sorted(delivered_identities),
                    "updated_at": _iso(self._now()),
                },
            )
            self._append_usage(
                phase="delivered",
                record_ids=[item["identity"].split("@", 1)[0] for item in selected],
                scope=scope,
                session_id=session_id,
            )
        return {
            "status": "ready",
            "items": selected,
            "token_estimate": token_total,
            "suppressed_duplicates": suppressed,
            "next_cursor": max((row["modified_at"] for row in attempted), default=since),
        }

    def delta_recall(self, *, scope: Scope, cursor: str | None = None) -> dict[str, Any]:
        self._assert_root_identity()
        after, seen_at_boundary, opaque_cursor = _decode_delta_cursor(cursor)
        snapshot_at = self._now()
        if after is not None and after > snapshot_at:
            raise ValidationError("delta cursor is in the future")
        events: list[dict[str, Any]] = []
        records, _ = self._load_records()
        for record in records.values():
            if not _scope_matches(record.get("scope", {}), scope):
                continue
            for ordinal, raw in enumerate(record.get("history", [])):
                at = _parse_time(raw["at"])
                event = {
                    "record_id": record["id"],
                    "change": raw["change"],
                    "at": raw["at"],
                    "revision": record["revision"],
                }
                event["_cursor_id"] = _delta_event_id(f"record:{record['id']}", ordinal, event)
                if at <= snapshot_at:
                    events.append(event)
            if record.get("expires_at") and record.get("state") == "active":
                expires = _parse_time(record["expires_at"])
                event = {
                    "record_id": record["id"],
                    "change": "expired",
                    "at": record["expires_at"],
                    "revision": record["revision"],
                }
                event["_cursor_id"] = _delta_event_id(f"expiry:{record['id']}", 0, event)
                if expires <= snapshot_at:
                    events.append(event)
        fences, _ = self._load_fences()
        for fence in fences.values():
            if not fence.get("active") or not _scope_matches(fence.get("scope", {}), scope):
                continue
            at = _parse_time(fence["forgotten_at"])
            event = {
                "record_id": fence["record_id"],
                "change": "forgotten",
                "at": fence["forgotten_at"],
                "revision": fence["record_revision"],
            }
            event["_cursor_id"] = _delta_event_id(
                f"fence:{fence['record_id']}@{fence['record_revision']}", 0, event
            )
            if at <= snapshot_at:
                events.append(event)
        events.sort(key=lambda item: (item["at"], item["record_id"], item["change"], item["_cursor_id"]))
        delivered: list[dict[str, Any]] = []
        for event in events:
            event_at = _parse_time(event["at"])
            if after is not None:
                if event_at < after:
                    continue
                if event_at == after and (not opaque_cursor or event["_cursor_id"] in seen_at_boundary):
                    continue
            delivered.append({key: value for key, value in event.items() if key != "_cursor_id"})
        boundary_seen = [
            event["_cursor_id"]
            for event in events
            if _parse_time(event["at"]) == snapshot_at
        ]
        return {"events": delivered, "next_cursor": _encode_delta_cursor(snapshot_at, boundary_seen)}

    def queue_promotion(
        self,
        record_id: str,
        *,
        scope: Scope,
        decision_evidence: str,
    ) -> dict[str, Any]:
        record = self.get(record_id, scope=scope, include_inactive=True)
        if record["state"] != "candidate":
            raise ValidationError("promotion queue accepts only candidates")
        destinations = {
            "preference": "30-context/users/ (ROUTER review required)",
            "safety": "30-context/domains/ (operator approval and ROUTER review required)",
            "procedure": "50-procedures/playbooks/ (ROUTER review required)",
            "event": "30-context/projects/ (ROUTER review required)",
        }
        queued = {
            "schema_version": "1.0.0",
            "record_id": record_id,
            "candidate_revision": record["revision"],
            "candidate_checksum": self._file_checksum(self.record_path(record_id)),
            "recommended_destination": destinations.get(
                record["kind"], "20-knowledge/ or 30-context/ (ROUTER decision required)"
            ),
            "decision_evidence": self._required_text(decision_evidence, "decision_evidence"),
            "source": record["source"],
            "scope": record["scope"],
            "status": "queued",
            "canonical_write_performed": False,
            "created_at": _iso(self._now()),
        }
        self._atomic_json(self.paths.promotion_queue / f"{record_id}.json", queued)
        return queued

    def status(self, *, scope: Scope | None = None) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for row in self._build_state()["records"].values():
            if scope is not None and not _scope_matches(row.get("scope", {}), scope):
                continue
            counts[row["state"]] = counts.get(row["state"], 0) + 1
        doctor = self.doctor()
        return {
            "canonical_authority": "AKM Markdown and original sources",
            "derived_state": str(self.paths.derived_state),
            "counts": counts,
            "unresolved_receipts": len(doctor["unresolved_receipts"]),
            "global_injection": "HOLD",
            "shadow_extraction": True,
        }

    def rebuild(self) -> dict[str, Any]:
        state = self._build_state()
        self._write_derived_state(state)
        return {
            "records": len(state["records"]),
            "malformed_records": state["diagnostics"]["malformed_records"],
            "malformed_fences": state["diagnostics"]["malformed_fences"],
            "derived_state": str(self.paths.derived_state),
        }

    def reconcile(self) -> dict[str, Any]:
        self._assert_root_identity()
        rebuild = self.rebuild()
        if rebuild["malformed_records"] or rebuild["malformed_fences"]:
            raise ValidationError("reconcile stopped because rebuild found malformed durable artifacts")
        reconciled: list[str] = []
        for path in sorted(self.paths.receipts.glob("*.json")):
            receipt = self._read_json(path)
            if receipt.get("reconcile_status") != "retry_required":
                continue
            receipt["derived_status"] = "written"
            receipt["reconcile_status"] = "reconciled"
            receipt["reconciled_at"] = _iso(self._now())
            receipt["failure"] = None
            self._atomic_json(path, receipt)
            reconciled.append(receipt["id"])
        return {"reconciled_receipts": reconciled, "derived_state": str(self.paths.derived_state)}

    def doctor(self) -> dict[str, Any]:
        self._assert_root_identity()
        canonical, malformed_records = self._load_records()
        fences, malformed_fences = self._load_fences()
        derived_state_error: str | None = None
        try:
            derived = self._read_json(self.paths.derived_state) if self.paths.derived_state.is_file() else {
                "records": {}, "checksums": {}
            }
            if canonical and not self.paths.derived_state.is_file():
                derived_state_error = "missing-derived-state"
        except (OSError, json.JSONDecodeError, ValidationError):
            derived = {"records": {}, "checksums": {}}
            derived_state_error = "malformed-derived-state"
        derived_records = derived.get("records", {}) if isinstance(derived.get("records"), dict) else {}
        derived_checksums = derived.get("checksums", {}) if isinstance(derived.get("checksums"), dict) else {}
        canonical_ids = set(canonical)
        db_only = sorted(set(derived_records) - canonical_ids)
        canonical_only = sorted(canonical_ids - set(derived_records))
        expected_records = self._build_state()["records"]
        canonical_drift = sorted(
            record_id
            for record_id in canonical_ids.intersection(derived_records)
            if derived_records[record_id] != expected_records[record_id]
        )
        missing_scope = sorted(
            record_id
            for record_id, row in {**canonical, **derived_records}.items()
            if not isinstance(row.get("scope"), Mapping) or not row.get("scope", {}).get("source_id")
        )
        checksum_drift = sorted(
            record_id
            for record_id in canonical_ids.intersection(derived_checksums)
            if derived_checksums[record_id] != self._file_checksum(self.record_path(record_id))
        )
        unresolved_receipts: list[str] = []
        for path in sorted(self.paths.receipts.glob("*.json")):
            try:
                receipt = self._read_json(path)
            except (OSError, json.JSONDecodeError):
                unresolved_receipts.append(path.stem)
                continue
            if receipt.get("reconcile_status") in {"retry_required", "manual"}:
                unresolved_receipts.append(str(receipt.get("id", path.stem)))
        expired_but_recalled: set[str] = set()
        if self.paths.usage_audit.is_file():
            for line in self._read_text(self.paths.usage_audit).splitlines():
                if not line.strip():
                    continue
                try:
                    usage = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if usage.get("phase") != "delivered":
                    continue
                used_at = _parse_time(usage["at"])
                for record_id in usage.get("record_ids", []):
                    record = canonical.get(record_id)
                    if record and record.get("expires_at") and used_at >= _parse_time(record["expires_at"]):
                        expired_but_recalled.add(record_id)
        malformed_fence_paths = list(malformed_fences)
        for record_id, fence in fences.items():
            if record_id not in canonical or fence.get("record_id") != record_id:
                malformed_fence_paths.append(str(self.paths.fences / f"{record_id}.md"))
        return {
            "ok": not any(
                (
                    db_only,
                    canonical_only,
                    canonical_drift,
                    derived_state_error,
                    missing_scope,
                    checksum_drift,
                    unresolved_receipts,
                    malformed_records,
                    malformed_fence_paths,
                    expired_but_recalled,
                )
            ),
            "orphan": db_only,
            "db_only": db_only,
            "canonical_only": canonical_only,
            "canonical_drift": canonical_drift,
            "derived_state_error": derived_state_error,
            "expired_but_recalled": sorted(expired_but_recalled),
            "missing_scope": missing_scope,
            "unresolved_receipts": sorted(unresolved_receipts),
            "malformed_records": malformed_records,
            "malformed_fences": sorted(set(malformed_fence_paths)),
            "checksum_drift": checksum_drift,
        }

    def read_receipt(self, receipt_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"rcpt_[a-f0-9]{24}", receipt_id):
            raise ValidationError("invalid receipt id")
        path = self.paths.receipts / f"{receipt_id}.json"
        if not path.is_file():
            raise MemoryNotFound("receipt not found")
        return self._read_json(path)

    def _append_usage(
        self,
        *,
        phase: str,
        record_ids: Sequence[str],
        scope: Scope,
        session_id: str,
        detail: str | None = None,
    ) -> None:
        if phase not in {"attempted", "selected", "delivered"}:
            raise ValidationError("invalid usage phase")
        event = {
            "schema_version": "1.0.0",
            "phase": phase,
            "record_ids": list(record_ids),
            "scope": scope.as_dict(),
            "session_id": session_id,
            "at": _iso(self._now()),
            "detail": detail,
        }
        self._append_text(self.paths.usage_audit, _canonical_json(event) + "\n")

    def _write_mutation(self, operation: str, record: dict[str, Any]) -> dict[str, Any]:
        receipt_id = self._receipt_id(operation, record["id"])
        receipt = self._new_receipt(receipt_id, operation, [record["id"]])
        self._write_receipt(receipt)
        try:
            checksum = self._write_record(record)
            receipt.update(
                canonical_status="written",
                canonical_checksum=checksum,
                revision=record["revision"],
            )
            self._write_receipt(receipt)
        except Exception as exc:
            receipt.update(canonical_status="failed", failure=str(exc), reconcile_status="manual")
            self._write_receipt(receipt)
            raise MemoryWriteError(f"{operation} Markdown write failed", receipt_id) from exc
        self._finish_derived_write(receipt, receipt_id)
        return {"record": record, "receipt": receipt}

    def _finish_derived_write(self, receipt: dict[str, Any], receipt_id: str) -> None:
        try:
            self._write_derived_state(self._build_state())
        except Exception as exc:
            receipt.update(
                derived_status="failed",
                failure=str(exc),
                reconcile_status="retry_required",
                completed_at=None,
            )
            self._write_receipt(receipt)
            raise MemoryWriteError(
                "canonical Markdown was written but derived state failed; reconcile required",
                receipt_id,
            ) from exc
        receipt.update(
            derived_status="written",
            reconcile_status="not_required",
            failure=None,
            completed_at=_iso(self._now()),
        )
        self._write_receipt(receipt)

    def _completed_noop_receipt(
        self, operation: str, record: Mapping[str, Any], path: Path
    ) -> dict[str, Any]:
        receipt_id = self._receipt_id(operation, record["id"])
        receipt = self._new_receipt(receipt_id, operation, [record["id"]])
        receipt.update(
            canonical_status="unchanged",
            canonical_checksum=self._file_checksum(path),
            revision=record["revision"],
        )
        self._write_receipt(receipt)
        self._finish_derived_write(receipt, receipt_id)
        return receipt

    def _new_receipt(self, receipt_id: str, operation: str, record_ids: Sequence[str]) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "id": receipt_id,
            "operation": operation,
            "record_ids": list(record_ids),
            "canonical_status": "pending",
            "derived_status": "pending",
            "canonical_checksum": None,
            "revision": None,
            "failure": None,
            "reconcile_status": "pending",
            "created_at": _iso(self._now()),
            "completed_at": None,
        }

    def _receipt_id(self, operation: str, identity: str) -> str:
        entropy = secrets.token_hex(8)
        digest = hashlib.sha256(f"{operation}\0{identity}\0{_iso(self._now())}\0{entropy}".encode()).hexdigest()
        return "rcpt_" + digest[:24]

    def _write_receipt(self, receipt: Mapping[str, Any]) -> None:
        self._atomic_json(self.paths.receipts / f"{receipt['id']}.json", receipt)

    def _write_record(self, record: Mapping[str, Any]) -> str:
        self._validate_record(record)
        return self._write_markdown_json(
            self.record_path(str(record["id"])),
            RECORD_MARKER,
            f"AKM Memory Record {record['id']}",
            record,
        )

    def _read_record(self, record_id: str) -> dict[str, Any]:
        path = self.record_path(record_id)
        if not path.is_file():
            raise MemoryNotFound("memory not found")
        record = self._read_markdown_json(path, RECORD_MARKER)
        self._validate_record(record)
        return record

    def _load_records(self) -> tuple[dict[str, dict[str, Any]], list[str]]:
        records: dict[str, dict[str, Any]] = {}
        malformed: list[str] = []
        for path in sorted(self.paths.records.glob("*.md")):
            if path.is_symlink() or not path.is_file():
                malformed.append(str(path))
                continue
            try:
                record = self._read_markdown_json(path, RECORD_MARKER)
                self._validate_record(record)
                if path.stem != record["id"] or record["id"] in records:
                    raise ValidationError("record filename/id mismatch or duplicate")
                records[record["id"]] = record
            except (OSError, json.JSONDecodeError, ValidationError):
                malformed.append(str(path))
        return records, malformed

    def _load_fences(self) -> tuple[dict[str, dict[str, Any]], list[str]]:
        fences: dict[str, dict[str, Any]] = {}
        malformed: list[str] = []
        for path in sorted(self.paths.fences.glob("*.md")):
            if path.is_symlink() or not path.is_file():
                malformed.append(str(path))
                continue
            try:
                fence = self._read_markdown_json(path, FENCE_MARKER)
                required = {
                    "record_id",
                    "scope",
                    "forgotten_at",
                    "record_revision",
                    "active",
                }
                if not required.issubset(fence) or path.stem != fence["record_id"]:
                    raise ValidationError("malformed forget fence")
                Scope.from_mapping(fence["scope"])
                _parse_time(fence["forgotten_at"])
                if not isinstance(fence["active"], bool):
                    raise ValidationError("forget fence active must be boolean")
                fences[fence["record_id"]] = fence
            except (OSError, json.JSONDecodeError, ValidationError, TypeError):
                malformed.append(str(path))
        return fences, malformed

    def _build_state(self) -> dict[str, Any]:
        self._assert_root_identity()
        records, malformed_records = self._load_records()
        fences, malformed_fences = self._load_fences()
        effective: dict[str, dict[str, Any]] = {}
        for record_id, raw in records.items():
            record = json.loads(json.dumps(raw))
            if (
                record["state"] == "active"
                and record.get("expires_at")
                and not record.get("stable_authority")
                and _parse_time(record["expires_at"]) <= self._now()
            ):
                record["state"] = "expired"
            fence = fences.get(record_id)
            if fence and fence.get("active"):
                record["state"] = "forgotten"
                record["forgotten_at"] = fence["forgotten_at"]
            effective[record_id] = record
        checksums = {
            record_id: self._file_checksum(self.record_path(record_id)) for record_id in records
        }
        return {
            "schema_version": "1.0.0",
            "generated_at": _iso(self._now()),
            "authority": "runtime Markdown records and fences; AKM sources remain claim authority",
            "records": effective,
            "checksums": checksums,
            "diagnostics": {
                "malformed_records": malformed_records,
                "malformed_fences": malformed_fences,
            },
        }

    def _write_derived_state(self, state: dict[str, Any]) -> None:
        self._atomic_json(self.paths.derived_state, state)

    def _validate_record(self, record: Mapping[str, Any]) -> None:
        missing = RECORD_FIELDS - set(record)
        if missing:
            raise ValidationError(f"memory record missing fields: {sorted(missing)}")
        unexpected = set(record) - RECORD_FIELDS - {"forgotten_at"}
        if unexpected:
            raise ValidationError(f"memory record has unexpected fields: {sorted(unexpected)}")
        if record.get("schema_version") != "1.0.0":
            raise ValidationError("unsupported memory record schema version")
        self._validate_id(str(record["id"]))
        if record["state"] not in STATES:
            raise ValidationError("invalid lifecycle state")
        if record["kind"] not in KINDS or record["visibility"] not in VISIBILITIES:
            raise ValidationError("invalid kind or visibility")
        if (
            not isinstance(record["revision"], int)
            or isinstance(record["revision"], bool)
            or record["revision"] < 1
        ):
            raise ValidationError("revision must be a positive integer")
        text = self._required_text(record["text"], "text")
        summary = self._required_text(record["safe_summary"], "safe_summary")
        entity = self._required_text(record["entity"], "entity")
        if len(summary) > SAFE_SUMMARY_LIMIT:
            raise ValidationError("safe_summary exceeds the schema limit")
        if len(entity) > 200:
            raise ValidationError("entity exceeds the schema limit")
        if not isinstance(record["egress_allowed"], bool) or not isinstance(
            record["stable_authority"], bool
        ):
            raise ValidationError("egress_allowed and stable_authority must be boolean")
        if _safe_summary(text) != summary:
            raise ValidationError("safe_summary does not match the bounded text summary")
        Scope.from_mapping(record["scope"])
        created_at = _parse_time(record["created_at"])
        modified_at = _parse_time(record["modified_at"])
        if modified_at < created_at:
            raise ValidationError("modified_at may not precede created_at")
        if record.get("expires_at"):
            _parse_time(record["expires_at"])
        if record.get("forgotten_at"):
            _parse_time(record["forgotten_at"])
        for relation in ("supersedes", "superseded_by"):
            if record.get(relation) is not None:
                self._validate_id(record[relation])
        if record.get("decision_evidence") is not None and not isinstance(
            record["decision_evidence"], Mapping
        ):
            raise ValidationError("decision_evidence must be an object or null")
        source = record.get("source")
        if not isinstance(source, Mapping) or not source.get("path") or not source.get("lineage"):
            raise ValidationError("source path and lineage are required")
        if set(source) != SOURCE_FIELDS:
            raise ValidationError("source must contain exactly path and lineage")
        self._required_text(source["path"], "source path")
        if not isinstance(source["lineage"], list) or not source["lineage"] or any(
            not isinstance(item, str) or not item.strip() for item in source["lineage"]
        ):
            raise ValidationError("source lineage must be a non-empty string list")
        if not isinstance(record["history"], list) or not record["history"]:
            raise ValidationError("history must be a non-empty list")
        for event in record["history"]:
            if not isinstance(event, Mapping):
                raise ValidationError("history event must be an object")
            if not {"change", "at", "evidence"}.issubset(event) or set(event) - HISTORY_FIELDS:
                raise ValidationError("history event fields do not match the schema")
            if event["change"] not in HISTORY_CHANGES:
                raise ValidationError("invalid history change")
            _parse_time(event["at"])
            self._required_text(event["evidence"], "history evidence")
            if "detail" in event and not isinstance(event["detail"], str):
                raise ValidationError("history detail must be a string")
            if "related_record_id" in event:
                self._validate_id(event["related_record_id"])
        if record.get("stable_authority") and record.get("expires_at"):
            raise ValidationError("stable authority may not expire")
        if record.get("stable_authority") and record.get("kind") not in STABLE_AUTHORITY_KINDS:
            raise ValidationError("stable authority is limited to preference and safety records")

    @staticmethod
    def _validate_id(record_id: str) -> None:
        if not re.fullmatch(r"mem_[a-z0-9_-]{3,80}", record_id):
            raise ValidationError("invalid memory id")

    @staticmethod
    def _required_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field} is required")
        return value.strip()

    def _read_markdown_json(self, path: Path, marker: str) -> dict[str, Any]:
        text = self._read_text(path)
        if marker not in text:
            raise ValidationError(f"missing marker in {path}")
        match = JSON_BLOCK.search(text)
        if not match:
            raise ValidationError(f"missing JSON block in {path}")
        payload = json.loads(match.group("payload"))
        if not isinstance(payload, dict):
            raise ValidationError(f"JSON block must be an object in {path}")
        return payload

    def _write_markdown_json(
        self,
        path: Path,
        marker: str,
        title: str,
        value: Mapping[str, Any],
    ) -> str:
        body = (
            f"{marker}\n# {title}\n\n"
            "This machine-readable Markdown artifact is local runtime state. "
            "AKM source Markdown remains authoritative for claims.\n\n"
            "```json\n"
            + json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n```\n"
        )
        self._atomic_text(path, body)
        return self._file_checksum(path)

    def _read_json(self, path: Path) -> dict[str, Any]:
        value = json.loads(self._read_text(path))
        if not isinstance(value, dict):
            raise ValidationError(f"expected JSON object: {path}")
        return value

    def _atomic_json(self, path: Path, value: Mapping[str, Any]) -> None:
        self._atomic_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")

    def _atomic_text(self, path: Path, text: str) -> None:
        parent_fd, leaf = self._secure_parent_fd(path)
        temp_name = f".{leaf}.{secrets.token_hex(12)}"
        descriptor: int | None = None
        try:
            descriptor = os.open(
                temp_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent_fd,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                descriptor = None
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, leaf, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            os.fsync(parent_fd)
        except Exception as exc:
            if descriptor is not None:
                os.close(descriptor)
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            if isinstance(exc, OSError):
                raise ValidationError(f"unsafe runtime path: {path}") from exc
            raise
        finally:
            os.close(parent_fd)

    def _append_text(self, path: Path, text: str) -> None:
        parent_fd, leaf = self._secure_parent_fd(path)
        descriptor: int | None = None
        try:
            descriptor = os.open(
                leaf,
                os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent_fd,
            )
            file_stat = os.fstat(descriptor)
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                raise ValidationError(f"runtime path is not a regular file: {path}")
            with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
                descriptor = None
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise ValidationError(f"unsafe runtime path: {path}") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(parent_fd)

    def _read_text(self, path: Path) -> str:
        parent_fd, leaf = self._secure_parent_fd(path)
        descriptor: int | None = None
        try:
            descriptor = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
            file_stat = os.fstat(descriptor)
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                raise ValidationError(f"runtime path is not a regular file: {path}")
            with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
                descriptor = None
                return handle.read()
        except OSError as exc:
            raise ValidationError(f"unsafe runtime path: {path}") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(parent_fd)

    def _read_bytes(self, path: Path) -> bytes:
        parent_fd, leaf = self._secure_parent_fd(path)
        descriptor: int | None = None
        try:
            descriptor = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
            file_stat = os.fstat(descriptor)
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                raise ValidationError(f"runtime path is not a regular file: {path}")
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = None
                return handle.read()
        except OSError as exc:
            raise ValidationError(f"unsafe runtime path: {path}") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(parent_fd)

    def _secure_parent_fd(self, path: Path) -> tuple[int, str]:
        """Open each runtime path component without following symlinks.

        The runtime is single-writer, but an operator or local process may replace
        a child directory after construction. Directory-fd traversal plus
        ``O_NOFOLLOW`` keeps every later read/write inside the originally selected
        runtime root instead of trusting a one-time ``Path.resolve`` check.
        """

        try:
            relative = path.relative_to(self.paths.root)
        except ValueError as exc:
            raise ValidationError(f"runtime path escapes selected root: {path}") from exc
        if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
            raise ValidationError(f"invalid runtime path: {path}")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        current_fd: int | None = None
        try:
            current_fd = os.open(self.paths.root, flags)
            root_stat = os.fstat(current_fd)
            if (root_stat.st_dev, root_stat.st_ino) != self._root_identity:
                raise ValidationError("runtime root identity changed after initialization")
            for component in relative.parts[:-1]:
                next_fd = os.open(component, flags, dir_fd=current_fd)
                os.close(current_fd)
                current_fd = next_fd
        except (OSError, ValidationError) as exc:
            if current_fd is not None:
                os.close(current_fd)
            if isinstance(exc, ValidationError):
                raise
            raise ValidationError(f"unsafe runtime path: {path}") from exc
        assert current_fd is not None
        return current_fd, relative.parts[-1]

    def _assert_root_identity(self) -> None:
        descriptor: int | None = None
        try:
            descriptor = os.open(
                self.paths.root,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
            root_stat = os.fstat(descriptor)
            if (root_stat.st_dev, root_stat.st_ino) != self._root_identity:
                raise ValidationError("runtime root identity changed after initialization")
            for directory in (
                self.paths.records,
                self.paths.fences,
                self.paths.derived,
                self.paths.receipts,
                self.paths.previews,
                self.paths.promotion_queue,
                self.paths.cursors,
                self.paths.audit,
            ):
                relative = directory.relative_to(self.paths.root)
                if len(relative.parts) != 1:
                    raise ValidationError(f"invalid runtime directory layout: {directory}")
                child_fd = os.open(
                    relative.parts[0],
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=descriptor,
                )
                os.close(child_fd)
        except OSError as exc:
            raise ValidationError(f"unsafe runtime root: {self.paths.root}") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def _file_checksum(self, path: Path) -> str:
        return _sha256_bytes(self._read_bytes(path))


def compute_metrics(observations: Sequence[Mapping[str, Any]]) -> dict[str, float | int | None]:
    """Compute the fixed evaluation surface without inventing missing denominators."""

    if not observations:
        return {
            "false_memory_rate": None,
            "duplicate_injection_rate": None,
            "conflict_exposure_rate": None,
            "usefulness_rate": None,
            "token_cost": 0,
            "latency_ms": None,
            "manual_correction_rate": None,
            "source_lineage_recovery_rate": None,
        }
    total = len(observations)

    def rate(field: str) -> float:
        return sum(bool(row.get(field)) for row in observations) / total

    latencies = [float(row["latency_ms"]) for row in observations if row.get("latency_ms") is not None]
    return {
        "false_memory_rate": rate("false_memory"),
        "duplicate_injection_rate": rate("duplicate_injection"),
        "conflict_exposure_rate": rate("conflict_exposed"),
        "usefulness_rate": rate("useful"),
        "token_cost": sum(int(row.get("token_cost", 0)) for row in observations),
        "latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "manual_correction_rate": rate("manual_correction"),
        "source_lineage_recovery_rate": rate("source_lineage_recovered"),
    }

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema
import pytest

from adapters.hermes.memory import (
    ConfirmationRequired,
    HoldoutEvaluator,
    MemoryNotFound,
    MemoryRuntime,
    MemoryWriteError,
    Scope,
    ValidationError,
    compute_metrics,
)


UTC = timezone.utc


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 13, 1, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **kwargs: int) -> None:
        self.value += timedelta(**kwargs)


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def scope() -> Scope:
    return Scope(source_id="akm", project="runtime-demo", profile="default", user="operator")


@pytest.fixture
def runtime(tmp_path: Path, clock: Clock) -> MemoryRuntime:
    return MemoryRuntime(tmp_path / "runtime", now=clock)


def remember_active(
    runtime: MemoryRuntime,
    scope: Scope,
    text: str,
    *,
    entity: str,
    **kwargs: object,
) -> dict:
    result = runtime.remember(
        text,
        scope=scope,
        entity=entity,
        source_path="40-memory/user-preferences.md",
        source_lineage=["user-stated"],
        **kwargs,
    )
    runtime.approve(
        result["record"]["id"],
        scope=scope,
        decision_evidence="operator-approved:test",
    )
    return runtime.get(result["record"]["id"], scope=scope)


def test_schema_accepts_runtime_record(runtime: MemoryRuntime, scope: Scope) -> None:
    result = runtime.remember(
        "Use concise status updates.",
        scope=scope,
        entity="status-updates",
        kind="preference",
        stable_authority=True,
        source_path="40-memory/user-preferences.md",
        source_lineage=["user-stated"],
    )
    schema_path = Path(__file__).parents[4] / "99-system" / "memory-record.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(result["record"], schema)
    assert result["record"]["state"] == "candidate"
    assert result["receipt"]["canonical_status"] == "written"
    assert result["receipt"]["derived_status"] == "written"


def test_runtime_root_must_stay_outside_an_akm_canonical_vault(tmp_path: Path) -> None:
    akm_root = tmp_path / "akm"
    (akm_root / "99-system").mkdir(parents=True)
    (akm_root / "99-system" / "SCHEMA.md").write_text("# schema\n", encoding="utf-8")
    (akm_root / "99-system" / "ROUTER.md").write_text("# router\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="outside the AKM canonical vault"):
        MemoryRuntime(akm_root / "40-memory" / "runtime")


def test_runtime_rejects_post_init_symlink_directory_escape(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    outside = tmp_path / "outside"
    outside.mkdir()
    runtime = MemoryRuntime(root)
    runtime.paths.records.rmdir()
    runtime.paths.records.symlink_to(outside, target_is_directory=True)

    with pytest.raises(MemoryWriteError) as captured:
        runtime.remember(
            "Symlink escape must fail closed.",
            scope=Scope(source_id="akm"),
            entity="symlink-escape",
            source_path="30-context/projects/symlink.md",
            source_lineage=["adversarial-probe"],
        )
    assert list(outside.iterdir()) == []
    receipt = runtime.read_receipt(captured.value.receipt_id)
    assert receipt["canonical_status"] == "failed"
    assert receipt["reconcile_status"] == "manual"
    with pytest.raises(ValidationError, match="unsafe runtime root"):
        runtime.status(scope=Scope(source_id="akm"))


def test_runtime_rejects_post_init_root_replacement(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    moved = tmp_path / "moved-runtime"
    outside = tmp_path / "outside-root"
    runtime = MemoryRuntime(root)
    outside.mkdir()
    root.rename(moved)
    root.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValidationError, match="unsafe runtime (?:path|root)|identity changed"):
        runtime.status(scope=Scope(source_id="akm"))
    assert list(outside.iterdir()) == []


def test_runtime_rejects_usage_audit_hardlink_escape(
    runtime: MemoryRuntime, scope: Scope, tmp_path: Path
) -> None:
    outside = tmp_path / "outside-audit.jsonl"
    outside.write_text("external-prefix\n", encoding="utf-8")
    os.link(outside, runtime.paths.usage_audit)

    with pytest.raises(ValidationError, match="regular file"):
        runtime.context_pack(
            scope=scope,
            entity_terms=["atlas"],
            allowed_terms=["atlas"],
            session_id="hardlink-probe",
        )
    assert outside.read_text(encoding="utf-8") == "external-prefix\n"


def test_conformance_remember_recall_forget_rebuild_recall(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    active = remember_active(runtime, scope, "The runtime is local only.", entity="runtime")
    assert runtime.recall(scope=scope, query="local")[0]["id"] == active["id"]

    preview = runtime.forget_preview(
        scope=scope,
        record_ids=[active["id"]],
        reason="conformance-test",
    )
    assert preview["impact"]["count"] == 1
    result = runtime.forget_confirm(preview["confirmation_token"], scope=scope)
    assert result["readback"]["state"] == "forgotten"
    schema_path = Path(__file__).parents[4] / "99-system" / "memory-record.schema.json"
    jsonschema.validate(result["readback"], json.loads(schema_path.read_text(encoding="utf-8")))

    runtime.rebuild()
    assert runtime.recall(scope=scope, query="local") == []
    assert runtime.get(active["id"], scope=scope, include_inactive=True)["state"] == "forgotten"


def test_scope_isolation_and_unauthorized_probes_are_not_found(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    record = remember_active(runtime, scope, "Private project fact.", entity="secret-project")
    wrong = Scope(source_id="akm", project="other", profile="default", user="operator")

    assert runtime.recall(scope=wrong, query="Private") == []
    with pytest.raises(MemoryNotFound):
        runtime.get(record["id"], scope=wrong)
    with pytest.raises(MemoryNotFound):
        runtime.forget_preview(scope=wrong, record_ids=[record["id"]], reason="probe")


def test_ordinary_recall_cannot_expose_candidate_state(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    candidate = runtime.remember(
        "Candidate must stay out of ordinary recall.",
        scope=scope,
        entity="candidate-isolation",
        source_path="00-inbox/candidate.md",
        source_lineage=["adversarial-audit"],
    )["record"]
    assert runtime.recall(scope=scope, query="Candidate") == []
    with pytest.raises(MemoryNotFound, match="memory not found"):
        runtime.recall(scope=scope, record_id=candidate["id"])
    with pytest.raises(ValidationError, match="active records only"):
        runtime.recall(scope=scope, include_states=["candidate"])
    with pytest.raises(MemoryNotFound, match="memory not found"):
        runtime.get(
            candidate["id"],
            scope=scope,
            include_inactive=True,
            external_model=True,
        )


def test_private_visibility_is_separate_from_external_model_egress(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    private = remember_active(
        runtime,
        scope,
        "A private internal detail.",
        entity="private-detail",
        visibility="private",
        egress_allowed=True,
    )
    public = remember_active(
        runtime,
        scope,
        "A publishable detail.",
        entity="public-detail",
        visibility="public",
        egress_allowed=True,
    )

    internal = runtime.recall(scope=scope)
    assert {row["id"] for row in internal} == {private["id"], public["id"]}
    external = runtime.recall(scope=scope, external_model=True)
    assert [row["id"] for row in external] == [public["id"]]
    with pytest.raises(MemoryNotFound):
        runtime.get(private["id"], scope=scope, external_model=True)


def test_ttl_and_stable_authority_never_auto_expire(
    runtime: MemoryRuntime, scope: Scope, clock: Clock
) -> None:
    expiring = remember_active(
        runtime,
        scope,
        "Temporary launch context.",
        entity="launch",
        ttl_seconds=60,
    )
    with pytest.raises(ValidationError, match="stable authority"):
        runtime.remember(
            "Never upload secrets.",
            scope=scope,
            entity="secret-safety",
            kind="safety",
            stable_authority=True,
            ttl_seconds=60,
            source_path="40-memory/safety.md",
            source_lineage=["operator-approved"],
        )
    stable = remember_active(
        runtime,
        scope,
        "Prefer short summaries.",
        entity="summary-style",
        kind="preference",
        stable_authority=True,
    )

    clock.advance(seconds=61)
    assert runtime.recall(scope=scope, query="Temporary") == []
    assert runtime.get(expiring["id"], scope=scope, include_inactive=True)["state"] == "expired"
    assert runtime.get(stable["id"], scope=scope)["state"] == "active"


def test_supersession_is_persisted_and_survives_rebuild(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    old = remember_active(runtime, scope, "Use option A.", entity="runtime-option")
    new = remember_active(runtime, scope, "Use option B.", entity="runtime-option")

    assert runtime.get(old["id"], scope=scope, include_inactive=True)["state"] == "superseded"
    assert runtime.get(old["id"], scope=scope, include_inactive=True)["superseded_by"] == new["id"]
    runtime.rebuild()
    assert [row["id"] for row in runtime.recall(scope=scope, query="option")] == [new["id"]]


def test_rejected_lifecycle_is_durable_and_not_recalled(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    candidate = runtime.remember(
        "Unsupported candidate.",
        scope=scope,
        entity="rejected",
        source_path="00-inbox/candidate.md",
        source_lineage=["shadow"],
    )["record"]
    rejected = runtime.reject(
        candidate["id"], scope=scope, decision_evidence="direct source did not support it"
    )["record"]
    assert rejected["state"] == "rejected"
    runtime.rebuild()
    assert runtime.recall(scope=scope, query="Unsupported") == []
    assert runtime.get(candidate["id"], scope=scope, include_inactive=True)["state"] == "rejected"
    with pytest.raises(ValidationError, match="only candidate records"):
        runtime.approve(candidate["id"], scope=scope, decision_evidence="cannot undo rejection")
    with pytest.raises(ValidationError, match="only candidates"):
        runtime.queue_promotion(
            candidate["id"], scope=scope, decision_evidence="cannot promote rejected evidence"
        )


def test_extraction_outcomes_are_explicit_and_shadow_only(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    success = runtime.extract_local(
        "Remember: Use pointer-first retrieval.\nordinary line",
        scope=scope,
        persist=True,
    )
    assert success.outcome == "success"
    assert len(success.candidates) == 1
    candidate = runtime.get(success.candidates[0]["id"], scope=scope, include_inactive=True)
    assert candidate["state"] == "candidate"
    assert runtime.recall(scope=scope) == []

    nothing = runtime.extract_local("ordinary line", scope=scope)
    assert nothing.outcome == "nothing_salient"
    for outcome in (
        "provider_error",
        "refusal",
        "content_filter",
        "malformed_output",
        "truncated_output",
    ):
        observed = runtime.ingest_provider_boundary(outcome, payload=None, scope=scope)
        assert observed.outcome == outcome
        assert observed.candidates == []
    with pytest.raises(ValidationError, match="provider outcome"):
        runtime.ingest_provider_boundary("nothing_salient", payload={"candidates": [1]}, scope=scope)


def test_write_receipt_failure_is_non_success_and_reconcilable(
    runtime: MemoryRuntime, scope: Scope, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = runtime._write_derived_state

    def fail_once(state: dict) -> None:
        monkeypatch.setattr(runtime, "_write_derived_state", original)
        raise OSError("simulated derived failure")

    monkeypatch.setattr(runtime, "_write_derived_state", fail_once)
    with pytest.raises(MemoryWriteError) as captured:
        runtime.remember(
            "Canonical write must not look successful.",
            scope=scope,
            entity="receipt",
            source_path="30-context/projects/runtime.md",
            source_lineage=["operator"],
        )
    receipt = runtime.read_receipt(captured.value.receipt_id)
    assert receipt["canonical_status"] == "written"
    assert receipt["derived_status"] == "failed"
    assert receipt["reconcile_status"] == "retry_required"
    assert runtime.doctor()["unresolved_receipts"] == [captured.value.receipt_id]

    reconciled = runtime.reconcile()
    assert captured.value.receipt_id in reconciled["reconciled_receipts"]
    assert runtime.doctor()["unresolved_receipts"] == []


def test_doctor_detects_db_only_drift_missing_scope_malformed_fence_and_expired_use(
    runtime: MemoryRuntime, scope: Scope, clock: Clock
) -> None:
    record = remember_active(
        runtime,
        scope,
        "Short-lived detail.",
        entity="doctor-detail",
        ttl_seconds=10,
    )
    state = json.loads(runtime.paths.derived_state.read_text(encoding="utf-8"))
    ghost = dict(record)
    ghost["id"] = "mem_db_only"
    ghost["scope"] = {}
    state["records"][ghost["id"]] = ghost
    runtime.paths.derived_state.write_text(json.dumps(state), encoding="utf-8")
    (runtime.paths.fences / "bad.md").write_text("not a valid forget fence", encoding="utf-8")
    clock.advance(seconds=11)
    runtime._append_usage(
        phase="delivered",
        record_ids=[record["id"]],
        scope=scope,
        session_id="doctor-test",
    )

    report = runtime.doctor()
    assert "mem_db_only" in report["db_only"]
    assert "mem_db_only" in report["missing_scope"]
    assert report["malformed_fences"]
    assert record["id"] in report["expired_but_recalled"]


def test_doctor_detects_checksum_drift(runtime: MemoryRuntime, scope: Scope) -> None:
    record = runtime.remember(
        "Checksum source.",
        scope=scope,
        entity="checksum",
        source_path="30-context/projects/checksum.md",
        source_lineage=["operator"],
    )["record"]
    path = runtime.record_path(record["id"])
    path.write_text(path.read_text(encoding="utf-8") + "\nmanual drift\n", encoding="utf-8")
    assert record["id"] in runtime.doctor()["checksum_drift"]


def test_doctor_detects_missing_derived_state_and_rebuild_repairs_it(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    record = runtime.remember(
        "Rebuildable canonical record.",
        scope=scope,
        entity="rebuild",
        source_path="30-context/projects/rebuild.md",
        source_lineage=["operator"],
    )["record"]
    runtime.paths.derived_state.unlink()
    report = runtime.doctor()
    assert report["derived_state_error"] == "missing-derived-state"
    assert report["canonical_only"] == [record["id"]]
    assert report["ok"] is False
    runtime.rebuild()
    assert runtime.doctor()["ok"] is True


def test_forget_requires_preview_token_and_exact_scope(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    first = remember_active(runtime, scope, "First record.", entity="first")
    second = remember_active(runtime, scope, "Second record.", entity="second")
    with pytest.raises(ConfirmationRequired):
        runtime.forget_confirm("missing-token", scope=scope)
    with pytest.raises(ValidationError, match="all_in_scope"):
        runtime.forget_preview(scope=scope, record_ids=None, reason="mass")

    preview = runtime.forget_preview(scope=scope, all_in_scope=True, reason="mass")
    assert preview["impact"]["record_ids"] == sorted([first["id"], second["id"]])
    wrong = Scope(source_id="akm", project="other", profile="default", user="operator")
    with pytest.raises(MemoryNotFound):
        runtime.forget_confirm(preview["confirmation_token"], scope=wrong)
    result = runtime.forget_confirm(preview["confirmation_token"], scope=scope)
    assert result["forgotten_count"] == 2


def test_forget_fence_is_reversible_with_explicit_restore_evidence(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    record = remember_active(runtime, scope, "Restorable record.", entity="restore")
    preview = runtime.forget_preview(
        scope=scope, record_ids=[record["id"]], reason="mistaken-forget"
    )
    runtime.forget_confirm(preview["confirmation_token"], scope=scope)
    restored = runtime.restore_forgotten(
        record["id"], scope=scope, decision_evidence="operator-reviewed-restore"
    )
    assert restored["record"]["state"] == "active"
    assert restored["fence"]["active"] is False
    assert restored["fence"]["restore_evidence"] == "operator-reviewed-restore"
    assert restored["receipt"]["operation"] == "restore"
    assert restored["receipt"]["canonical_status"] == "written"
    assert restored["receipt"]["derived_status"] == "written"
    runtime.rebuild()
    assert runtime.recall(scope=scope, query="Restorable")[0]["id"] == record["id"]


def test_context_pack_is_bounded_pointer_first_and_suppresses_duplicates(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    one = remember_active(
        runtime,
        scope,
        "Project Atlas uses pointer-first retrieval with a compact summary.",
        entity="atlas",
    )
    remember_active(
        runtime,
        scope,
        "Project Borealis is unrelated and must not leak.",
        entity="borealis",
    )

    held = runtime.context_pack(
        scope=scope,
        entity_terms=["Borealis"],
        allowed_terms=["Atlas"],
        session_id="session-a",
        max_count=2,
        token_budget=100,
    )
    assert held["status"] == "HOLD"
    assert held["items"] == []

    pack = runtime.context_pack(
        scope=scope,
        entity_terms=["Atlas"],
        allowed_terms=["Atlas"],
        session_id="session-a",
        max_count=1,
        token_budget=100,
        deliver=True,
    )
    assert pack["status"] == "ready"
    assert pack["items"][0]["identity"] == f"{one['id']}@{one['revision']}"
    assert set(pack["items"][0]) == {
        "identity",
        "pointer",
        "safe_summary",
        "freshness",
        "conflict",
        "direct_read",
    }
    assert "evidence" not in json.dumps(pack)
    assert "usage" not in json.dumps(pack)

    duplicate = runtime.context_pack(
        scope=scope,
        entity_terms=["Atlas"],
        allowed_terms=["Atlas"],
        session_id="session-a",
        max_count=1,
        token_budget=100,
        deliver=True,
    )
    assert duplicate["items"] == []
    assert duplicate["suppressed_duplicates"] == [f"{one['id']}@{one['revision']}"]


def test_context_pack_records_attempted_selected_and_delivered_but_never_embeds_audit(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    remember_active(runtime, scope, "Atlas context.", entity="atlas")
    pack = runtime.context_pack(
        scope=scope,
        entity_terms=["Atlas"],
        allowed_terms=["Atlas"],
        session_id="usage-session",
        deliver=True,
    )
    rows = [json.loads(line) for line in runtime.paths.usage_audit.read_text(encoding="utf-8").splitlines()]
    assert [row["phase"] for row in rows] == ["attempted", "selected", "delivered"]
    assert "audit" not in pack


def test_delta_recall_reports_lifecycle_changes_after_cursor(
    runtime: MemoryRuntime, scope: Scope, clock: Clock
) -> None:
    first = remember_active(runtime, scope, "Old setting.", entity="setting")
    cursor = runtime.delta_recall(scope=scope)["next_cursor"]
    clock.advance(seconds=1)
    second = remember_active(runtime, scope, "New setting.", entity="setting")
    preview = runtime.forget_preview(scope=scope, record_ids=[second["id"]], reason="delta")
    runtime.forget_confirm(preview["confirmation_token"], scope=scope)

    delta = runtime.delta_recall(scope=scope, cursor=cursor)
    kinds = {event["change"] for event in delta["events"]}
    assert {"created", "modified", "superseded", "forgotten"}.issubset(kinds)
    assert first["id"] in {event["record_id"] for event in delta["events"]}


def test_delta_cursor_delivers_new_same_timestamp_events_once(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    first = runtime.remember(
        "First boundary event.",
        scope=scope,
        entity="delta-boundary-first",
        source_path="30-context/projects/delta-first.md",
        source_lineage=["adversarial-audit"],
    )["record"]
    cursor = runtime.delta_recall(scope=scope)["next_cursor"]
    second = runtime.remember(
        "Second event at the exact same clock timestamp.",
        scope=scope,
        entity="delta-boundary-second",
        source_path="30-context/projects/delta-second.md",
        source_lineage=["adversarial-audit"],
    )["record"]
    runtime.approve(second["id"], scope=scope, decision_evidence="same timestamp audit")

    delta = runtime.delta_recall(scope=scope, cursor=cursor)
    assert first["id"] not in {event["record_id"] for event in delta["events"]}
    assert second["id"] in {event["record_id"] for event in delta["events"]}
    assert {event["change"] for event in delta["events"]} == {"created", "modified"}
    repeated = runtime.delta_recall(scope=scope, cursor=delta["next_cursor"])
    assert repeated["events"] == []


def test_delta_cursor_does_not_replay_prior_event_when_same_record_changes_at_boundary(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    candidate = runtime.remember(
        "Boundary candidate.",
        scope=scope,
        entity="delta-existing-boundary",
        source_path="30-context/projects/delta-existing.md",
        source_lineage=["adversarial-audit"],
    )["record"]
    cursor = runtime.delta_recall(scope=scope)["next_cursor"]
    runtime.approve(candidate["id"], scope=scope, decision_evidence="same record boundary")

    delta = runtime.delta_recall(scope=scope, cursor=cursor)
    assert [(event["record_id"], event["change"]) for event in delta["events"]] == [
        (candidate["id"], "modified")
    ]


def test_delta_cursor_rejects_malformed_opaque_payload(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    with pytest.raises(ValidationError, match="invalid delta cursor"):
        runtime.delta_recall(scope=scope, cursor="d1.not-valid-json")
    with pytest.raises(ValidationError, match="future"):
        runtime.delta_recall(scope=scope, cursor="2099-01-01T00:00:00Z")
    with pytest.raises(ValidationError, match="too large"):
        runtime.delta_recall(scope=scope, cursor="d1." + ("a" * 262_145))


def test_promotion_queue_recommends_router_destination_without_writing_layers(
    runtime: MemoryRuntime, scope: Scope, tmp_path: Path
) -> None:
    candidate = runtime.remember(
        "A reusable operating preference.",
        scope=scope,
        entity="promotion",
        kind="preference",
        source_path="00-inbox/operator-note.md",
        source_lineage=["operator"],
    )["record"]
    queued = runtime.queue_promotion(
        candidate["id"],
        scope=scope,
        decision_evidence="candidate extraction line 1",
    )
    assert queued["recommended_destination"].startswith("30-context/")
    assert queued["decision_evidence"] == "candidate extraction line 1"
    assert runtime.paths.promotion_queue.joinpath(f"{candidate['id']}.json").exists()
    assert not (tmp_path / "20-knowledge").exists()
    assert not (tmp_path / "30-context").exists()
    assert not (tmp_path / "40-memory").exists()
    assert not (tmp_path / "50-procedures").exists()


def test_holdout_evaluator_keeps_gold_sealed_from_runtime(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({"cases": [{"id": "q1", "query": "atlas"}]}), encoding="utf-8")
    prepared = HoldoutEvaluator.prepare_fixture(fixture)
    assert prepared == {"cases": [{"id": "q1", "query": "atlas"}]}
    leaked = tmp_path / "leaked.json"
    leaked.write_text(json.dumps({"cases": [], "gold": {"q1": "answer"}}), encoding="utf-8")
    with pytest.raises(ValidationError, match="sealed gold"):
        HoldoutEvaluator.prepare_fixture(leaked)

    result = tmp_path / "results" / "runtime" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text(json.dumps({"results": [{"id": "q1", "selected": ["mem_1"]}]}), encoding="utf-8")
    gold = tmp_path / "sealed-gold" / "evaluator" / "gold.json"
    gold.parent.mkdir(parents=True)
    gold.write_text(json.dumps({"q1": ["mem_1"]}), encoding="utf-8")
    score = HoldoutEvaluator.score_result(result, gold)
    assert score["exact_match_rate"] == 1.0
    assert "gold" not in result.read_text(encoding="utf-8")
    with pytest.raises(ValidationError, match="paths must be isolated"):
        HoldoutEvaluator.score_result(result, result)


def test_session_cursor_uses_full_identity_not_only_a_lossy_slug(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    remember_active(runtime, scope, "Atlas detail.", entity="atlas")
    first = runtime.context_pack(
        scope=scope,
        entity_terms=["atlas"],
        allowed_terms=["atlas"],
        session_id="session/a",
        deliver=True,
    )
    second = runtime.context_pack(
        scope=scope,
        entity_terms=["atlas"],
        allowed_terms=["atlas"],
        session_id="session a",
        deliver=True,
    )
    assert len(first["items"]) == 1
    assert len(second["items"]) == 1


def test_runtime_validation_rejects_schema_unknown_fields(
    runtime: MemoryRuntime, scope: Scope
) -> None:
    candidate = runtime.remember(
        "Schema drift.",
        scope=scope,
        entity="schema",
        source_path="30-context/projects/schema.md",
        source_lineage=["direct-read"],
    )["record"]
    path = runtime.record_path(candidate["id"])
    text = path.read_text(encoding="utf-8")
    payload_text = text.split("```json\n", 1)[1].split("\n```", 1)[0]
    payload = json.loads(payload_text)
    payload["unknown_field"] = "must fail"
    path.write_text(
        text.replace(payload_text, json.dumps(payload, sort_keys=True, indent=2)),
        encoding="utf-8",
    )
    assert str(path) in runtime.rebuild()["malformed_records"]


def test_metrics_surface_all_required_measurements() -> None:
    metrics = compute_metrics(
        [
            {
                "false_memory": False,
                "duplicate_injection": True,
                "conflict_exposed": False,
                "useful": True,
                "token_cost": 42,
                "latency_ms": 7.5,
                "manual_correction": False,
                "source_lineage_recovered": True,
            },
            {
                "false_memory": True,
                "duplicate_injection": False,
                "conflict_exposed": True,
                "useful": False,
                "token_cost": 10,
                "latency_ms": 2.5,
                "manual_correction": True,
                "source_lineage_recovered": False,
            },
        ]
    )
    assert metrics == {
        "false_memory_rate": 0.5,
        "duplicate_injection_rate": 0.5,
        "conflict_exposure_rate": 0.5,
        "usefulness_rate": 0.5,
        "token_cost": 52,
        "latency_ms": 5.0,
        "manual_correction_rate": 0.5,
        "source_lineage_recovery_rate": 0.5,
    }


def test_cli_json_workflow_and_nonzero_failure(tmp_path: Path) -> None:
    root = tmp_path / "cli-runtime"
    base = [
        sys.executable,
        "-m",
        "adapters.hermes.memory",
        "--root",
        str(root),
        "--source-id",
        "akm",
        "--project",
        "cli",
        "--profile",
        "default",
        "--user",
        "operator",
    ]
    remembered = subprocess.run(
        base
        + [
            "remember",
            "--text",
            "CLI memory candidate.",
            "--entity",
            "cli",
            "--source-path",
            "00-inbox/cli.md",
        ],
        check=True,
        cwd=Path(__file__).parents[4],
        capture_output=True,
        text=True,
    )
    record_id = json.loads(remembered.stdout)["record"]["id"]
    approved = subprocess.run(
        base + ["approve", "--id", record_id, "--decision-evidence", "cli-operator"],
        check=True,
        cwd=Path(__file__).parents[4],
        capture_output=True,
        text=True,
    )
    assert json.loads(approved.stdout)["record"]["state"] == "active"
    recalled = subprocess.run(
        base + ["recall", "--query", "candidate"],
        check=True,
        cwd=Path(__file__).parents[4],
        capture_output=True,
        text=True,
    )
    assert json.loads(recalled.stdout)["records"][0]["id"] == record_id
    state_override = subprocess.run(
        base + ["recall", "--include-state", "candidate", "--external-model"],
        check=False,
        cwd=Path(__file__).parents[4],
        capture_output=True,
        text=True,
    )
    assert state_override.returncode != 0
    assert "unrecognized arguments" in state_override.stderr
    failed = subprocess.run(
        base + ["forget", "--confirm", "invalid"],
        check=False,
        cwd=Path(__file__).parents[4],
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert json.loads(failed.stderr)["ok"] is False


def test_status_is_fail_closed_and_reports_hold(runtime: MemoryRuntime, scope: Scope) -> None:
    status = runtime.status(scope=scope)
    assert status["global_injection"] == "HOLD"
    assert status["canonical_authority"] == "AKM Markdown and original sources"
    assert status["counts"] == {}

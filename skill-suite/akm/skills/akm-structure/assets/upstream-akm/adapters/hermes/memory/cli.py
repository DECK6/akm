"""JSON CLI for exercising the AKM-native local memory runtime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .runtime import MemoryRuntime, MemoryRuntimeError, Scope


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m adapters.hermes.memory")
    parser.add_argument("--root", type=Path, required=True, help="local runtime root")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--project")
    parser.add_argument("--profile")
    parser.add_argument("--user")
    sub = parser.add_subparsers(dest="command", required=True)

    remember = sub.add_parser("remember")
    remember.add_argument("--text", required=True)
    remember.add_argument("--entity", required=True)
    remember.add_argument("--kind", default="fact")
    remember.add_argument("--visibility", default="non_sensitive")
    remember.add_argument("--egress-allowed", action="store_true")
    remember.add_argument("--ttl-seconds", type=int)
    remember.add_argument("--stable-authority", action="store_true")
    remember.add_argument("--source-path", required=True)
    remember.add_argument("--lineage", action="append", default=["operator-cli"])

    approve = sub.add_parser("approve")
    approve.add_argument("--id", required=True)
    approve.add_argument("--decision-evidence", required=True)

    reject = sub.add_parser("reject")
    reject.add_argument("--id", required=True)
    reject.add_argument("--decision-evidence", required=True)

    recall = sub.add_parser("recall")
    recall.add_argument("--query")
    recall.add_argument("--id")
    recall.add_argument("--external-model", action="store_true")
    recall.add_argument("--max-count", type=int, default=20)

    forget = sub.add_parser("forget")
    forget_mode = forget.add_mutually_exclusive_group(required=True)
    forget_mode.add_argument("--preview", action="store_true")
    forget_mode.add_argument("--confirm")
    forget.add_argument("--id", action="append")
    forget.add_argument("--all-in-scope", action="store_true")
    forget.add_argument("--reason", default="operator-request")

    restore = sub.add_parser("restore")
    restore.add_argument("--id", required=True)
    restore.add_argument("--decision-evidence", required=True)

    extract = sub.add_parser("extract")
    extract.add_argument("--input", required=True)
    extract.add_argument("--persist", action="store_true")

    provider = sub.add_parser("provider-outcome")
    provider.add_argument("--outcome", required=True)
    provider.add_argument("--payload-json")
    provider.add_argument("--persist", action="store_true")

    context = sub.add_parser("context-pack", aliases=["reflex"])
    context.add_argument("--entity-term", action="append", required=True)
    context.add_argument("--allowed-term", action="append", required=True)
    context.add_argument("--session-id", required=True)
    context.add_argument("--since")
    context.add_argument("--max-count", type=int, default=5)
    context.add_argument("--token-budget", type=int, default=400)
    context.add_argument("--external-model", action="store_true")
    context.add_argument("--deliver", action="store_true")

    delta = sub.add_parser("delta")
    delta.add_argument("--cursor")

    promote = sub.add_parser("promote")
    promote.add_argument("--id", required=True)
    promote.add_argument("--decision-evidence", required=True)

    sub.add_parser("status")
    sub.add_parser("rebuild")
    sub.add_parser("doctor")
    sub.add_parser("reconcile")
    return parser


def _scope(args: argparse.Namespace) -> Scope:
    return Scope(
        source_id=args.source_id,
        project=args.project,
        profile=args.profile,
        user=args.user,
    )


def _dispatch(runtime: MemoryRuntime, scope: Scope, args: argparse.Namespace) -> dict[str, Any]:
    command = args.command
    if command == "remember":
        return runtime.remember(
            args.text,
            scope=scope,
            entity=args.entity,
            kind=args.kind,
            visibility=args.visibility,
            egress_allowed=args.egress_allowed,
            ttl_seconds=args.ttl_seconds,
            stable_authority=args.stable_authority,
            source_path=args.source_path,
            source_lineage=args.lineage,
        )
    if command == "approve":
        return runtime.approve(args.id, scope=scope, decision_evidence=args.decision_evidence)
    if command == "reject":
        return runtime.reject(args.id, scope=scope, decision_evidence=args.decision_evidence)
    if command == "recall":
        return {
            "records": runtime.recall(
                scope=scope,
                query=args.query,
                record_id=args.id,
                external_model=args.external_model,
                max_count=args.max_count,
            )
        }
    if command == "forget":
        if args.preview:
            return runtime.forget_preview(
                scope=scope,
                record_ids=args.id,
                all_in_scope=args.all_in_scope,
                reason=args.reason,
            )
        return runtime.forget_confirm(args.confirm, scope=scope)
    if command == "restore":
        return runtime.restore_forgotten(
            args.id, scope=scope, decision_evidence=args.decision_evidence
        )
    if command == "extract":
        outcome = runtime.extract_local(args.input, scope=scope, persist=args.persist)
        return {"outcome": outcome.outcome, "candidates": outcome.candidates, "detail": outcome.detail}
    if command == "provider-outcome":
        payload = json.loads(args.payload_json) if args.payload_json else None
        outcome = runtime.ingest_provider_boundary(
            args.outcome, payload=payload, scope=scope, persist=args.persist
        )
        return {"outcome": outcome.outcome, "candidates": outcome.candidates, "detail": outcome.detail}
    if command in {"context-pack", "reflex"}:
        return runtime.context_pack(
            scope=scope,
            entity_terms=args.entity_term,
            allowed_terms=args.allowed_term,
            session_id=args.session_id,
            since=args.since,
            max_count=args.max_count,
            token_budget=args.token_budget,
            external_model=args.external_model,
            deliver=args.deliver,
        )
    if command == "delta":
        return runtime.delta_recall(scope=scope, cursor=args.cursor)
    if command == "promote":
        return runtime.queue_promotion(
            args.id, scope=scope, decision_evidence=args.decision_evidence
        )
    if command == "status":
        return runtime.status(scope=scope)
    if command == "rebuild":
        return runtime.rebuild()
    if command == "doctor":
        report = runtime.doctor()
        if not report["ok"]:
            raise MemoryRuntimeError("doctor found fail-closed issues: " + json.dumps(report, sort_keys=True))
        return report
    if command == "reconcile":
        return runtime.reconcile()
    raise MemoryRuntimeError(f"unknown command: {command}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        result = _dispatch(MemoryRuntime(args.root), _scope(args), args)
    except (MemoryRuntimeError, json.JSONDecodeError) as exc:
        payload = {"ok": False, "error": type(exc).__name__, "message": str(exc)}
        receipt_id = getattr(exc, "receipt_id", None)
        if receipt_id:
            payload["receipt_id"] = receipt_id
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0

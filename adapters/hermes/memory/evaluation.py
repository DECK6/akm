"""Sealed-gold evaluation boundary for the AKM memory runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .runtime import ValidationError


class HoldoutEvaluator:
    """Keep runtime fixtures/results separate from held-out answer material."""

    FORBIDDEN_FIXTURE_KEYS = {"gold", "answer", "answers", "expected", "expected_ids"}

    @classmethod
    def prepare_fixture(cls, fixture_path: str | Path) -> dict[str, Any]:
        fixture = cls._read_object(Path(fixture_path))
        cls._assert_no_gold(fixture, path="$")
        cases = fixture.get("cases")
        if not isinstance(cases, list):
            raise ValidationError("fixture cases must be a list")
        seen: set[str] = set()
        for index, case in enumerate(cases):
            if not isinstance(case, dict) or not isinstance(case.get("id"), str):
                raise ValidationError(f"fixture case {index} needs an id")
            if case["id"] in seen:
                raise ValidationError(f"duplicate fixture case id: {case['id']}")
            seen.add(case["id"])
        return fixture

    @classmethod
    def score_result(cls, result_path: str | Path, gold_path: str | Path) -> dict[str, Any]:
        result_file = Path(result_path).expanduser().resolve()
        gold_file = Path(gold_path).expanduser().resolve()
        if cls._paths_overlap(result_file, gold_file):
            raise ValidationError("runtime result and sealed gold paths must be isolated")
        result = cls._read_object(result_file)
        gold = cls._read_object(gold_file)
        rows = result.get("results")
        if not isinstance(rows, list):
            raise ValidationError("result rows must be a list")
        if "gold" in result:
            raise ValidationError("runtime result contains sealed gold")
        matched = 0
        scored = 0
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise ValidationError("result row needs an id")
            case_id = row["id"]
            if case_id in seen:
                raise ValidationError(f"duplicate result id: {case_id}")
            seen.add(case_id)
            if case_id not in gold:
                continue
            scored += 1
            expected = gold[case_id]
            selected = row.get("selected", [])
            if selected == expected:
                matched += 1
        return {
            "scored_cases": scored,
            "exact_matches": matched,
            "exact_match_rate": matched / scored if scored else None,
        }

    @staticmethod
    def _paths_overlap(left: Path, right: Path) -> bool:
        left_parent = left.parent
        right_parent = right.parent
        if left == right or left_parent == right_parent:
            return True
        try:
            return left_parent.is_relative_to(right_parent) or right_parent.is_relative_to(left_parent)
        except ValueError:
            return False

    @classmethod
    def _assert_no_gold(cls, value: Any, *, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.casefold() in cls.FORBIDDEN_FIXTURE_KEYS:
                    raise ValidationError(f"sealed gold key is forbidden in runtime fixture at {path}.{key}")
                cls._assert_no_gold(child, path=f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                cls._assert_no_gold(child, path=f"{path}[{index}]")

    @staticmethod
    def _read_object(path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(f"invalid evaluator JSON: {path}") from exc
        if not isinstance(value, dict):
            raise ValidationError(f"evaluator artifact must be an object: {path}")
        return value

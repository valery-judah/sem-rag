from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_CASES_DIR = REPO_ROOT / "evals" / "cases"
SETS_DIR = EVAL_CASES_DIR / "sets"
CASE_SCHEMA_PATH = EVAL_CASES_DIR / "cases.schema.json"
ANSWER_KEY_SCHEMA_PATH = EVAL_CASES_DIR / "answer_keys.schema.json"
SOURCE_DOC_PATH_RN1 = REPO_ROOT / "evals" / "corpus" / "research-notes-1.md"
SOURCE_DOC_PATH_RN2 = REPO_ROOT / "evals" / "corpus" / "research-notes-2.md"
LOOKUP_SET_NAME = "supported_lookup_research_1"
LOOKUP_CASE_IDS = {
    "lookup_rn1_001",
    "lookup_rn1_002",
    "lookup_rn1_003",
    "lookup_rn1_004",
    "lookup_rn1_005",
    "lookup_rn1_006",
    "lookup_rn1_007",
    "lookup_rn1_008",
}
NAV_SET_NAME = "supported_source_navigation"
NAV_CASE_IDS = {
    "nav_rn1_001",
    "nav_rn1_002",
    "nav_rn1_003",
    "nav_rn1_004",
    "nav_rn1_005",
    "nav_rn1_006",
    "nav_rn1_007",
    "nav_rn1_008",
    "nav_rn1_009",
    "nav_rn1_010",
}
PARTIAL_SUPPORT_RN1_SET_NAME = "partial_synthesis_research_1"
PARTIAL_SUPPORT_RN1_CASE_IDS = {f"psynth_rn1_{index:03d}" for index in range(1, 13)}
PARTIAL_SUPPORT_RN2_SET_NAME = "partial_support_synthesis_cases_rn2"
PARTIAL_SUPPORT_RN2_CASE_IDS = {f"psynth_rn2_{index:03d}" for index in range(1, 13)}
INGESTION_STRESS_RN3_SET_NAME = "ingestion_structure_stress_cases_rn3"
INGESTION_STRESS_RN3_CASE_IDS = {f"istruct_rn3_{index:03d}" for index in range(1, 13)}
INGESTION_STRESS_RN3_A1_SET_NAME = "ingestion_structure_stress_cases_rn3_a1_harder"
INGESTION_STRESS_RN3_A1_CASE_IDS = {f"istruct_rn3_a1_{index:03d}" for index in range(1, 9)}
RN2_SET_INVARIANTS: dict[str, dict[str, Any]] = {
    "ambiguous_conflicting_cases_rn2": {
        "expected_case_ids": {f"conflict_rn2_{index:03d}" for index in range(1, 5)},
        "case_family": "ambiguous_conflicting_evidence",
        "question_class": "ambiguous_conflict",
        "support_state": "AMBIGUOUS_OR_CONFLICTING",
        "expected_behavior": "surface_ambiguity_with_source_qualification",
        "abstention_expected": False,
        "primary_target_failures": ["A2", "U2", "P1"],
        "secondary_target_failures": ["P2"],
    },
    "supported_localized_explanation_cases_rn2": {
        "expected_case_ids": {f"lexp_rn2_{index:03d}" for index in range(1, 9)},
        "case_family": "supported_localized_explanation",
        "question_class": "localized_explanation",
        "support_state": "SUPPORTED",
        "expected_behavior": "direct_answer_with_section_citation",
        "abstention_expected": False,
        "primary_target_failures": ["U1", "P1", "P2"],
        "secondary_target_failures": ["A1"],
    },
    "unsupported_in_corpus_cases_rn2": {
        "expected_case_ids": {f"unsup_rn2_{index:03d}" for index in range(1, 13)},
        "case_family": "unsupported_in_corpus",
        "question_class": {"factual_lookup", "localized_explanation"},
        "support_state": "UNSUPPORTED_IN_CORPUS",
        "expected_behavior": "abstain_or_state_insufficient_support",
        "abstention_expected": True,
        "primary_target_failures": ["A2", "U1", "P2"],
        "secondary_target_failures": ["P1"],
    },
    "unsupported_question_type_cases_rn2": {
        "expected_case_ids": {f"uqt_rn2_{index:03d}" for index in range(1, 13)},
        "case_family": "unsupported_question_type",
        "question_class": "unsupported_scope",
        "support_state": "UNSUPPORTED_QUESTION_TYPE",
        "expected_behavior": "state_scope_limitation",
        "abstention_expected": True,
        "primary_target_failures": ["S1", "A2", "P2"],
        "secondary_target_failures": ["P1"],
    },
}
RN2_SET_NAMES = set(RN2_SET_INVARIANTS) | {PARTIAL_SUPPORT_RN2_SET_NAME}
ELLIPSIS_TOKENS = ("...", "…")
HEADING_RE = re.compile(r"^\d+(?:\.\d+)?\.? ")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _iter_case_set_dirs() -> list[Path]:
    return sorted(
        path
        for path in SETS_DIR.iterdir()
        if path.is_dir()
        and (path / "cases.jsonl").exists()
        and (path / "answer_keys.jsonl").exists()
    )


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise AssertionError(f"unsupported ref {ref}")
    node: Any = root_schema
    for part in ref[2:].split("/"):
        node = node[part]
    if not isinstance(node, dict):
        raise AssertionError(f"ref {ref} did not resolve to an object schema")
    return node


def _validate_json_schema(
    instance: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any] | None = None,
    path: str = "$",
) -> None:
    root = root_schema or schema
    if "$ref" in schema:
        _validate_json_schema(instance, _resolve_ref(root, schema["$ref"]), root, path)
        return

    if "oneOf" in schema:
        matches = 0
        last_error: AssertionError | None = None
        for option in schema["oneOf"]:
            try:
                _validate_json_schema(instance, option, root, path)
            except AssertionError as exc:
                last_error = exc
            else:
                matches += 1
        if matches != 1:
            detail = f": {last_error}" if last_error is not None else ""
            raise AssertionError(f"{path}: expected exactly one oneOf match{detail}")
        return

    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                _validate_json_schema(instance, option, root, path)
            except AssertionError:
                continue
            break
        else:
            raise AssertionError(f"{path}: expected at least one anyOf match")

    if "const" in schema and instance != schema["const"]:
        raise AssertionError(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        raise AssertionError(f"{path}: expected one of {schema['enum']!r}, got {instance!r}")

    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(instance, dict):
            raise AssertionError(f"{path}: expected object, got {type(instance).__name__}")
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise AssertionError(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra_keys = set(instance) - set(properties)
            if extra_keys:
                raise AssertionError(f"{path}: unexpected properties {sorted(extra_keys)!r}")
        for key, value in instance.items():
            if key in properties:
                _validate_json_schema(value, properties[key], root, f"{path}.{key}")
        return

    if schema_type == "array":
        if not isinstance(instance, list):
            raise AssertionError(f"{path}: expected array, got {type(instance).__name__}")
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise AssertionError(f"{path}: expected at least {schema['minItems']} items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            raise AssertionError(f"{path}: expected at most {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True) for item in instance]
            if len(encoded) != len(set(encoded)):
                raise AssertionError(f"{path}: expected unique items")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, value in enumerate(instance):
                _validate_json_schema(value, item_schema, root, f"{path}[{index}]")
        return

    if schema_type == "string":
        if not isinstance(instance, str):
            raise AssertionError(f"{path}: expected string, got {type(instance).__name__}")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise AssertionError(f"{path}: expected minLength {schema['minLength']}")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, instance) is None:
            raise AssertionError(f"{path}: value {instance!r} did not match {pattern!r}")
        return

    if schema_type == "boolean" and not isinstance(instance, bool):
        raise AssertionError(f"{path}: expected boolean, got {type(instance).__name__}")

    if schema_type == "integer" and (not isinstance(instance, int) or isinstance(instance, bool)):
        raise AssertionError(f"{path}: expected integer, got {type(instance).__name__}")


def _parse_sections(markdown_path: Path) -> dict[tuple[str, ...], str]:
    sections: dict[tuple[str, ...], str] = {}
    stack: list[tuple[int, str]] = []
    current_path: tuple[str, ...] | None = None
    current_lines: list[str] = []
    preamble_lines: list[str] = []
    heading_pattern = re.compile(r"^(#{2,6}) (.+)$")

    for line in markdown_path.read_text().splitlines():
        match = heading_pattern.match(line)
        if match is None:
            if current_path is not None:
                current_lines.append(line)
            else:
                preamble_lines.append(line)
            continue

        if current_path is not None:
            sections[current_path] = "\n".join(current_lines).strip()

        heading_level = len(match.group(1))
        heading_text = match.group(2)
        while stack and stack[-1][0] >= heading_level:
            stack.pop()
        stack.append((heading_level, heading_text))
        current_path = tuple(title for _, title in stack)
        current_lines = preamble_lines[:] if not sections else []

    if current_path is not None:
        sections[current_path] = "\n".join(current_lines).strip()

    return sections


def _canonical_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(value)
    return str(value)


def _has_localizer(source: dict[str, Any]) -> bool:
    return any(source.get(field) for field in ("section_path", "page_start", "section_anchor"))


def _normalize_locator(source: dict[str, Any]) -> tuple[Any, ...]:
    section_path = tuple(source.get("section_path", []))
    return (
        source["doc_id"],
        source["display_name"],
        section_path,
        source.get("page_start"),
        source.get("page_end"),
        source.get("section_anchor"),
    )


def _load_set(set_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases = _load_jsonl(set_dir / "cases.jsonl")
    answer_keys = _load_jsonl(set_dir / "answer_keys.jsonl")
    return cases, answer_keys


def _assert_section_grounded_source(
    source: dict[str, Any],
    sections: dict[tuple[str, ...], str],
    *,
    expect_snippet: bool,
) -> None:
    section_path = tuple(source["section_path"])
    assert section_path in sections
    if expect_snippet:
        support_snippet = source["support_snippet"]
        assert not any(token in support_snippet for token in ELLIPSIS_TOKENS)
        assert support_snippet in sections[section_path]


def _validate_research_notes_set(
    *,
    set_name: str,
    expected_case_ids: set[str],
    question_class: str,
    expected_behavior: str,
    expected_secondary_failures: list[str],
    expected_user_intent_note: str,
) -> None:
    cases, answer_keys = _load_set(SETS_DIR / set_name)
    sections = _parse_sections(SOURCE_DOC_PATH_RN1)
    answer_keys_by_id = {row["case_id"]: row for row in answer_keys}

    case_ids = [row["case_id"] for row in cases]
    answer_key_ids = [row["case_id"] for row in answer_keys]
    assert set(case_ids) == expected_case_ids
    assert set(answer_key_ids) == expected_case_ids
    assert case_ids == sorted(case_ids)
    assert answer_key_ids == sorted(answer_key_ids)

    for case in cases:
        assert case["corpus_id"] == "research-notes-1"
        assert case["source_type"] == "markdown"
        assert case["primary_target_failures"] == ["A1", "P1", "P2"]
        assert case["secondary_target_failures"] == expected_secondary_failures

        question_spec = case["question_spec"]
        assert question_spec["question_class"] == question_class
        assert question_spec["support_state"] == "SUPPORTED"
        assert question_spec["minimum_provenance"] == "document_and_section"
        assert question_spec["user_intent_note"] == expected_user_intent_note
        assert len(question_spec["gold_sources"]) == 1

        gold_source = question_spec["gold_sources"][0]
        assert gold_source["doc_id"] == "research-notes-1"
        assert len(gold_source["section_path"]) == 2
        _assert_section_grounded_source(gold_source, sections, expect_snippet=False)

        answer_key = answer_keys_by_id[case["case_id"]]
        assert answer_key["expected_behavior"] == expected_behavior
        assert answer_key["abstention_expected"] is False
        assert len(answer_key["gold_evidence_set"]) == 1
        assert answer_key["must_include"]
        assert answer_key["must_not_include"]

        evidence = answer_key["gold_evidence_set"][0]
        assert evidence["doc_id"] == "research-notes-1"
        assert evidence["section_path"] == gold_source["section_path"]
        _assert_section_grounded_source(evidence, sections, expect_snippet=True)

        canonical_text = _canonical_text(answer_key["canonical_answer"]).lower()
        for needle in answer_key["must_include"]:
            assert needle.lower() in canonical_text
        for distractor in answer_key["must_not_include"]:
            assert distractor.lower() not in canonical_text


def _validate_rn2_set(set_name: str, invariant: dict[str, Any]) -> None:
    cases, answer_keys = _load_set(SETS_DIR / set_name)
    sections = _parse_sections(SOURCE_DOC_PATH_RN2)
    answer_keys_by_id = {row["case_id"]: row for row in answer_keys}

    case_ids = [row["case_id"] for row in cases]
    answer_key_ids = [row["case_id"] for row in answer_keys]
    assert set(case_ids) == invariant["expected_case_ids"]
    assert set(answer_key_ids) == invariant["expected_case_ids"]
    assert case_ids == sorted(case_ids)
    assert answer_key_ids == sorted(answer_key_ids)

    for case in cases:
        assert case["corpus_id"] == "research-notes-2"
        assert case["source_type"] == "markdown"
        assert case["case_family"] == invariant["case_family"]
        assert case["primary_target_failures"] == invariant["primary_target_failures"]
        assert case["secondary_target_failures"] == invariant["secondary_target_failures"]

        question_spec = case["question_spec"]
        expected_question_class = invariant["question_class"]
        if isinstance(expected_question_class, set):
            assert question_spec["question_class"] in expected_question_class
        else:
            assert question_spec["question_class"] == expected_question_class
        assert question_spec["support_state"] == invariant["support_state"]
        assert question_spec["minimum_provenance"] == "document_and_section"
        for source in question_spec["gold_sources"]:
            assert "support_snippet" not in source
            assert source["doc_id"] == "research-notes-2"
            _assert_section_grounded_source(source, sections, expect_snippet=False)

        answer_key = answer_keys_by_id[case["case_id"]]
        assert answer_key["expected_behavior"] == invariant["expected_behavior"]
        assert answer_key["abstention_expected"] is invariant["abstention_expected"]
        for source in answer_key["gold_evidence_set"]:
            assert source["doc_id"] == "research-notes-2"
            _assert_section_grounded_source(source, sections, expect_snippet=True)


def _validate_partial_support_rn2_set() -> None:
    cases, answer_keys = _load_set(SETS_DIR / PARTIAL_SUPPORT_RN2_SET_NAME)
    sections = _parse_sections(SOURCE_DOC_PATH_RN2)
    answer_keys_by_id = {row["case_id"]: row for row in answer_keys}

    case_ids = [row["case_id"] for row in cases]
    answer_key_ids = [row["case_id"] for row in answer_keys]
    assert set(case_ids) == PARTIAL_SUPPORT_RN2_CASE_IDS
    assert set(answer_key_ids) == PARTIAL_SUPPORT_RN2_CASE_IDS
    assert case_ids == sorted(case_ids)
    assert answer_key_ids == sorted(answer_key_ids)

    for case in cases:
        assert case["corpus_id"] == "research-notes-2"
        assert case["source_type"] == "markdown"
        assert case["case_family"] == "partial_support_answer"
        assert case["primary_target_failures"] == ["U2", "P1", "P2"]
        assert case["secondary_target_failures"] == ["A1"]

        question_spec = case["question_spec"]
        assert question_spec["question_class"] == "multi_source_synthesis"
        assert question_spec["support_state"] == "PARTIALLY_SUPPORTED"
        assert question_spec["minimum_provenance"] == "document_and_section"
        for source in question_spec["gold_sources"]:
            assert "support_snippet" not in source
            assert source["doc_id"] == "research-notes-2"
            _assert_section_grounded_source(source, sections, expect_snippet=False)

        answer_key = answer_keys_by_id[case["case_id"]]
        assert answer_key["expected_behavior"] == "qualified_answer_with_citation"
        assert answer_key["abstention_expected"] is False
        for source in answer_key["gold_evidence_set"]:
            assert source["doc_id"] == "research-notes-2"
            _assert_section_grounded_source(source, sections, expect_snippet=True)


def _validate_partial_support_rn1_set() -> None:
    cases, answer_keys = _load_set(SETS_DIR / PARTIAL_SUPPORT_RN1_SET_NAME)
    sections = _parse_sections(SOURCE_DOC_PATH_RN1)
    answer_keys_by_id = {row["case_id"]: row for row in answer_keys}

    case_ids = [row["case_id"] for row in cases]
    answer_key_ids = [row["case_id"] for row in answer_keys]
    assert set(case_ids) == PARTIAL_SUPPORT_RN1_CASE_IDS
    assert set(answer_key_ids) == PARTIAL_SUPPORT_RN1_CASE_IDS
    assert case_ids == sorted(case_ids)
    assert answer_key_ids == sorted(answer_key_ids)

    for case in cases:
        assert case["corpus_id"] == "research-notes-1"
        assert case["source_type"] == "markdown"
        assert case["case_family"] == "partial_support_answer"
        assert case["primary_target_failures"] == ["U2", "P1", "P2"]
        assert case["secondary_target_failures"] == ["A1"]

        question_spec = case["question_spec"]
        assert question_spec["question_class"] == "multi_source_synthesis"
        assert question_spec["support_state"] == "PARTIALLY_SUPPORTED"
        assert question_spec["minimum_provenance"] == "document_and_section"
        assert (
            question_spec["user_intent_note"]
            == "Broader synthesis request; the corpus supports only a qualified or narrowed answer."
        )
        for source in question_spec["gold_sources"]:
            assert "support_snippet" not in source
            assert source["doc_id"] == "research-notes-1"
            _assert_section_grounded_source(source, sections, expect_snippet=False)

        answer_key = answer_keys_by_id[case["case_id"]]
        assert answer_key["expected_behavior"] == "qualified_answer_with_citation"
        assert answer_key["abstention_expected"] is False
        for source in answer_key["gold_evidence_set"]:
            assert source["doc_id"] == "research-notes-1"
            _assert_section_grounded_source(source, sections, expect_snippet=True)


def _validate_ingestion_structure_stress_rn3_set(
    *,
    set_name: str,
    expected_case_ids: set[str],
    expected_primary_failures: list[str] | None = None,
    expected_secondary_failures: list[str] | None = None,
    allowed_primary_failures: set[tuple[str, ...]] | None = None,
    allowed_secondary_failures: set[tuple[str, ...]] | None = None,
) -> None:
    cases, answer_keys = _load_set(SETS_DIR / set_name)
    sections = _parse_sections(REPO_ROOT / "evals" / "corpus" / "research-notes-3.md")
    answer_keys_by_id = {row["case_id"]: row for row in answer_keys}

    case_ids = [row["case_id"] for row in cases]
    answer_key_ids = [row["case_id"] for row in answer_keys]
    assert set(case_ids) == expected_case_ids
    assert set(answer_key_ids) == expected_case_ids
    assert case_ids == sorted(case_ids)
    assert answer_key_ids == sorted(answer_key_ids)

    for case in cases:
        assert case["corpus_id"] == "research-notes-3"
        assert case["source_type"] == "markdown"
        assert case["case_family"] == "ingestion_structure_stress"

        if expected_primary_failures is not None:
            assert case["primary_target_failures"] == expected_primary_failures
        if expected_secondary_failures is not None:
            assert case["secondary_target_failures"] == expected_secondary_failures
        if allowed_primary_failures is not None:
            assert tuple(case["primary_target_failures"]) in allowed_primary_failures
        if allowed_secondary_failures is not None:
            assert tuple(case["secondary_target_failures"]) in allowed_secondary_failures

        question_spec = case["question_spec"]
        assert question_spec["question_class"] in {"factual_lookup", "source_navigation"}
        assert question_spec["support_state"] == "SUPPORTED"
        assert question_spec["minimum_provenance"] == "document_and_section"
        assert question_spec["user_intent_note"]
        for source in question_spec["gold_sources"]:
            assert "support_snippet" not in source
            assert source["doc_id"] == "research-notes-3"
            _assert_section_grounded_source(source, sections, expect_snippet=False)

        answer_key = answer_keys_by_id[case["case_id"]]
        expected_behavior = (
            "direct_navigation_with_section_citation"
            if question_spec["question_class"] == "source_navigation"
            else "direct_answer_with_section_citation"
        )
        assert answer_key["expected_behavior"] == expected_behavior
        assert answer_key["abstention_expected"] is False
        assert answer_key["must_include"]
        assert answer_key["must_not_include"]
        for source in answer_key["gold_evidence_set"]:
            assert source["doc_id"] == "research-notes-3"
            _assert_section_grounded_source(source, sections, expect_snippet=True)


def test_all_eval_case_sets_validate_against_shared_schemas() -> None:
    case_schema = json.loads(CASE_SCHEMA_PATH.read_text())
    answer_key_schema = json.loads(ANSWER_KEY_SCHEMA_PATH.read_text())
    set_dirs = _iter_case_set_dirs()

    assert {path.name for path in set_dirs} >= {
        LOOKUP_SET_NAME,
        NAV_SET_NAME,
        PARTIAL_SUPPORT_RN1_SET_NAME,
        INGESTION_STRESS_RN3_SET_NAME,
        INGESTION_STRESS_RN3_A1_SET_NAME,
        *RN2_SET_NAMES,
    }

    for set_dir in set_dirs:
        cases, answer_keys = _load_set(set_dir)
        assert cases, f"{set_dir.name} has no cases"
        assert answer_keys, f"{set_dir.name} has no answer keys"

        case_ids = [row["case_id"] for row in cases]
        answer_key_ids = [row["case_id"] for row in answer_keys]
        assert len(case_ids) == len(set(case_ids))
        assert len(answer_key_ids) == len(set(answer_key_ids))
        assert set(case_ids) == set(answer_key_ids)

        cases_by_id = {row["case_id"]: row for row in cases}

        for case in cases:
            _validate_json_schema(case, case_schema)
            assert case["question_spec"]["gold_sources"]
            for source in case["question_spec"]["gold_sources"]:
                assert _has_localizer(source)

        for answer_key in answer_keys:
            _validate_json_schema(answer_key, answer_key_schema)
            case = cases_by_id[answer_key["case_id"]]
            case_sources = {
                _normalize_locator(source) for source in case["question_spec"]["gold_sources"]
            }
            answer_sources = {
                _normalize_locator(source) for source in answer_key["gold_evidence_set"]
            }
            assert case_sources == answer_sources
            for source in answer_key["gold_evidence_set"]:
                assert _has_localizer(source)


def test_supported_lookup_research_1_grounding() -> None:
    _validate_research_notes_set(
        set_name=LOOKUP_SET_NAME,
        expected_case_ids=LOOKUP_CASE_IDS,
        question_class="factual_lookup",
        expected_behavior="direct_answer_with_section_citation",
        expected_secondary_failures=["U1"],
        expected_user_intent_note="Direct fact lookup, not synthesis.",
    )


def test_supported_source_navigation_grounding() -> None:
    _validate_research_notes_set(
        set_name=NAV_SET_NAME,
        expected_case_ids=NAV_CASE_IDS,
        question_class="source_navigation",
        expected_behavior="direct_navigation_with_section_citation",
        expected_secondary_failures=[],
        expected_user_intent_note=(
            "User mainly needs the right location in the corpus, not a synthesized content answer."
        ),
    )

    _, answer_keys = _load_set(SETS_DIR / NAV_SET_NAME)
    for answer_key in answer_keys:
        for distractor in answer_key["must_not_include"]:
            assert HEADING_RE.match(distractor), distractor


def test_partial_support_synthesis_cases_rn2_grounding() -> None:
    _validate_partial_support_rn2_set()


def test_partial_synthesis_research_1_grounding() -> None:
    _validate_partial_support_rn1_set()


def test_ingestion_structure_stress_cases_rn3_grounding() -> None:
    _validate_ingestion_structure_stress_rn3_set(
        set_name=INGESTION_STRESS_RN3_SET_NAME,
        expected_case_ids=INGESTION_STRESS_RN3_CASE_IDS,
        expected_primary_failures=["I1", "P1", "P2"],
        expected_secondary_failures=["A1"],
    )


def test_ingestion_structure_stress_cases_rn3_a1_harder_grounding() -> None:
    _validate_ingestion_structure_stress_rn3_set(
        set_name=INGESTION_STRESS_RN3_A1_SET_NAME,
        expected_case_ids=INGESTION_STRESS_RN3_A1_CASE_IDS,
        allowed_primary_failures={
            ("A1", "I1", "P1"),
            ("A1", "I1"),
        },
        allowed_secondary_failures={
            ("P2",),
            ("P1", "P2"),
            ("P1",),
        },
    )


def test_rn2_matrix_slice_grounding_and_invariants() -> None:
    for set_name, invariant in RN2_SET_INVARIANTS.items():
        _validate_rn2_set(set_name, invariant)

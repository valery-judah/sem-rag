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
SOURCE_DOC_PATH = REPO_ROOT / "evals" / "corpus" / "research-notes-1.md"
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
    heading_pattern = re.compile(r"^(#{2,6}) (.+)$")

    for line in markdown_path.read_text().splitlines():
        match = heading_pattern.match(line)
        if match is None:
            if current_path is not None:
                current_lines.append(line)
            continue

        if current_path is not None:
            sections[current_path] = "\n".join(current_lines).strip()

        heading_level = len(match.group(1))
        heading_text = match.group(2)
        while stack and stack[-1][0] >= heading_level:
            stack.pop()
        stack.append((heading_level, heading_text))
        current_path = tuple(title for _, title in stack)
        current_lines = []

    if current_path is not None:
        sections[current_path] = "\n".join(current_lines).strip()

    return sections


def _canonical_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(value)
    return str(value)


def _has_localizer(source: dict[str, Any]) -> bool:
    return any(
        source.get(field)
        for field in ("section_path", "page_start", "section_anchor")
    )


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
    sections = _parse_sections(SOURCE_DOC_PATH)
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
        section_path = tuple(gold_source["section_path"])
        assert section_path in sections

        answer_key = answer_keys_by_id[case["case_id"]]
        assert answer_key["expected_behavior"] == expected_behavior
        assert answer_key["abstention_expected"] is False
        assert len(answer_key["gold_evidence_set"]) == 1
        assert answer_key["must_include"]
        assert answer_key["must_not_include"]

        evidence = answer_key["gold_evidence_set"][0]
        assert evidence["doc_id"] == "research-notes-1"
        assert evidence["section_path"] == gold_source["section_path"]
        assert evidence["support_snippet"] in sections[section_path]

        canonical_text = _canonical_text(answer_key["canonical_answer"]).lower()
        for needle in answer_key["must_include"]:
            assert needle.lower() in canonical_text
        for distractor in answer_key["must_not_include"]:
            assert distractor.lower() not in canonical_text


def test_all_eval_case_sets_validate_against_shared_schemas() -> None:
    case_schema = json.loads(CASE_SCHEMA_PATH.read_text())
    answer_key_schema = json.loads(ANSWER_KEY_SCHEMA_PATH.read_text())
    set_dirs = _iter_case_set_dirs()

    assert {path.name for path in set_dirs} >= {LOOKUP_SET_NAME, NAV_SET_NAME}

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

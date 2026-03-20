from typing import Annotated, NewType

from pydantic import AfterValidator, Field

from doc_forge.identifiers import validate_identifier

_CorpusId = NewType("_CorpusId", str)


def validate_corpus_id(value: str) -> _CorpusId:
    return _CorpusId(
        validate_identifier(
            value,
            field_name="corpus_id",
            reject_dot_segments=True,
        )
    )


CorpusId = Annotated[_CorpusId, Field(min_length=1), AfterValidator(validate_corpus_id)]


def parse_corpus_id(value: str) -> _CorpusId:
    return validate_corpus_id(value)

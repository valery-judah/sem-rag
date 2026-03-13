from __future__ import annotations

from e2e.runtime_defaults import resolve_e2e_answer_generator


def test_e2e_defaults_use_host_ollama_on_apple_silicon() -> None:
    selection = resolve_e2e_answer_generator(
        {},
        system="Darwin",
        machine="arm64",
        host_ollama_ready=True,
    )

    assert selection.environment["DOC_FORGE_ANSWER_GENERATOR_BACKEND"] == "ollama"
    assert selection.environment["DOC_FORGE_ANSWER_GENERATOR_MODEL"] == "llama3.2:1b"
    assert selection.environment["OLLAMA_BASE_URL"] == "http://host.docker.internal:11434"


def test_e2e_defaults_stay_deterministic_on_non_apple_hosts() -> None:
    selection = resolve_e2e_answer_generator(
        {},
        system="Linux",
        machine="x86_64",
        host_ollama_ready=True,
    )

    assert selection.environment == {
        "DOC_FORGE_ANSWER_GENERATOR_BACKEND": "deterministic",
    }

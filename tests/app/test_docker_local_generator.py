from __future__ import annotations

from doc_forge.devtools.docker_local_generator import (
    DEFAULT_HOST_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    format_shell_env,
    resolve_docker_local_generator,
)


def test_resolver_uses_host_ollama_on_apple_silicon_when_available() -> None:
    selection = resolve_docker_local_generator(
        {},
        system="Darwin",
        machine="arm64",
        host_ollama_ready=True,
    )

    assert selection.backend == "ollama"
    assert selection.reason == "apple_silicon_host_ollama"
    assert selection.using_host_ollama is True
    assert selection.environment == {
        "DOC_FORGE_ANSWER_GENERATOR_BACKEND": "ollama",
        "DOC_FORGE_ANSWER_GENERATOR_MODEL": DEFAULT_OLLAMA_MODEL,
        "OLLAMA_BASE_URL": DEFAULT_HOST_OLLAMA_BASE_URL,
    }


def test_resolver_falls_back_to_deterministic_when_host_ollama_is_unavailable() -> None:
    selection = resolve_docker_local_generator(
        {},
        system="Darwin",
        machine="arm64",
        host_ollama_ready=False,
    )

    assert selection.backend == "deterministic"
    assert selection.reason == "deterministic_host_ollama_unavailable"
    assert selection.environment == {
        "DOC_FORGE_ANSWER_GENERATOR_BACKEND": "deterministic",
    }


def test_resolver_keeps_non_apple_hosts_deterministic_by_default() -> None:
    selection = resolve_docker_local_generator(
        {},
        system="Linux",
        machine="x86_64",
        host_ollama_ready=True,
    )

    assert selection.backend == "deterministic"
    assert selection.reason == "deterministic_non_apple_host"
    assert selection.environment == {
        "DOC_FORGE_ANSWER_GENERATOR_BACKEND": "deterministic",
    }


def test_resolver_preserves_explicit_backend_model_and_base_url() -> None:
    selection = resolve_docker_local_generator(
        {
            "DOC_FORGE_ANSWER_GENERATOR_BACKEND": "ollama",
            "DOC_FORGE_ANSWER_GENERATOR_MODEL": "llama3.2:3b",
            "OLLAMA_BASE_URL": "http://example.test:11434",
        },
        system="Darwin",
        machine="arm64",
        host_ollama_ready=False,
    )

    assert selection.backend == "ollama"
    assert selection.reason == "explicit_backend"
    assert selection.environment == {
        "DOC_FORGE_ANSWER_GENERATOR_BACKEND": "ollama",
        "DOC_FORGE_ANSWER_GENERATOR_MODEL": "llama3.2:3b",
        "OLLAMA_BASE_URL": "http://example.test:11434",
    }


def test_shell_formatter_unsets_unused_values_for_deterministic_fallback() -> None:
    rendered = format_shell_env(
        resolve_docker_local_generator(
            {},
            system="Linux",
            machine="x86_64",
            host_ollama_ready=False,
        )
    )

    assert rendered.splitlines() == [
        "export DOC_FORGE_ANSWER_GENERATOR_BACKEND=deterministic",
        "unset DOC_FORGE_ANSWER_GENERATOR_MODEL",
        "unset OLLAMA_BASE_URL",
    ]

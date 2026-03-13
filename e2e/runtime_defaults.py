from __future__ import annotations

from collections.abc import Mapping

from doc_forge.devtools.docker_local_generator import (
    DockerLocalGeneratorSelection,
    resolve_docker_local_generator,
)


def resolve_e2e_answer_generator(
    environ: Mapping[str, str] | None = None,
    *,
    system: str | None = None,
    machine: str | None = None,
    host_ollama_ready: bool | None = None,
) -> DockerLocalGeneratorSelection:
    return resolve_docker_local_generator(
        environ,
        system=system,
        machine=machine,
        host_ollama_ready=host_ollama_ready,
    )

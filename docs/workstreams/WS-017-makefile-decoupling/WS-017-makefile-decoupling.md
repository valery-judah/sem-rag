# WS-017: Makefile Decoupling

## Objective
Decouple Python-related tasks from the `Makefile` to a more Python-native solution, reserving the `Makefile` strictly for local DevEx operations (e.g., Docker, Docker Compose, observability stack).

## Reasoning
The project relies heavily on `uv` for Python dependency management and tool execution. While `Make` is excellent for orchestrating system-level and container-based commands, relying on it for Python-specific workflows (like linting, formatting, and testing) creates unnecessary friction and an inconsistent developer experience. 

By migrating Python tasks to a Python-native task runner, we achieve:
1. Better integration with our Python toolchain (`uv`).
2. A clearer separation of concerns between application lifecycle commands and infrastructure/environment commands.
3. Cross-platform compatibility for Python tasks without depending on system-level `make`.

We selected **`poethepoet`** as our task runner. It integrates seamlessly with `uv` and `pyproject.toml`, providing a clean, TOML-based configuration for defining project-specific tasks.

## Work Log

### Iteration 1: Initial Migration to `poethepoet`
- Introduced `poethepoet` as the Python task runner.
- Migrated all Python-centric commands (`fmt`, `lint`, `test`, `migrate`, etc.) from the `Makefile` into the `[tool.poe.tasks]` section of `pyproject.toml`.
- Stripped the `Makefile` down to focus exclusively on local DevEx commands such as `docker-up` and `observability-up`.
- Updated all canonical documentation (`AGENTS.md`, `README.md`, and `docs/evergreen/*`) to reflect the new command structure, standardizing on `uv run poe <task>`.

### Iteration 2: Configuration Isolation
To prevent `pyproject.toml` from becoming bloated and to further enforce separation of concerns, we extracted the task definitions into a standalone file.
- Created `poe_tasks.toml` to house all task configurations using the `[tasks.<name>]` syntax.
- Updated `pyproject.toml` to act primarily as the source of truth for packaging metadata, dependencies, and tool configuration.
- Retained the Poe environment settings (`envfile = ".env"`) within `pyproject.toml` but delegated the task definitions by adding `include = ["poe_tasks.toml"]` under the `[tool.poe]` section.

## Conclusion and Current State
We have successfully established a clean, three-tiered separation of concerns for our project operations:

1. **`pyproject.toml`**: Dedicated to packaging metadata, Python dependencies, and global tool configurations.
2. **`poe_tasks.toml`**: Dedicated to Python developer tasks and scripts (`fmt`, `lint`, `test`, etc.), run via `uv run poe <task>`.
3. **`Makefile`**: Dedicated to system-level, Docker, and DevEx wrappers (`docker-up`, `observability-up`, etc.).

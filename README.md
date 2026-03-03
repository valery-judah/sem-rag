# <PROJECT_NAME>

One-line description of what this project does.

## Requirements
- Python 3.11+
- `uv` (recommended)

## Quickstart
```bash
make init
make test
```

## Run
```bash
make run
```

## Development
Common commands (see `Makefile` for the full list):

```bash
make fmt     # auto-format and fix
make lint    # formatting + lint checks
make type    # mypy
make test    # pytest
make check   # fmt + lint + type + test
```

## Dependencies
- Add a runtime dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`
- Sync lockfile + env: `make sync`
- Template check (adds a small runtime dep): `make add-rich`

## Project layout
```text
src/<package_name>/
tests/
docs/
```

## Configuration
- Packaging/config: `pyproject.toml`
- Tooling: `ruff`, `mypy`, `pytest` (configured in `pyproject.toml`)

## Contributing
See `CONTRIBUTING.md`.

## Security
See `SECURITY.md`.

## License
Add a `LICENSE` file (MIT/Apache-2.0/BSD-3-Clause/etc.) and update this section.

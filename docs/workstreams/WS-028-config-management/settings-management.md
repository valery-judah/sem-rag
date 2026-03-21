Yes. With a **Docker-first** startup path and a **12-factor / cloud-native** direction, I would narrow the choice quite a bit.

The core distinction is:

* **the app’s config contract**: what the code reads and validates
* **the deployment transport**: how values get into the container

For a FastAPI service, the strongest default is:

* **contract**: `pydantic-settings`
* **transport**:

  * local dev: shell env, `docker run --env-file`, or Compose `environment` / `env_file`
  * cloud/Kubernetes: ConfigMaps for non-secret config, Secrets or secret files for sensitive config

That aligns with FastAPI’s documented settings pattern, Pydantic Settings’ support for env vars and secrets files, and the 12-factor recommendation to store config in environment variables rather than app-specific config files. ([FastAPI][1])

## What changes when Docker becomes the normal way to start the app

Once the container is the standard runtime, the application should stop thinking in terms of “load config from wherever is convenient” and instead think in terms of “read a typed config object from externally injected values”. That is the 12-factor model: config is outside the code, usually exposed as environment variables, and it should vary per deploy without rebuilding the image. Kubernetes ConfigMaps exist for exactly this decoupling of environment-specific config from container images. ([12factor.net][2])

So the design target becomes:

* build **one image**
* inject config per environment
* validate config at startup
* fail fast on invalid or missing required values

That is where `pydantic-settings` fits well: it gives you a typed schema, validation, env-prefix support, dotenv support for local use, and secrets-file support for containerized deployments. ([Pydantic][3])

## What I would recommend for your case

### 1. Preferred default: `pydantic-settings`

This is still the best fit. FastAPI explicitly recommends Pydantic Settings for app settings, including `.env` support and cached dependency usage; Pydantic Settings supports environment variables, dotenv files, prefixes, and secrets directories such as `/run/secrets`. ([FastAPI][1])

Why it matches your direction:

* typed settings model
* startup validation
* compatible with env-var based deployment
* supports secret files for Docker/K8s style setups
* easy to test by passing a `Settings(...)` object directly

### 2. Simpler alternative: `starlette.config`

If you want less machinery and fewer features, `starlette.config` is a credible minimal option. Starlette’s docs explicitly frame it as 12-factor-oriented and based on env vars / `.env`. It is good when you want simple casting and secrets but do not want a full Pydantic settings model. ([Starlette][4])

I would use this only if the config surface stays small.

### 3. Heavier options only if config composition becomes a real problem

* **Dynaconf**: useful when you want layered settings files, multiple formats, and more elaborate source-merging behavior. ([Dynaconf][5])
* **ConfZ**: Pydantic-based and supports config files, env vars, and CLI inputs; reasonable if you want more source-management features than plain `pydantic-settings`. ([ConfZ][6])
* **Hydra/OmegaConf**: good for hierarchical config composition and CLI override workflows, but usually a mismatch for a normal API service unless the service is also a complex job runner or ML-style application. ([Hydra][7])

For a cloud-native FastAPI API, I would not start with these.

## The 12-factor nuance that matters here

A common mistake is to interpret 12-factor as “have one `ENVIRONMENT=dev|test|prod` variable and branch everything off it”. The 12-factor config page explicitly argues against grouping config into named environments as the main model; instead, config should be granular and orthogonal. ([12factor.net][2])

In your code, this part is the main thing I would revise:

```python
enable_swagger = environment == "dev" or enable_swagger_env
```

That is not wrong, but it makes `environment` a policy switchboard. A more 12-factor-friendly shape is:

* `DOC_FORGE_ENABLE_SWAGGER`
* `DOC_FORGE_LOG_LEVEL`
* `DOC_FORGE_SERVICE_NAME`
* `DOC_FORGE_OTEL_ENDPOINT`
* `DOC_FORGE_DATABASE_URL`
* etc.

You can still keep `DOC_FORGE_ENVIRONMENT` for tagging logs/telemetry and broad runtime identity, but avoid making it the hidden source of unrelated behavior.

## What `.env` should mean in this model

For this direction, `.env` should be treated as a **local development convenience**, not as the production configuration mechanism. Pydantic Settings supports dotenv files, and environment variables override dotenv values. Docker Compose also has its own `.env` interpolation behavior and precedence rules, but Compose `.env` handling is a CLI feature, not the application’s long-term config contract. ([Pydantic][3])

So I would use this rule:

* **local dev outside Docker**: optional `.env`
* **local dev inside Docker**: `docker run --env-file ...` or Compose `environment` / `env_file`
* **prod/cloud**: platform-injected env vars, ConfigMaps, Secrets, or mounted secret files

That keeps the app independent of whichever orchestrator you end up using. Kubernetes supports ConfigMaps for non-confidential data and Secrets for sensitive data, and Pods can consume them as env vars or files. ([Kubernetes][8])

## Secrets: env vars vs secret files

For non-sensitive settings, env vars are fine.

For sensitive settings, if you are moving toward cloud-native/container-native operation, I would make the app support **both**:

* env vars
* secret files via `secrets_dir`

Pydantic Settings supports secrets directories directly, and documents Docker’s default `/run/secrets` location. Kubernetes Secrets can also be mounted or exposed to Pods, though Kubernetes warns that Secrets need proper handling because they are not magically secure by default. ([Pydantic][3])

That leads to a practical pattern:

* `DATABASE_HOST`, `LOG_LEVEL`, `ENABLE_SWAGGER`: env vars
* `DATABASE_PASSWORD`, `API_TOKEN`, `JWT_PRIVATE_KEY`: secret file or secret manager injection

## Concrete recommendation for your app

I would standardize on this architecture:

```python
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOC_FORGE_",
        env_file=".env",          # local convenience only
        extra="ignore",
        secrets_dir="/run/secrets",
    )

    environment: Literal["dev", "test", "prod"] = "prod"
    service_name: str = "doc_forge-api"
    log_level: str = "INFO"
    enable_swagger: bool = False

    # examples
    database_url: str | None = None
    api_token: SecretStr | None = None

    @property
    def swagger_enabled(self) -> bool:
        return self.enable_swagger


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Then:

* `create_app(settings: Settings | None = None)`
* default to `get_settings()`
* configure logging from `settings`
* store `app.state.settings = settings`

And I would stop calling `os.environ.get(...)` throughout the app.

## Decision table

For your stated direction, this is the practical ranking:

**Best default**

* `pydantic-settings`

**Good minimal fallback**

* `starlette.config`

**Only if config itself becomes complex**

* `Dynaconf`
* `ConfZ`

**Usually overkill for FastAPI services**

* `Hydra` / `OmegaConf`

So the short recommendation is:

**Use `pydantic-settings` as the app-level config framework, treat environment variables as the primary external interface, support `secrets_dir` for container/cloud secrets, and keep `.env` only as a local dev convenience.**

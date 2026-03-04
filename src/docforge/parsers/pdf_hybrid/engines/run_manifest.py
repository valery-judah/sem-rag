from pydantic import BaseModel


class EngineRunManifest(BaseModel):
    engine_name: str
    status: str  # "ok", "timeout", "error", "unavailable"
    version: str | None = None
    binary_path: str | None = None
    raw_output_dir: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    execution_time_s: float | None = None
    error_details: str | None = None

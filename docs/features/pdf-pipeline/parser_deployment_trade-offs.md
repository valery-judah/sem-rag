# Architectural Trade-off Analysis: Marker Integration (Docker API vs. Subprocess CLI)

This analysis evaluates two approaches for integrating the custom `marker-master` parsing logic into the `sem-rag` hybrid PDF pipeline:
1. **Subprocess CLI (Current Approach):** Running an isolated virtual environment (`tools/marker/.venv`) and invoking a single-PDF Python adapter via `subprocess.run()`.
2. **Docker HTTP API:** Packing `marker-master` and its models into a Docker container exposing a REST API (e.g., FastAPI), and querying it over the local network.

---

### 1. Deployment Complexity and Infrastructure

*   **Subprocess CLI:**
    *   **Pros:** Minimal infrastructure footprint. It leverages standard Python virtual environments, aligning with the existing `sem-rag` repository setup (`Makefile`, `uv`). Deployment only requires cloning the repo and syncing dependencies.
    *   **Cons:** Host environment variability. Managing system-level dependencies (like `libGL`, `poppler-utils`, or specific CUDA drivers) relies on the host OS. This can lead to "works on my machine" issues across macOS, Linux, or CI environments.
*   **Docker API:**
    *   **Pros:** Complete immutability and portability. All OS-level dependencies, system libraries, and Python packages are baked into the image. It guarantees the exact same environment across local dev, CI, and production.
    *   **Cons:** Introduces new architectural topology. Requires Docker daemon to be running. You now have a distributed system (Main App + Sidecar API) instead of a monolithic execution flow. Requires managing Docker compose files, port mappings, and container lifecycle.

### 2. Resource Isolation (GPU/Memory Limits)

*   **Subprocess CLI:**
    *   **Pros:** Lightweight process boundaries with virtually no namespace or networking overhead.
    *   **Cons:** Weak resource sandboxing. A memory leak or aggressive VRAM allocation in the `marker` subprocess can easily starve or OOM the main `sem-rag` application. Restricting a subprocess to specific CPU/Memory quotas is notoriously difficult relying only on OS-level `ulimit` or environment variables (e.g., `PYTORCH_ALLOC_CONF`).
*   **Docker API:**
    *   **Pros:** First-class resource isolation. Docker provides strict enforcement of bounds via `--memory`, `--cpus`, and `--gpus all`. If the Marker container OOMs, the Docker daemon restarts it (or kills it safely) without taking down the main `sem-rag` orchestration pipeline.

### 3. Performance (Cold Starts, IPC, and Batching)

*   **Subprocess CLI:**
    *   **Pros:** Avoids network serialization overhead (no HTTP payloads). Data is passed efficiently via the filesystem (writing PDF to disk, subprocess reads it, writes JSON/MD, main process reads JSON).
    *   **Cons:** **Severe Cold-Start Penalty.** Every time `subprocess.run()` is called, Python must spin up, initialize PyTorch, load the heavy vision/layout models from disk into VRAM/RAM, run inference on *one* PDF, and tear down. For processing a corpus of 100 PDFs, you pay the model loading cost 100 times.
*   **Docker API:**
    *   **Pros:** **Persistent Model State.** A Dockerized API loads the heavy ML models into memory *once* upon startup. Subsequent HTTP requests skip the initialization phase entirely, resulting in dramatically faster per-document inference times. It also opens the door to intelligent request queueing or dynamic batching inside the API server.
    *   **Cons:** Network serialization overhead (encoding the PDF to base64 or multipart/form-data, and deserializing the JSON response), though this cost is negligible compared to the massive savings of avoiding model cold-starts.

### 4. Maintainability and Developer Experience (DX)

*   **Subprocess CLI:**
    *   **Pros:** Excellent local DX. Fits perfectly into the current `AGENTS.md` and E2E harness (`docs/features/e2e/`). Developers can step through the main pipeline and easily debug the subprocess by running the CLI command manually. Updating custom logic in `marker-master` just requires a fast `uv pip install -e` in the tool's `.venv`.
    *   **Cons:** Python environment path issues (`PYTHONPATH`) can still occasionally leak if the isolation isn't perfectly configured.
*   **Docker API:**
    *   **Pros:** Language-agnostic, strict API contracts (e.g., OpenAPI). The main application doesn't care about the internal Python version or dependencies of the Marker container.
    *   **Cons:** Degraded local iteration speed. Every change to the custom `marker-master` logic requires rebuilding the Docker image or setting up complex volume mounts for live-reloading. Debugging requires attaching remote debuggers into the running container. Tests require standing up the container first.

### 5. Determinism and Artifact Stability (RFC `01_rfc.md` Compliance)

*   **Subprocess CLI:**
    *   **Pros:** High alignment with current RFC. The subprocess approach natively supports the strict artifact layout (`<artifact_dir>/<safe_doc_id>/<run_id>/`). The main process constructs the `config_hash` and directs the subprocess via `--output_dir` exactly where to write the deterministic artifacts. The process is inherently stateless between runs.
    *   **Cons:** System noise (thread contention) might rarely affect execution time, though functional determinism is usually safe.
*   **Docker API:**
    *   **Pros:** Container immutability guarantees the exact same model weights and library versions, ensuring stable inference output.
    *   **Cons:** Friction with the RFC artifact layout. To emit artifacts deterministically to the main app's `<artifact_dir>`, the Docker container must either:
        1. Return the entire artifact payload (images, MD, JSON) over HTTP for the main app to write to disk.
        2. Mount the host's `artifact_dir` via Docker volumes, which introduces path/permission complexities across OSes.
        Additionally, tracking the "engine version" for the `config_hash` (required by the RFC) requires pinging a `/health` or `/version` endpoint on the API rather than just running a fast `python -c` script. Finally, persistent APIs can sometimes leak state or cache between requests, risking non-determinism.

### Summary Recommendation

*   **Stick with Subprocess CLI if:** The priority is adhering strictly to the current `sem-rag` architecture, maintaining simple local development loops, and ensuring seamless compliance with the `01_rfc.md` artifact generation rules. The cold-start penalty is acceptable for the current scale or is mitigated by processing very large PDFs where inference time dwarfs startup time.
*   **Pivot to Docker API if:** Processing throughput is the primary bottleneck and you must eliminate the PyTorch model cold-start penalty per document. It is also the better choice if strict VRAM/RAM sandboxing is required to prevent the main application from crashing during heavy ML inference.
# Ingestion Flow

Based on an investigation of the codebase, **no generative LLM (such as Llama, OpenAI, or Gemini) processes the document during ingestion.**

The document is processed through an asynchronous, event-driven architecture. The stack is split into the **API layer** (which accepts the file and queues the first job) and the **Background Worker layer** (which processes the file through a state machine of stages).

Here is the exact call stack and function flow:

## 1. API Layer (Ingestion Request)
* **Controller/Router:** `src/doc_forge/app/api.py:upload_document`
  * Accepts the HTTP POST request with the file.
* **Service:** `src/doc_forge/lifecycle/service.py:DocumentLifecycleService.upload_document`
  * Validates the file extension, computes the checksum, and passes it to the orchestrator.
* **Orchestrator:** `src/doc_forge/lifecycle/orchestrator.py:DocumentLifecycleOrchestrator.register_document` (invoked internally during upload)
  * Writes the raw file to the filesystem (`FilesystemArtifactStore.write_raw`).
  * Creates the `PersistedDocument` record in Postgres with status `REGISTERED`.
  * Calls `enqueue_stage(target_stage=DocumentJobStage.EXTRACT)` to queue the first worker job.

## 2. Worker Layer (Processing Pipeline)
A background polling loop (`src/doc_forge/lifecycle/worker.py:main`) continually queries the database for pending jobs. When the job is picked up, it passes through the following stack for each stage:

* **Worker Loop:** `src/doc_forge/lifecycle/worker.py:DocumentLifecycleWorker.run_next`
  * Claims the next job and looks up the corresponding `StageRunner` from a registry (defined in `src/doc_forge/app/deps.py:get_document_lifecycle_worker`).
  * Calls `runner.run(job)`. Upon success, calls `orchestrator.enqueue_stage` for the *next* stage in the sequence.

The sequence of stages (`runner.run`) is defined by the `_NEXT_STAGE` dictionary in `src/doc_forge/lifecycle/orchestrator.py`:

### Stage 1: EXTRACT
* **Runner:** `src/doc_forge/stages/extract.py:ExtractDocumentJobStage.run` -> `ExtractDocumentStage.run`
* **Implementation:** Reads the raw file and calls `ExtractorRegistry.extract`.
  * For Markdown: `src/doc_forge/extractors/markdown.py:MarkdownExtractor.extract` (regex-based).
  * For PDF: `src/doc_forge/extractors/pdf.py:PdfExtractor.extract` (uses PyPDF2).
* **Output:** Saves an `ExtractedArtifact` JSON to disk. Updates status to `EXTRACTING`.

### Stage 2: NORMALIZE
* **Runner:** `src/doc_forge/stages/normalize.py:NormalizeDocumentJobStage.run` -> `NormalizeDocumentStage.run`
* **Implementation:** Calls `NormalizerRegistry.normalize` to convert raw extracted blocks into a canonical structure.
  * For Markdown: `src/doc_forge/normalizers/markdown.py:MarkdownNormalizer.normalize`.
* **Output:** Saves a `NormalizedArtifact` JSON to disk. Updates status to `NORMALIZED`.

### Stage 3: SECTIONIZE
* **Runner:** `src/doc_forge/structure/sections.py:SectionizeDocumentStage.run`
* **Implementation:** Calls `SectionDerivationService.derive`. It parses heading hierarchies to build logical sections.
* **Output:** Inserts `Section` records into Postgres.

### Stage 4: CHUNK
* **Runner:** `src/doc_forge/chunking/service.py:ChunkDocumentStage.run`
* **Implementation:** Calls `ChunkingService.derive_chunks` to split text blocks into bite-sized segments based on token limits while respecting section boundaries.
* **Output:** Inserts `Chunk` records into Postgres. Updates status to `CHUNKED`.

### Stage 5: INDEX
* **Runner:** `src/doc_forge/indexing/service.py:IndexDocumentStage.run`
* **Implementation:** Calls `SqlVectorStore.publish_document`.
  * It maps chunks to an `EmbeddingAdapter` (`src/doc_forge/indexing/embeddings.py:SentenceTransformerEmbeddingAdapter.embed_texts`).
  * Computes the vector using `sentence-transformers/all-MiniLM-L6-v2`.
* **Output:** Inserts `ChunkEmbedding` vectors and `IndexEntry` records into Postgres. Updates status to `INDEXED`.

### Stage 6: READY_CHECK
* **Runner:** `src/doc_forge/stages/ready.py:ReadyDocumentStage.run` -> `ReadinessAssessor.assess`
* **Implementation:** Validates that the document has all artifacts, sections, chunks, and index entries properly populated. Runs a "smoke query" against the vector store to ensure the document is retrievable.
* **Output:** Updates final status to `READY`.

If any stage fails, `DocumentLifecycleWorker._fail_job` catches the exception, updates the document status to `FAILED`, and stops the chain.

## The Model Used During Ingestion
The only model that processes the document during ingestion is the **embedding model** in the `INDEX` stage. 

According to `docker-compose.yml` and the default settings in `src/doc_forge/app/settings.py`, the index stage uses the `sentence-transformers` backend:
* **Embedding Backend:** `sentence-transformers`
* **Specific Model:** `sentence-transformers/all-MiniLM-L6-v2` (`DOC_FORGE_EMBEDDING_MODEL` default)

## Generative LLM Usage
The generative LLMs configured in the project (like `mlx-community/TinyLlama-1.1B-Chat-v1.0` or `llama3.2:1b` via Ollama) are **only used later during the Query Answer Generation phase** (specifically the `GENERATE` stage in `src/doc_forge/query/answer_generation.py`), not during the ingestion of the document.

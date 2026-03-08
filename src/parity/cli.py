"""Command-line demo for semantic retrieval."""

from __future__ import annotations

from .retrieval import SemanticIndex


def main() -> None:
    docs = [
        "Retrieval augmented generation connects an LLM to external knowledge.",
        "Semantic search returns passages based on meaning, not only keyword match.",
        "Chunking strategy strongly affects context quality in RAG pipelines.",
    ]
    index = SemanticIndex(docs)
    query = "How does semantic retrieval help rag?"

    print(f"Query: {query}")
    for rank, (doc, score) in enumerate(index.search(query, k=2), start=1):
        print(f"{rank}. score={score:.3f} :: {doc}")


if __name__ == "__main__":
    main()

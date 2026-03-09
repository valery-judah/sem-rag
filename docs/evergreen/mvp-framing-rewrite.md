# MVP Framing: Question-Answering Service over PDF Books and Markdown Files

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-09

## 1. Problem

Engineers often work with collections of technical books, manuals, specifications, and notes in **PDF** and **Markdown** formats. Those materials contain the answers they need, but the answers are difficult to reach quickly.

The information is trapped inside long-form documents that are slow to browse manually. Relevant material may be spread across multiple files, chapters, or sections. PDF books are especially awkward to work with because structure is not always explicit, while Markdown files vary widely in quality and organization.

The result is repeated search loops, unnecessary reading, and avoidable decision risk. Users spend time searching, skimming, and cross-checking documents instead of reaching a supported answer.

Basic file search and keyword search are not sufficient because they do not reliably provide:

- answers grounded in the uploaded corpus
- usable references back to the source material
- light synthesis from one or more relevant files
- a consistent experience across PDF and Markdown inputs

This MVP addresses that problem by turning a focused collection of PDF books and Markdown files into a queryable corpus that can answer questions and point the user back to the supporting source material.

## 2. Goal

Build a service where a user can:

- upload a focused collection of **PDF books** and **Markdown files**
- ask natural-language questions over the collection
- receive answers grounded in the uploaded documents
- inspect which documents, pages, chapters, or sections informed the answer
- recognize when the corpus does not support a confident response

The MVP should prove that a mixed-format document collection can become a usable **question-answering and evidence-inspection service**.

## 3. Why This MVP Exists Now

This MVP exists to validate a limited set of product and feasibility hypotheses without expanding into a broad research or document-intelligence platform.

### 3.1 Product hypotheses

1. Engineers working with technical books, manuals, specs, and notes derive real value from asking questions over a bounded document collection rather than searching files manually.
2. Users trust answers more when the service shows the evidence behind them.
3. A single interface over a focused corpus is more useful than isolated file browsing or keyword search.

### 3.2 Feasibility hypotheses

1. Text-based PDF and Markdown inputs can be processed well enough to support useful retrieval and source-backed answers.
2. The service can preserve enough source context to make answer inspection practical.
3. A mixed-format corpus can be supported without forcing the user into format-specific workflows.

### 3.3 Fallback path during validation

The product target for MVP remains a mixed-format corpus of PDFs and Markdown files.

If PDF handling does not clear a usefulness threshold during beta validation, the team may run a Markdown-first beta to validate the core user flow: asking questions, receiving source-backed answers, and inspecting evidence. That is a validation fallback, not a redefinition of the product target.

## 4. Product Definition

The MVP is a **document question-answering and evidence-inspection service** over a bounded user-provided corpus.

At a high level, the product does four things:

1. accepts user-uploaded PDF and Markdown documents
2. prepares those documents so they can be queried as one corpus
3. retrieves relevant content for a user question
4. answers using that content and shows the supporting sources

The product is successful if a user can reach a supported answer, inspect the evidence behind it, and notice when the corpus does not support a reliable response.

## 5. Initial User and Primary Jobs To Be Done

### Initial beta user

- engineers working with technical books, manuals, specifications, and notes

### Possible expansion users after MVP

- researchers or students working with a focused reading corpus
- internal knowledge workers querying a personal or team document set

### Primary jobs to be done

Users want to:

- find answers without manually reading entire books or notes
- ask focused questions in natural language over a bounded collection
- get a supported answer from one or more relevant documents
- inspect the evidence behind an answer
- navigate back to the source material behind an answer
- understand when the corpus does not support a reliable answer

## 6. Supported Inputs

### In scope for MVP

- **text-based PDF files**
- **Markdown files**

### Input assumptions

- PDFs are primarily text-based and do not require OCR.
- PDF handling is aimed at recoverable text structure and usable source references, not layout-perfect reconstruction.
- Markdown files are UTF-8 text and may include headings, lists, paragraphs, and code blocks.
- Some Markdown files may originate from PDF-to-Markdown conversion.
- Users may upload a collection rather than a single file.

## 7. In Scope

The MVP includes the following capabilities.

### 7.1 Corpus creation

- accept user-uploaded PDF and Markdown files
- treat them as one question-answerable collection
- retain enough document context to present meaningful source references

### 7.2 Basic structure recovery

- extract text from supported inputs
- recover headings and sections where possible
- preserve document boundaries
- preserve coarse source locations that are useful for source inspection

For PDFs, source references may be coarse, such as page number plus inferred heading or section context when available. Exact paragraph-level anchoring is not required in MVP.

### 7.3 Question answering over the corpus

- accept natural-language questions over the uploaded collection
- retrieve relevant content from one or more documents
- generate answers based on retrieved source material
- return source references with the answer

### 7.4 Source inspection and navigation

- show which documents contributed to an answer
- identify relevant sections, chapters, and pages when available
- let the user inspect the source material behind the answer

## 8. Out of Scope

The following are explicitly deferred from MVP.

### 8.1 Parsing and document understanding exclusions

- scanned PDFs that require OCR
- layout-perfect reconstruction
- special handling for tables, diagrams, charts, and pictures
- figure understanding
- complex footnotes, sidebars, or margin annotations

### 8.2 Retrieval and answer-behavior exclusions

- lexical search as a first-class retrieval mode
- advanced hybrid retrieval tuning
- sophisticated reranking pipelines beyond basic MVP needs
- guaranteed exhaustive retrieval over very large corpora
- strong compare-and-contrast behavior that depends on deliberate source diversification or exhaustive coverage of competing viewpoints

### 8.3 Derived knowledge exclusions

- stored summaries as a first-class artifact
- synthetic questions
- graph or entity-relation extraction
- precomputed derived knowledge views beyond direct question answering

### 8.4 Product/platform exclusions

- collaboration and sharing
- external drive connectors and sync
- workflow automation
- billing, quotas, and advanced admin controls
- full production hardening and platform operations tooling

### 8.5 Question classes outside MVP

- questions requiring external world knowledge not present in the uploaded corpus
- questions whose answers depend mainly on tables, figures, or images
- exact scholarly citation formatting

## 9. Primary Use Cases

### 9.1 Factual lookup

Examples:

- “What is X?”
- “How does this book define Y?”
- “What are the requirements for Z?”

### 9.2 Localized explanation

Examples:

- “Explain the retry strategy described in these notes.”
- “Summarize the chapter’s explanation of backpropagation.”

### 9.3 Light multi-document synthesis

Examples:

- “What do these documents say about vector databases?”
- “Synthesize the guidance on caching from Book A and my notes.”

The MVP may synthesize across more than one relevant document when the evidence is straightforward. It does not promise exhaustive comparison across all relevant sources or deliberate balancing of competing viewpoints.

### 9.4 Source navigation

Examples:

- “Where is tokenization discussed?”
- “Which book or section covers distributed transactions?”
- “Show the passages relevant to this question.”

## 10. Trust Contract

The MVP stands or falls on whether users can inspect and verify answers.

The product must therefore satisfy these conditions:

- answers are based primarily on retrieved corpus content
- source references are useful enough for a user to inspect the origin of the answer
- the service does not hide weak evidence behind confident language
- when the corpus is insufficient, the service says so

For PDFs, source inspection may be coarse. The requirement is usable provenance, not perfect citation precision.

## 11. Success Criteria

The MVP is successful if a beta user can:

- upload a small collection of PDF and Markdown documents
- ask a question over that collection
- receive an answer based primarily on uploaded source material
- inspect which documents and sections informed the answer
- determine when the corpus does not provide enough evidence for a reliable response

### Recommended beta validation metrics

The team should evaluate the beta against a small set of measurable checks such as:

- **Supported-answer rate:** in a representative beta question set, a substantial majority of answers judged useful are also judged supported by the cited source material
- **Inspectable-source rate:** users can open and inspect the cited source material for most successful answers
- **Failure honesty:** when evidence is weak or absent, the service abstains or qualifies the answer rather than asserting unsupported claims
- **Time-to-answer improvement:** users reach a supported answer materially faster than with manual browsing alone
- **Mixed-format usability:** users can work across PDFs and Markdown files without needing different mental models for each format

Exact thresholds should be set during beta planning, but these are the right dimensions for MVP validation.

## 12. Non-Goals

This MVP is **not** intended to:

- fully understand arbitrary PDFs
- solve OCR and complex layout reconstruction
- replace deep manual reading for all workflows
- provide perfect answers for every question type
- support every document format from day one
- act as a general-purpose research agent over the public web

## 13. Open Questions

These questions should be answered in design and beta planning rather than in the framing document itself.

1. What maximum corpus size should MVP support reliably?
2. What minimum PDF source reference is sufficient for users: page only, page plus heading, or page plus inferred section path?
3. How should the product behave when structure recovery is weak?
4. What beta metrics and thresholds are sufficient to declare the product useful?
5. What answer UI is sufficient for source inspection in MVP?

## 14. Summary

This MVP is a focused service for asking questions over a bounded user-uploaded collection of PDF books and Markdown files.

Version 1 is about proving that the system can:

- accept a mixed-format corpus
- support question answering over that corpus
- ground answers in identifiable source material
- let the user inspect the evidence behind the answer
- fail honestly when the corpus does not support a confident response

It is not yet about full document intelligence, advanced parsing, or exhaustive analytical comparison across sources.

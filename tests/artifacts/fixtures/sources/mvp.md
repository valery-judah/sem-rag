# MVP: Question-Answering Service over PDF Books and Markdown Files

## 1. Problem

Users often have collections of technical books, manuals, notes, and internal documents in PDF and Markdown formats, but these materials are difficult to query as a single knowledge source.

Basic file search or keyword search is often not enough because it does not reliably provide:

- grounded answers based on the uploaded corpus
- references back to the relevant source material
- synthesis across multiple files

## 2. Goal

Build a service where a user can:

- upload a focused collection of PDF books and Markdown files
- ask natural-language questions over the whole collection
- inspect which documents, pages, chapters, or sections informed the answer

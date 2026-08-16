"""Embedding column type.

Stores embeddings as plain JSON (a list of floats) rather than a pgvector
column -- no Postgres extension required. Kept as its own module so the
Event model and any future models have one place to import from, and so
a switch back to pgvector later (if scale ever warrants in-database ANN
search) only touches this file.
"""

from __future__ import annotations

from sqlalchemy import JSON as EmbeddingType

__all__ = ["EmbeddingType"]
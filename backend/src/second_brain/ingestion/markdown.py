"""Markdown file ingestion: read, chunk, embed, store."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, cast

from second_brain.contracts.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeTypeValue,
    SourceOriginValue,
)
from second_brain.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_MAX_CHUNK_CHARS = 2000
DEFAULT_MIN_CHUNK_CHARS = 100
EXPECTED_EMBEDDING_DIM = 1024


def chunk_markdown(
    content: str,
    max_chars: int = DEFAULT_MAX_CHUNK_CHARS,
    min_chars: int = DEFAULT_MIN_CHUNK_CHARS,
) -> list[str]:
    """Split markdown by H2 headings, then paragraphs, and merge tiny chunks."""
    if not content.strip():
        return []

    sections: list[str] = []
    current: list[str] = []

    for line in content.split("\n"):
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    chunks: list[str] = []
    for section in sections:
        if not section:
            continue

        if len(section) <= max_chars:
            chunks.append(section)
            continue

        paragraphs = section.split("\n\n")
        buffer = ""
        for paragraph in paragraphs:
            candidate = paragraph.strip()
            if not candidate:
                continue

            if buffer and len(buffer) + len(candidate) + 2 > max_chars:
                chunks.append(buffer.strip())
                buffer = candidate
            else:
                buffer = f"{buffer}\n\n{candidate}" if buffer else candidate

        if buffer.strip():
            chunks.append(buffer.strip())

    merged: list[str] = []
    for chunk in chunks:
        if merged and len(chunk) < min_chars and not chunk.lstrip().startswith("## "):
            merged[-1] = f"{merged[-1]}\n\n{chunk}"
        else:
            merged.append(chunk)

    return [chunk for chunk in merged if chunk.strip()]


def read_markdown_file(path: Path) -> tuple[str, str]:
    """Read a markdown file and derive title from first H1 heading."""
    content = path.read_text(encoding="utf-8")
    title = path.stem

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            break

    return title, content


def ingest_markdown_directory(
    directory: str | Path,
    supabase_url: str | None = None,
    supabase_key: str | None = None,
    voyage_api_key: str | None = None,
    embed_model: str = "voyage-4-large",
    knowledge_type: KnowledgeTypeValue = "note",
    source_origin: SourceOriginValue = "obsidian",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Ingest .md files into knowledge_documents and knowledge_chunks."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return {
            "error": f"Directory not found: {directory}",
            "files": 0,
            "chunks": 0,
        }

    md_files = sorted(dir_path.glob("*.md"))
    if not md_files:
        return {"error": f"No .md files found in {directory}", "files": 0, "chunks": 0}

    resolved_supabase_url = supabase_url or os.getenv("SUPABASE_URL")
    resolved_supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
    resolved_voyage_key = voyage_api_key or os.getenv("VOYAGE_API_KEY")

    if not dry_run and (not resolved_supabase_url or not resolved_supabase_key):
        return {"error": "SUPABASE_URL and SUPABASE_KEY required for non-dry-run ingestion"}

    if not dry_run and not resolved_voyage_key:
        return {"error": "VOYAGE_API_KEY required for embedding"}

    voyage_client: Any | None = None
    if not dry_run:
        try:
            import voyageai

            voyage_client = voyageai.Client(api_key=resolved_voyage_key)  # type: ignore[attr-defined]
        except ImportError:
            return {"error": "voyageai SDK not installed. Run: pip install voyageai"}
        except Exception as exc:
            return {"error": f"Voyage client init failed: {exc}"}

    supa_client: Any | None = None
    if not dry_run:
        try:
            from supabase import create_client

            assert resolved_supabase_url is not None
            assert resolved_supabase_key is not None
            supa_client = create_client(resolved_supabase_url, resolved_supabase_key)
        except ImportError:
            return {"error": "supabase SDK not installed. Run: pip install supabase"}
        except Exception as exc:
            return {"error": f"Supabase client init failed: {exc}"}

    results: dict[str, Any] = {
        "files": len(md_files),
        "chunks": 0,
        "documents_created": 0,
        "chunks_embedded": 0,
        "chunks_stored": 0,
        "errors": [],
        "dry_run": dry_run,
    }

    for md_file in md_files:
        try:
            title, content = read_markdown_file(md_file)
            chunks = chunk_markdown(content)
            if not chunks:
                results["errors"].append(f"{md_file.name}: no chunks produced")
                continue

            document_id = uuid.uuid4()
            document = KnowledgeDocument(
                id=document_id,
                title=title,
                knowledge_type=knowledge_type,
                source_origin=source_origin,
                source_url=str(md_file.resolve()),
                raw_content=content,
            )

            if not dry_run and supa_client is not None:
                supa_client.table("knowledge_documents").insert(
                    {
                        "id": str(document.id),
                        "title": document.title,
                        "knowledge_type": document.knowledge_type,
                        "source_origin": document.source_origin,
                        "source_url": document.source_url,
                        "raw_content": document.raw_content,
                    }
                ).execute()
                results["documents_created"] += 1

            for index, chunk_text in enumerate(chunks):
                try:
                    embedding: list[float] | None = None
                    if not dry_run and voyage_client is not None:
                        embed_result = voyage_client.embed(
                            [chunk_text], model=embed_model, input_type="document"
                        )
                        if not embed_result.embeddings:
                            results["errors"].append(
                                f"{md_file.name} chunk {index}: empty embedding"
                            )
                            continue

                        embedding = cast(list[float], embed_result.embeddings[0])
                        if len(embedding) != EXPECTED_EMBEDDING_DIM:
                            results["errors"].append(
                                f"{md_file.name} chunk {index}: embedding dimension "
                                f"{len(embedding)} != {EXPECTED_EMBEDDING_DIM}"
                            )
                            continue
                        results["chunks_embedded"] += 1

                    chunk = KnowledgeChunk(
                        document_id=document_id,
                        content=chunk_text,
                        chunk_index=index,
                        knowledge_type=knowledge_type,
                        source_origin=source_origin,
                    )

                    if not dry_run and supa_client is not None and embedding is not None:
                        supa_client.table("knowledge_chunks").insert(
                            {
                                "id": str(chunk.id),
                                "document_id": str(chunk.document_id),
                                "content": chunk.content,
                                "embedding": embedding,
                                "knowledge_type": chunk.knowledge_type,
                                "chunk_index": chunk.chunk_index,
                                "source_origin": chunk.source_origin,
                            }
                        ).execute()
                        results["chunks_stored"] += 1

                except Exception as exc:
                    results["errors"].append(
                        f"{md_file.name} chunk {index}: {type(exc).__name__}: {str(exc)[:100]}"
                    )

            results["chunks"] += len(chunks)
            logger.info("Ingested %s: %d chunks", md_file.name, len(chunks))

        except Exception as exc:
            results["errors"].append(
                f"{md_file.name}: {type(exc).__name__}: {str(exc)[:100]}"
            )

    return results

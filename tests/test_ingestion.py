"""Tests for markdown ingestion."""

from second_brain.ingestion.markdown import (
    chunk_markdown,
    ingest_markdown_directory,
    read_markdown_file,
)


class TestChunkMarkdown:
    """Test chunk_markdown function."""

    def test_empty_content(self) -> None:
        assert chunk_markdown("") == []
        assert chunk_markdown("   ") == []

    def test_single_section(self) -> None:
        content = "# Title\n\nSome content here."
        chunks = chunk_markdown(content)
        assert len(chunks) == 1
        assert "Some content" in chunks[0]

    def test_split_on_h2(self) -> None:
        content = (
            "# Title\n\nIntro paragraph\n\n"
            "## Section 1\n\nContent 1\n\n"
            "## Section 2\n\nContent 2"
        )
        chunks = chunk_markdown(content)
        assert len(chunks) >= 2

    def test_large_section_splits_on_paragraphs(self) -> None:
        content = "## Big Section\n\n" + "\n\n".join(
            [f"Paragraph {i} " * 50 for i in range(10)]
        )
        chunks = chunk_markdown(content, max_chars=500)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 700

    def test_tiny_chunks_merged(self) -> None:
        content = (
            "## A\n\nOk\n\n"
            "## B\n\nAlso short\n\n"
            "## C\n\nThis is a much longer section with real content "
            "that should stand on its own."
        )
        chunks = chunk_markdown(content, min_chars=50)
        assert len(chunks) <= 3

    def test_no_headings(self) -> None:
        content = "Just plain text\n\nWith paragraphs\n\nAnd more text"
        chunks = chunk_markdown(content)
        assert len(chunks) >= 1
        assert "Just plain text" in chunks[0]

    def test_preserves_content(self) -> None:
        content = "## Section\n\nImportant content that must be preserved."
        chunks = chunk_markdown(content)
        full_text = " ".join(chunks)
        assert "Important content" in full_text

    def test_only_whitespace_sections_filtered(self) -> None:
        content = "## A\n\n\n\n## B\n\nReal content"
        chunks = chunk_markdown(content)
        for chunk in chunks:
            assert chunk.strip()


class TestReadMarkdownFile:
    """Test read_markdown_file function."""

    def test_reads_file_and_extracts_title(self, tmp_path) -> None:
        md_file = tmp_path / "test.md"
        md_file.write_text("# My Title\n\nSome content.", encoding="utf-8")
        title, content = read_markdown_file(md_file)
        assert title == "My Title"
        assert "Some content" in content

    def test_no_heading_uses_filename(self, tmp_path) -> None:
        md_file = tmp_path / "notes.md"
        md_file.write_text("Just content, no heading.", encoding="utf-8")
        title, content = read_markdown_file(md_file)
        assert title == "notes"
        assert "Just content" in content

    def test_h2_not_used_as_title(self, tmp_path) -> None:
        md_file = tmp_path / "doc.md"
        md_file.write_text("## Section\n\nContent", encoding="utf-8")
        title, _ = read_markdown_file(md_file)
        assert title == "doc"

    def test_title_with_extra_spaces(self, tmp_path) -> None:
        md_file = tmp_path / "test.md"
        md_file.write_text("#   Spaced Title  \n\nContent", encoding="utf-8")
        title, _ = read_markdown_file(md_file)
        assert title == "Spaced Title"


class TestIngestMarkdownDirectory:
    """Test ingest_markdown_directory function."""

    def test_nonexistent_directory(self) -> None:
        result = ingest_markdown_directory("/nonexistent/path")
        assert "error" in result
        assert result["files"] == 0

    def test_empty_directory(self, tmp_path) -> None:
        result = ingest_markdown_directory(tmp_path)
        assert "error" in result
        assert "No .md files" in result["error"]

    def test_dry_run_no_credentials_needed(self, tmp_path) -> None:
        (tmp_path / "note1.md").write_text("# Note 1\n\nContent 1", encoding="utf-8")
        (tmp_path / "note2.md").write_text("# Note 2\n\nContent 2", encoding="utf-8")

        result = ingest_markdown_directory(tmp_path, dry_run=True)

        assert result.get("error") is None
        assert result["files"] == 2
        assert result["chunks"] >= 2
        assert result["dry_run"] is True
        assert result["chunks_stored"] == 0
        assert result["documents_created"] == 0

    def test_dry_run_counts_chunks(self, tmp_path) -> None:
        content = "# Big Note\n\n## Section 1\n\nContent 1\n\n## Section 2\n\nContent 2"
        (tmp_path / "big.md").write_text(content, encoding="utf-8")

        result = ingest_markdown_directory(tmp_path, dry_run=True)

        assert result["chunks"] >= 2

    def test_missing_supabase_creds_without_dry_run(self, tmp_path) -> None:
        (tmp_path / "note.md").write_text("# Note\n\nContent", encoding="utf-8")

        result = ingest_markdown_directory(tmp_path, voyage_api_key="fake")

        assert "error" in result
        assert "SUPABASE" in result["error"]

    def test_missing_voyage_key_without_dry_run(self, tmp_path) -> None:
        (tmp_path / "note.md").write_text("# Note\n\nContent", encoding="utf-8")

        result = ingest_markdown_directory(
            tmp_path,
            supabase_url="https://x.supabase.co",
            supabase_key="key",
        )

        assert "error" in result
        assert "VOYAGE" in result["error"]

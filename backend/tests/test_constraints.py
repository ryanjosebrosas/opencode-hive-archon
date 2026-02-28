from __future__ import annotations

import pathlib

# Define base directory relative to this test file
BASE_DIR = pathlib.Path(__file__).parent.parent  # Go up twice from tests/ to backend/
MIGRATIONS_DIR = BASE_DIR / "migrations"
MIGRATION_FILE = MIGRATIONS_DIR / "004_integrity_constraints.sql"


def test_migration_file_exists():
    """Test that the integrity constraints migration file exists."""
    migration_path = MIGRATION_FILE
    assert migration_path.exists()


def test_entity_type_check_constraint_added():
    """Test SQL contains the entity_type check constraint."""
    content = MIGRATION_FILE.read_text()
    assert "knowledge_entities_entity_type_check" in content


def test_entity_type_values_include_person():
    """Test SQL checks for 'person' in entity_type values."""
    content = MIGRATION_FILE.read_text()
    assert "'person'" in content


def test_relationships_source_fkey_added():
    """Test SQL contains the relationships source foreign key."""
    content = MIGRATION_FILE.read_text()
    assert "knowledge_relationships_source_node_id_fkey" in content


def test_relationships_target_fkey_added():
    """Test SQL contains the relationships target foreign key."""
    content = MIGRATION_FILE.read_text()
    assert "knowledge_relationships_target_node_id_fkey" in content


def test_relationships_fkey_references_knowledge_entities():
    """Test SQL foreign keys reference knowledge_entities(id)."""
    content = MIGRATION_FILE.read_text()
    assert "REFERENCES knowledge_entities(id)" in content


def test_entity_name_unique_per_type():
    """Test SQL contains the unique constraint for entity name per type."""
    content = MIGRATION_FILE.read_text()
    assert "knowledge_entities_name_entity_type_unique" in content


def test_document_title_nonempty_check():
    """Test SQL contains the document title non-empty check."""
    content = MIGRATION_FILE.read_text()
    assert "knowledge_documents_title_nonempty" in content


def test_chunk_content_nonempty_check():
    """Test SQL contains the chunk content non-empty check."""
    content = MIGRATION_FILE.read_text()
    assert "knowledge_chunks_content_nonempty" in content


def test_entity_name_nonempty_check():
    """Test SQL contains the entity name non-empty check."""
    content = MIGRATION_FILE.read_text()
    assert "knowledge_entities_name_nonempty" in content


def test_all_constraints_use_drop_if_exists():
    """Test that every ADD CONSTRAINT is preceded by DROP CONSTRAINT IF EXISTS."""
    content = MIGRATION_FILE.read_text()
    
    lines = content.split('\n')
    add_constraint_lines = []
    drop_constraint_lines = []
    
    for i, line in enumerate(lines):
        if 'ADD CONSTRAINT' in line:
            add_constraint_lines.append(i)
        elif 'DROP CONSTRAINT IF EXISTS' in line:
            drop_constraint_lines.append(i)
    
    # For each ADD CONSTRAINT line, check if there's a DROP CONSTRAINT IF EXISTS before it
    for add_line_idx in add_constraint_lines:
        # Find the most recent DROP CONSTRAINT IF EXISTS before this ADD CONSTRAINT
        relevant_drops = [drop_idx for drop_idx in drop_constraint_lines if drop_idx < add_line_idx]
        assert len(relevant_drops) > 0, f"No DROP CONSTRAINT IF EXISTS found before ADD CONSTRAINT at line {add_line_idx}"
        
        # Check that there's a DROP CONSTRAINT that matches the ADD CONSTRAINT
        add_line = lines[add_line_idx]
        constraint_name_in_add = ""
        if "ADD CONSTRAINT" in add_line:
            part_after_add = add_line.split("ADD CONSTRAINT")[1].strip()
            constraint_name_in_add = part_after_add.split()[0]
            
        found_match = False
        for drop_idx in relevant_drops:
            drop_line = lines[drop_idx]
            if constraint_name_in_add in drop_line and "IF EXISTS" in drop_line:
                found_match = True
                break
                
        assert found_match, f"No matching DROP CONSTRAINT IF EXISTS found for ADD CONSTRAINT {constraint_name_in_add}"


def test_no_drop_column_statements():
    """Test that migration is additive only (no DROP COLUMN statements)."""
    content = MIGRATION_FILE.read_text()
    assert "DROP COLUMN" not in content


def test_sources_name_nonempty_check():
    """Test SQL contains the sources name non-empty check."""
    content = MIGRATION_FILE.read_text()
    assert "knowledge_sources_name_nonempty" in content
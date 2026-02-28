#!/usr/bin/env python3
"""
Script to auto-generate schema documentation from SQL migration files.
"""
from __future__ import annotations
import re
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List


def parse_sql_file(file_path: Path) -> dict[str, List[dict[str, Any]]]:
    """
    Parse SQL migration file and extract table, index, function and RLS definitions.
    """
    content = file_path.read_text()

    result: dict[str, Any] = {
        'tables': [],
        'indexes': [],
        'functions': [],
        'rls_tables': []
    }
    
    # The approach will be to use simple pattern matching, 
    # then combine statements that span multiple physical lines
    
    # Join multiple lines together where needed - statements that don't end with semicolon
    statements = []
    current_stmt = ""
    lines = content.splitlines()
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('--') or stripped.startswith('/*'):
            continue  # Skip empty lines and comments
        current_stmt += " " + stripped
        if stripped.endswith(';'):
            statements.append(current_stmt.strip())
            current_stmt = ""
    
    # Just finalize any leftover partial stmt
    if current_stmt.strip():
        statements.append(current_stmt.strip())
    
    for statement in statements:
        statement_lower = statement.lower()
        
        # Create Table (may or may not have IF NOT EXISTS)
        if 'create table' in statement_lower:
            # Use flexible matching to find table name in various formats
            table_patterns = [
                r'create\s+table\s+(?:if\s+not\s+exists\s+)?(?:[a-z_]+\.)?([a-z_][a-z0-9_]*)',
            ]
            
            table_name = None
            for pattern in table_patterns:
                match = re.search(pattern, statement, re.IGNORECASE)
                if match:
                    table_name = match.group(1)
                    break
            
            if table_name:
                # Find comment above within reasonable distance
                comment = ""
                pos = content.find(statement)
                if pos > 0:
                    prefix = content[:pos]
                    lines_above = prefix.split('\n')
                    # Look for the closest comment
                    for i in range(len(lines_above)-1, max(-1, len(lines_above)-10), -1):
                        line = lines_above[i].strip()
                        if line.startswith('--'):
                            comment = line[2:].strip()
                            break
                
                result['tables'].append({
                    'name': table_name,
                    'definition': statement,
                    'comment': comment
                })
        
        # Create Index
        elif 'create index' in statement_lower:
            index_patterns = [
                r'create\s+index\s+(?:if\s+not\s+exists\s+)?([a-z_][a-z0-9_]*)',
            ]
            
            index_name = None
            for pattern in index_patterns:
                match = re.search(pattern, statement, re.IGNORECASE)
                if match:
                    index_name = match.group(1)
                    break
            
            if index_name:
                result['indexes'].append({
                    'name': index_name,
                    'definition': statement
                })
        
        # Create Function
        elif 'create or replace function' in statement_lower:
            func_match = re.search(r'create or replace function\s+([a-z_][a-zA-Z0-9_]*)', statement, re.IGNORECASE)
            if func_match:
                func_name = func_match.group(1)
                
                # For functions, we want to identify RETURN type and signature
                returns_match = re.search(r'RETURNS\s+(.+?)(?:\s+LANGUAGE|\s+STABLE|\s+SECURITY|\s+AS\s+\$\$|$)', statement, re.IGNORECASE)
                return_type = returns_match.group(1).strip() if returns_match else "unknown"
                
                result['functions'].append({
                    'name': func_name,
                    'signature': statement.split('returns')[0].strip() if 'returns' in statement_lower else func_name,
                    'return_type': return_type,
                    'definition': statement
                })
        
        # Row Level Security
        elif 'alter table' in statement_lower and 'enable row level security' in statement_lower:
            rls_match = re.search(r'alter\s+table\s+([a-z_][a-zA-Z0-9_]*)\s+enable\s+row\s+level\s+security', statement, re.IGNORECASE)
            if rls_match:
                result['rls_tables'].append(rls_match.group(1))

    return result


def parse_table_columns(table_definition: str) -> List[Dict[str, str]]:
    """Parse CREATE TABLE definition to extract column information."""
    # Extract content between main parentheses
    # Find the opening and closing of the column definition 
    # by finding the first opening paren and the matching closing one
    
    paren_start = table_definition.find('(')
    if paren_start == -1:
        return []
    
    # Track parentheses to find the matching closing paren
    level = 0
    paren_end = -1
    in_string = False
    string_delimiter = ''
    
    for i in range(paren_start, len(table_definition)):
        char = table_definition[i]
        
        # Handle string literals carefully so we don't count parens inside strings
        if char in ["'", '"', '`'] and (i == 0 or table_definition[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_delimiter = char
            elif char == string_delimiter:
                in_string = False
            continue  # Don't process other characters while in string
        
        if in_string:
            continue
            
        if char == '(':
            level += 1
        elif char == ')':
            level -= 1
            if level == 0:
                paren_end = i
                break

    if paren_end == -1:
        return []
    
    columns_area = table_definition[paren_start+1 : paren_end]
    
    # Now parse the individual column definitions by splitting on commas at the correct level
    column_defs = []
    current_col = ""
    level = 0
    in_str = False
    str_delim = ''
    
    for i, char in enumerate(columns_area):
        if char in ['"', "'", '`'] and (i == 0 or columns_area[i-1] != '\\'):
            if not in_str:
                in_str = True
                str_delim = char
            elif char == str_delim:
                in_str = False
        elif in_str:
            current_col += char
        elif char == '(':
            level += 1
            current_col += char
        elif char == ')':
            level -= 1
            current_col += char
        elif char == ',' and level == 0:
            column_defs.append(current_col.strip())
            current_col = ""
        else:
            current_col += char
    
    if current_col.strip():
        column_defs.append(current_col.strip())
    
    # Now process each column definition
    columns = []
    constraint_starts = ('CONSTRAINT', 'PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK')
    
    for cdef in column_defs:
        cdef = cdef.strip()
        if not cdef:
            continue
            
        # Skip table-level constraints
        uppercase_cdef = cdef.upper().strip()
        is_table_constraint = False
        for constraint_start in constraint_starts:
            if uppercase_cdef.startswith(constraint_start):
                is_table_constraint = True
                break
        
        if is_table_constraint:
            continue  # Skip this - it's a table-level constraint, not a column
        
        # Parse: [name] [type] [attributes...]
        parts = cdef.split(None)  # split on any whitespace
        if len(parts) < 2:
            continue  # Not a valid column definition
            
        col_name = parts[0]
        # The type is likely the second token
        col_type = parts[1]
        
        # Anything beyond index 1 might be constraints/defaults/etc
        attributes = parts[2:] if len(parts) > 2 else []
        
        # Refinement: Some types have parentheses (e.g., varchar(255), vector(1024))
        # and the next part might actually be part of the type
        
        # Check if the current type has an opening parenthesis
        # If so, and there's more in attributes, extend type to accommodate the complete type
        temp_type = col_type
        i = 0
        while i < len(attributes):
            next_part = attributes[i]
            temp_type += ' ' + next_part
            if '(' in next_part and ')' not in next_part:
                # The type continues, need to find closing
                while ')' not in next_part and i+1 < len(attributes):
                    i += 1
                    next_part = attributes[i]
                    temp_type += ' ' + next_part
            elif '(' in temp_type and ')' in temp_type:
                # We've got the complete type
                break
            # If next part looks like a constraint we don't expect in a type, stop extending type
            elif next_part.upper() in ['NOT', 'NULL', 'DEFAULT', 'REFERENCES', 'PRIMARY', 'CHECK', 'UNIQUE']:
                break
            else:
                break
            i += 1
        
        # Settle the proper type
        actual_type = temp_type
        # And the remaining becomes constraints
        actual_constraints = ' '.join(attributes[i+1:]) if i+1 < len(attributes) else ''
        
        columns.append({
            'name': col_name,
            'type': actual_type,
            'constraints': actual_constraints.strip()
        })

    return columns


def find_table_indexes(table_name: str, all_indexes: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """Find all indexes related to a specific table."""
    table_indexes = []
    for idx in all_indexes:
        # Check if this index is defined on the given table
        # Pattern: CREATE INDEX ... ON table_name ...
        index_def_lower = idx['definition'].lower()
        if f'on {table_name}' in index_def_lower or f'on {table_name} ' in index_def_lower:
            table_indexes.append(idx)
    return table_indexes


def generate_markdown_docs(parser_results: List[dict[str, Any]]) -> str:
    """Generate markdown documentation for all parsed migration files."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown = f"""# Database Schema Documentation

*Generated on {timestamp} from migration files*

---

"""
    
    # Collect all indexes, functions and RLS for later association with specific tables
    all_indexes = []
    all_functions = []
    all_rls_tables = set()
    
    for result in parser_results:
        all_indexes.extend(result['indexes'])
        all_functions.extend(result['functions'])
        all_rls_tables.update(result['rls_tables'])
    
    # Process each table from all migrations
    for result in parser_results:
        for table in result['tables']:
            markdown += f"## Table: `{table['name']}`\n\n"
            
            if table.get('comment'):
                markdown += f"_Description_: {table['comment']}\n\n"
            
            # Add RLS indicator
            if table['name'] in all_rls_tables:
                markdown += "*Row Level Security enabled*\n\n"
            
            markdown += "### Columns:\n\n"
            
            columns = parse_table_columns(table['definition'])
            if columns:
                # Create table header
                markdown += "| Name | Type | Constraints |\n"
                markdown += "|------|------|-------------|\n"
                
                for col in columns:
                    col_name = col['name']
                    col_type = col['type']
                    constraints = col.get('constraints', '') or ""
                    constraints = constraints.replace('\n', ' ').replace('|', '&#124;')  # Escape pipe chars
                    
                    markdown += f"| `{col_name}` | `{col_type}` | {constraints} |\n"
            else:
                markdown += "No columns found.\n\n"
            
            # Find and show indexes for this table
            table_indexes = find_table_indexes(table['name'], all_indexes)
            if table_indexes:
                markdown += "\n### Indexes:\n\n"
                for idx in table_indexes:
                    # Clean up the definition for display
                    desc = idx['definition'].replace('\n', ' ')[:100] + ('...' if len(idx['definition'].replace('\n', ' ')) > 100 else '')
                    markdown += f"- `{idx['name']}`: {desc}\n"
            
            markdown += "\n---\n\n"
    
    # Add functions if any
    if all_functions:
        markdown += "## Functions\n\n"
        for func in all_functions:
            markdown += f"### `{func['name']}`\n\n"
            markdown += f"**Signature**: ```sql\n{func['signature']}\n```\n\n"
            markdown += f"**Returns**: `{func['return_type']}`\n\n"
            # Use the function definition in triple codeblocks
            markdown += f"**Definition**: ```sql\n{func['definition']}\n```\n\n"
    
    return markdown


def main() -> None:
    migrations_dir = Path.cwd() / "backend" / "migrations"
    
    if not migrations_dir.exists():
        print("Error: migrations directory not found")
        return
    
    # Find all SQL migration files and sort by name (order matters!)
    migration_files = sorted(list(migrations_dir.glob("*.sql")))
    
    if not migration_files:
        print("Error: no migration files found")
        return
    
    # Parse all migration files
    all_parser_results = []
    for mig_file in migration_files:
        print(f"Parsing {mig_file.name}...")
        parser_result = parse_sql_file(mig_file)
        all_parser_results.append(parser_result)
    
    # Generate markdown documentation
    markdown_content = generate_markdown_docs(all_parser_results)
    
    # Write the documentation
    docs_dir = Path.cwd() / "backend" / "docs"
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True)
    
    docs_file = docs_dir / "schema.md"
    docs_file.write_text(markdown_content)
    
    print(f"Schema documentation generated successfully at: {docs_file}")
    print(f"Documentation extracted from {len(migration_files)} migration file(s)")


if __name__ == "__main__":
    main()
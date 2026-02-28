#!/usr/bin/env python3
"""
Migration Policy Checker: Ensures SQL migrations are additive-only.

This script scans migration files for destructive operations that break
the additive-migration policy. Usage with --file checks a single file;
by default, scans all .sql files in backend/migrations/.
"""
import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


def find_sql_files(migrations_dir: Path) -> List[Path]:
    """Find all .sql files in the migrations directory."""
    return list(migrations_dir.glob("*.sql"))


def check_file_for_destructive_sql(filepath: Path) -> Tuple[List[str], List[str]]:
    """
    Check a single SQL file for destructive patterns.
    
    Returns tuple of (failures, warnings) lists.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert to lower case for case-insensitive matching, preserving original for context
    lower_content = content.lower()

    failures = []
    warnings = []

    # Destructive patterns (these cause failures)
    destructive_patterns = [
        (r'\bdrop\s+table\b', "DROP TABLE detected (destructive)"),
        (r'\bdrop\s+column\b', "DROP COLUMN detected (destructive)"),
        (r'\balter\s+table\s+\w+\s+alter\s+column\s+\w+\s+type\s+varchar', 
         "ALTER COLUMN ... TYPE varchar detected (type narrowing, destructive)"),
        (r'\balter\s+table\s+\w+\s+alter\s+column\s+\w+\s+type\s+char', 
         "ALTER COLUMN ... TYPE char detected (type narrowing, destructive)"),
        (r'\balter\s+table\s+\w+\s+alter\s+column\s+\w+\s+type\s+\w+\(\d+\)(?!\s+using)', 
         "ALTER COLUMN TYPE with length specification (potentially destructive - use 'USING' if needed)"),
        (r'\btruncate\b', "TRUNCATE detected (destructive)"),
        (r'\bdelete\s+from\s+\w+(?!\s+where)', "DELETE FROM without WHERE clause (destructive)"),
        # More specific ALTER TYPE patterns (narrowing conversions)
        (r'\balter\s+table\s+\w+\s+alter\s+column\s+\w+\s+type\s+(tinyint|smallint|integer)(?!\s+using)', 
         "ALTER COLUMN TYPE with narrowed numeric type (destructive)")
    ]

    # Warning patterns (not failures but warnings)
    warning_patterns = [
        (r'\balter\s+table\s+\w+\s+alter\s+column\s+\w+\s+drop\s+not\s+null', 
         "ALTER COLUMN ... DROP NOT NULL (warning - removing constraint)"),
        (r'\balter\s+table\s+\w+\s+alter\s+column\s+\w+\s+drop\s+default', 
         "ALTER COLUMN ... DROP DEFAULT (warning - removing constraint)"),
        (r'\bdrop\s+index\b', "DROP INDEX detected (warning - consider this)")
    ]

    # Check for failures
    for pattern, message in destructive_patterns:
        if re.search(pattern, lower_content, re.IGNORECASE | re.MULTILINE):
            failures.append(message)

    # Check for warnings
    for pattern, message in warning_patterns:
        if re.search(pattern, lower_content, re.IGNORECASE | re.MULTILINE):
            warnings.append(message)

    # Special context-aware processing for allowed patterns
    # Remove false positives for DROP CONSTRAINT IF EXISTS followed by ADD CONSTRAINT
    lines = content.splitlines()
    i = 0
    skip_failures = []  # Keep track of failures to skip
    while i < len(lines):
        line_lower = lines[i].lower().strip()
        
        # Handle the allowed DROP CONSTRAINT IF EXISTS ... followed by ADD CONSTRAINT pattern
        if 'drop constraint' in line_lower and 'if exists' in line_lower:
            # Look ahead to see if next several lines contain matching ADD CONSTRAINT
            found_matching_add = False
            j = i + 1
            # Look for the nearest ADD CONSTRAINT (up to several lines away)
            while j < min(i + 10, len(lines)) and not found_matching_add:
                if 'add constraint' in lines[j].lower():
                    # Consider this an allowed pattern and potentially remove related false positives
                    found_matching_add = True
                    # Check if this specific drop/add is for similar constraint name to be extra safe
                    drop_match = re.search(r'drop\s+constraint\s+if\s+exists\s+(\w+)', line_lower)
                    add_match = re.search(r'add\s+constraint\s+(\w+)', lines[j].lower()) 
                    if drop_match and add_match:
                        drop_name = drop_match.group(1)
                        add_name = add_match.group(1)
                        # Usually they are related if they share common root (e.g., mytable_col_check)  
                        if drop_name.replace('_drop', '').replace('_del', '') == \
                           add_name.replace('_add', '').replace('_new', ''):
                             # This is definitely a known update pattern, skip processing any constraint violations 
                             # that might result from this sequence
                             skip_failures.extend([msg for msg in failures if 'constraint' in msg.lower()])
                    break
                j += 1
                    
        i += 1

    # Remove any false positives from warnings/failures based on context
    actual_failures = [f for f in failures if f not in skip_failures]

    return actual_failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SQL migration files for destructive operations")
    parser.add_argument("--file", help="Check a single file")
    parser.add_argument("--directory", "-d", default="backend/migrations", 
                        help="Directory to scan for SQL files (default: backend/migrations)")
    
    args = parser.parse_args()

    if args.file:
        # Check single file
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"ERROR: File {filepath} does not exist", file=sys.stderr)
            return 1

        failures, warnings = check_file_for_destructive_sql(filepath)
        
        if failures or warnings:
            print(f"MIGRATION POLICY CHECK for {filepath}:")
            
            if warnings:
                print("WARNINGS (non-fatal):")
                for warning in warnings:
                    print(f"  WARNING: {warning}")
                
            if failures:
                print("FAILURES (will fail CI):")
                for failure in failures:
                    print(f"  FAILURE: {failure}")
                print(f"\nFILE ANALYSIS - {filepath.name}: FAILED")
                return 1
            else:
                print(f"\nFILE ANALYSIS - {filepath.name}: OK")
                # Still show warnings separately if any 
                if warnings:
                    print("  Note: Warnings found (these won't cause CI failure)")
                else:
                    print("  Status: All good")
        else:
            print(f"MIGRATION POLICY CHECK - {filepath.name}: OK All good")
        
        return 0
    else:
        # Check all migration files
        migrations_dir = Path(args.directory)
        if not migrations_dir.exists():
            print(f"ERROR: Directory {migrations_dir} does not exist", file=sys.stderr)
            return 1

        sql_files = find_sql_files(migrations_dir)
        
        if not sql_files:
            print(f"No SQL files found in {migrations_dir}", file=sys.stderr)
            return 1

        total_failures = 0
        print(f"Scanning {len(sql_files)} migration file(s)...")
        
        for sql_file in sql_files:
            failures, warnings = check_file_for_destructive_sql(sql_file)
            
            if failures or warnings:
                print(f"\nMIGRATION POLICY CHECK for {sql_file.name}:")
                
                if warnings:
                    print("  WARNINGS (non-fatal):")
                    for warning in warnings:
                        print(f"    WARNING: {warning}")
                        
                if failures:
                    print("  FAILURES (will fail CI):")
                    for failure in failures:
                        print(f"    FAILURE: {failure}")
                    print("  RESULT: FAILED")
                    total_failures += 1
                else:
                    print("  RESULT: OK (with warnings)")
            else:
                print(f"{sql_file.name}: OK")

        if total_failures > 0:
            print(f"\nOVERALL: FAILED {total_failures} of {len(sql_files)} files had policy violations")
            return 1
        else:
            print(f"\nOVERALL: OK All {len(sql_files)} files passed migration policy check")
            return 0


if __name__ == "__main__":
    sys.exit(main())
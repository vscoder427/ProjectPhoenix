#!/usr/bin/env python3
"""
Execute the row count SQL script against Supabase database.
Related Issue: #17
"""

import os
import sys
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed")
    print("Install with: pip install supabase")
    sys.exit(1)

# Load environment variables
workspace_env = Path(__file__).parent.parent.parent / ".env.workspace"
if workspace_env.exists():
    with open(workspace_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

# Get Supabase credentials
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    print("Check .env.workspace file")
    sys.exit(1)

print(f"Connecting to Supabase: {url}")
print()

# Create Supabase client
supabase: Client = create_client(url, key)

# Read the SQL script
sql_file = Path(__file__).parent / "count-all-table-rows.sql"
with open(sql_file) as f:
    sql = f.read()

print("Executing SQL query to count rows in all tables...")
print("This may take a minute for large databases...")
print()

try:
    # Execute the SQL using Supabase RPC or direct query
    # Note: Supabase client doesn't directly support arbitrary SQL
    # We'll use the REST API to query information_schema

    # Get all tables
    result = supabase.rpc(
        'exec_sql',
        {
            'query': """
                SELECT
                    table_schema,
                    table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                  AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name
            """
        }
    ).execute()

    tables = result.data
    print(f"Found {len(tables)} tables")
    print()

    # Count rows in each table
    row_counts = []
    for table in tables:
        schema = table['table_schema']
        name = table['table_name']

        try:
            # Count rows using Supabase select
            if schema == 'public':
                count_result = supabase.table(name).select('*', count='exact').limit(0).execute()
                count = count_result.count
            else:
                # For non-public schemas, we need raw SQL
                continue

            # Categorize by size
            if count == 0:
                category = "Empty"
            elif count < 100:
                category = "<100 rows"
            elif count < 1000:
                category = "<1,000 rows"
            elif count < 10000:
                category = "<10,000 rows"
            else:
                category = ">10,000 rows"

            row_counts.append({
                'schema': schema,
                'table': name,
                'count': count,
                'category': category
            })

        except Exception as e:
            print(f"  Warning: Could not count {schema}.{name}: {e}")
            row_counts.append({
                'schema': schema,
                'table': name,
                'count': None,
                'category': "Error"
            })

    # Sort by count descending
    row_counts.sort(key=lambda x: x['count'] if x['count'] is not None else -1, reverse=True)

    # Print results
    print("\n" + "="*80)
    print("TABLE ROW COUNTS")
    print("="*80)
    print(f"{'Schema':<15} {'Table Name':<40} {'Row Count':>12} {'Category':<15}")
    print("-"*80)

    for row in row_counts:
        count_str = str(row['count']) if row['count'] is not None else "N/A"
        print(f"{row['schema']:<15} {row['table']:<40} {count_str:>12} {row['category']:<15}")

    # Print summary statistics
    valid_counts = [r['count'] for r in row_counts if r['count'] is not None]

    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    total_tables = len(row_counts)
    empty = sum(1 for r in row_counts if r['count'] == 0)
    small = sum(1 for r in row_counts if r['count'] and 0 < r['count'] < 100)
    medium = sum(1 for r in row_counts if r['count'] and 100 <= r['count'] < 1000)
    large = sum(1 for r in row_counts if r['count'] and 1000 <= r['count'] < 10000)
    xlarge = sum(1 for r in row_counts if r['count'] and r['count'] >= 10000)
    total_rows = sum(valid_counts)

    print(f"Total Tables:           {total_tables}")
    print(f"Empty Tables:           {empty}")
    print(f"Tables <100 rows:       {small}")
    print(f"Tables <1,000 rows:     {medium}")
    print(f"Tables <10,000 rows:    {large}")
    print(f"Tables >10,000 rows:    {xlarge}")
    print(f"Total Rows (all):       {total_rows:,}")
    print()

    # Generate markdown table for issue comment
    print("="*80)
    print("MARKDOWN FOR ISSUE #17")
    print("="*80)
    print()
    print("### Row Count Results")
    print()
    print("| Schema | Table Name | Row Count | Category |")
    print("|--------|-----------|-----------|----------|")

    for row in row_counts[:20]:  # Top 20 tables
        count_str = f"{row['count']:,}" if row['count'] is not None else "N/A"
        print(f"| {row['schema']} | {row['table']} | {count_str} | {row['category']} |")

    if len(row_counts) > 20:
        print(f"\n...and {len(row_counts) - 20} more tables")

    print()
    print("### Summary")
    print()
    print(f"- **Total Tables:** {total_tables}")
    print(f"- **Empty Tables:** {empty}")
    print(f"- **Tables with data:** {total_tables - empty}")
    print(f"- **Total rows across all tables:** {total_rows:,}")

except Exception as e:
    print(f"Error executing query: {e}")
    print()
    print("Note: Direct SQL execution may not be supported via Supabase client.")
    print("Please use one of these methods instead:")
    print()
    print("1. Supabase SQL Editor (Dashboard)")
    print("   - Go to: https://supabase.com/dashboard/project/flisguvsodactmddejqz")
    print("   - Navigate to SQL Editor")
    print("   - Copy/paste the SQL from count-all-table-rows.sql")
    print()
    print("2. psql command line:")
    print(f"   psql 'postgresql://postgres:[PASSWORD]@db.flisguvsodactmddejqz.supabase.co:5432/postgres'")
    print()
    sys.exit(1)

print()
print("✅ Query completed successfully!")
print()
print("Next steps:")
print("1. Copy the markdown section above")
print("2. Post as comment on issue #17")
print("3. Use findings to inform database migration planning")

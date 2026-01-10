#!/usr/bin/env python3
"""
Execute row count query using Supabase REST API.
Simpler approach that queries each table individually.
Related Issue: #17
"""

import os
import sys
import requests
from pathlib import Path

# Get Supabase credentials from parent directory
url = os.getenv("SUPABASE_URL", "https://flisguvsodactmddejqz.supabase.co")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not key:
    print("Error: SUPABASE_SERVICE_KEY environment variable must be set")
    sys.exit(1)

print(f"Connecting to Supabase: {url}")
print()

# Known tables from Employa schema (from previous work)
# We'll query these directly
known_tables = [
    "profiles",
    "user_profiles",
    "career_goals",
    "career_paths",
    "job_applications",
    "job_postings",
    "conversations",
    "messages",
    "aa_meetings",
    "meeting_attendance",
    "recovery_milestones",
    "skills",
    "user_skills",
    "endorsements",
    "connections",
    "notifications",
    "system_logs",
    "api_keys",
    "webhooks",
    "integrations"
]

print("Querying table row counts...")
print("Note: Only querying known public schema tables")
print()

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "count=exact"
}

row_counts = []

for table in known_tables:
    try:
        # Query with count only, no data
        response = requests.get(
            f"{url}/rest/v1/{table}",
            headers=headers,
            params={"select": "id", "limit": 0}
        )

        if response.status_code == 200:
            # Content-Range header contains the count
            content_range = response.headers.get('content-range', '')
            if content_range:
                # Format: "0-0/123" where 123 is total count
                count = int(content_range.split('/')[-1])
            else:
                count = 0

            # Categorize
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
                'schema': 'public',
                'table': table,
                'count': count,
                'category': category
            })
            print(f"✓ {table}: {count:,} rows")

        elif response.status_code == 404:
            print(f"  (table {table} does not exist)")
        else:
            print(f"  Warning: {table} - HTTP {response.status_code}")

    except Exception as e:
        print(f"  Error querying {table}: {e}")

# Sort by count
row_counts.sort(key=lambda x: x['count'], reverse=True)

# Print results
print("\n" + "="*80)
print("TABLE ROW COUNTS")
print("="*80)
print(f"{'Schema':<10} {'Table Name':<30} {'Row Count':>15} {'Category':<15}")
print("-"*80)

for row in row_counts:
    print(f"{row['schema']:<10} {row['table']:<30} {row['count']:>15,} {row['category']:<15}")

# Summary
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

total_tables = len(row_counts)
empty = sum(1 for r in row_counts if r['count'] == 0)
small = sum(1 for r in row_counts if 0 < r['count'] < 100)
medium = sum(1 for r in row_counts if 100 <= r['count'] < 1000)
large = sum(1 for r in row_counts if 1000 <= r['count'] < 10000)
xlarge = sum(1 for r in row_counts if r['count'] >= 10000)
total_rows = sum(r['count'] for r in row_counts)

print(f"Tables Queried:         {total_tables}")
print(f"Empty Tables:           {empty}")
print(f"Tables <100 rows:       {small}")
print(f"Tables <1,000 rows:     {medium}")
print(f"Tables <10,000 rows:    {large}")
print(f"Tables >10,000 rows:    {xlarge}")
print(f"Total Rows:             {total_rows:,}")
print()
print(f"Note: Only queried {total_tables} known public schema tables.")
print(f"Actual database may have more tables. Use Supabase SQL Editor for complete list.")

# Generate markdown
print("\n" + "="*80)
print("MARKDOWN FOR ISSUE #17")
print("="*80)
print()
print("### Row Count Results (Sample)")
print()
print("Queried known public schema tables:")
print()
print("| Table Name | Row Count | Category |")
print("|-----------|-----------|----------|")

for row in row_counts:
    print(f"| {row['table']} | {row['count']:,} | {row['category']} |")

print()
print("### Summary")
print()
print(f"- **Tables queried:** {total_tables}")
print(f"- **Empty tables:** {empty}")
print(f"- **Tables with data:** {total_tables - empty}")
print(f"- **Total rows:** {total_rows:,}")
print()
print("**Note:** This is a sample of known tables. For complete database audit, use the SQL script in Supabase SQL Editor.")

print("\n✅ Query completed!")

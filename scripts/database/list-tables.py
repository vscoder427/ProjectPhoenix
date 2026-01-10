#!/usr/bin/env python3
"""
List all tables in Supabase database using PostgREST API.
"""
import os
import sys
import requests

url = os.getenv("SUPABASE_URL", "https://flisguvsodactmddejqz.supabase.co")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not key:
    print("Error: SUPABASE_SERVICE_KEY required")
    sys.exit(1)

print(f"Connecting to: {url}")
print()

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "count=exact"
}

# Try to get tables from information_schema
# Note: This requires RLS policy or service role access
response = requests.get(
    f"{url}/rest/v1/",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    tables = [d['name'] for d in data.get('definitions', {}).values()]
    print(f"Found {len(tables)} tables via OpenAPI schema:")
    for table in sorted(tables):
        print(f"  - {table}")
else:
    print(f"Could not fetch schema: HTTP {response.status_code}")
    print(response.text[:500])

print()
print("To get complete table list with row counts, use Supabase SQL Editor:")
print("https://supabase.com/dashboard/project/flisguvsodactmddejqz/editor")

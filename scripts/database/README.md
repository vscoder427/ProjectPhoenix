# Database Scripts

Utility scripts for Supabase database auditing and maintenance.

## Scripts

### count-all-table-rows.sql

**Purpose:** Query row counts for all tables in the Supabase database

**Related Issue:** [#17 - Database Audit: Query Row Counts](https://github.com/vscoder427/ProjectPhoenix/issues/17)

**Usage:**

#### Option 1: Supabase SQL Editor (Recommended)

1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/flisguvsodactmddejqz
2. Navigate to: **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy and paste the contents of `count-all-table-rows.sql`
5. Click **Run** or press `Ctrl+Enter`

#### Option 2: psql Command Line

```bash
# Connect to Supabase database
psql "postgresql://postgres:[PASSWORD]@db.flisguvsodactmddejqz.supabase.co:5432/postgres"

# Run the script
\i scripts/database/count-all-table-rows.sql
```

#### Option 3: Using supabase CLI

```bash
# If you have supabase CLI installed and linked
supabase db execute --file scripts/database/count-all-table-rows.sql
```

**Output:**

The script produces two result sets:

1. **Detailed Table List** - All tables with row counts, ordered by size (largest first)
   - Schema name
   - Table name
   - Row count
   - Size category (Empty, <100 rows, <1,000 rows, etc.)

2. **Summary Statistics** - Aggregate statistics
   - Total tables
   - Count by size category
   - Total rows across all tables

**Example Output:**

```
Schema  | Table Name           | Row Count | Size Category
--------+----------------------+-----------+---------------
public  | user_profiles        | 15234     | >10,000 rows
public  | career_goals         | 8542      | <10,000 rows
public  | aa_meetings          | 1256      | <10,000 rows
public  | job_applications     | 0         | Empty
...

Total Tables: 98
Empty Tables: 23
Tables <100 rows: 15
Tables <1,000 rows: 28
Tables <10,000 rows: 22
Tables >10,000 rows: 10
Total Rows: 245,678
```

## Database Connection Info

**Supabase Instance:** `flisguvsodactmddejqz`

**Connection Details:**
- Available in workspace `.env.workspace` file
- See workspace CLAUDE.md for Supabase configuration

**Security Note:** Never commit connection strings or passwords to the repository. Use GCP Secret Manager or environment variables.

## Related Documentation

- [Database Isolation & Migrations Standard](../../docs/standards/db-isolation-migrations.md)
- [Data Governance Standard](../../docs/standards/compliance/data-governance.md)
- [Supabase Configuration](../../CLAUDE.md#supabase-configuration) (workspace-level)

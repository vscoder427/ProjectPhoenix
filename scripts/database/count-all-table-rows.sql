-- Database Audit: Row Counts for All Tables
-- Purpose: Query row counts for all tables in the Supabase database
-- Related Issue: #17
-- Usage: Run this in Supabase SQL Editor or via psql
--
-- This script queries the information_schema to get all tables,
-- then dynamically counts rows in each table.

-- Create a temporary table to store results
CREATE TEMP TABLE IF NOT EXISTS table_row_counts (
    schema_name TEXT,
    table_name TEXT,
    row_count BIGINT
);

-- Generate and execute row count queries for all user tables
DO $$
DECLARE
    r RECORD;
    row_count BIGINT;
BEGIN
    -- Loop through all tables in public schema and custom schemas
    FOR r IN
        SELECT
            table_schema,
            table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name
    LOOP
        -- Execute count query for each table
        EXECUTE format('SELECT COUNT(*) FROM %I.%I', r.table_schema, r.table_name)
        INTO row_count;

        -- Insert result into temp table
        INSERT INTO table_row_counts (schema_name, table_name, row_count)
        VALUES (r.table_schema, r.table_name, row_count);
    END LOOP;
END $$;

-- Display results ordered by row count (descending)
SELECT
    schema_name AS "Schema",
    table_name AS "Table Name",
    row_count AS "Row Count",
    CASE
        WHEN row_count = 0 THEN 'Empty'
        WHEN row_count < 100 THEN '<100 rows'
        WHEN row_count < 1000 THEN '<1,000 rows'
        WHEN row_count < 10000 THEN '<10,000 rows'
        ELSE '>10,000 rows'
    END AS "Size Category"
FROM table_row_counts
ORDER BY row_count DESC, schema_name, table_name;

-- Summary statistics
SELECT
    COUNT(*) AS "Total Tables",
    SUM(CASE WHEN row_count = 0 THEN 1 ELSE 0 END) AS "Empty Tables",
    SUM(CASE WHEN row_count > 0 AND row_count < 100 THEN 1 ELSE 0 END) AS "Tables <100 rows",
    SUM(CASE WHEN row_count >= 100 AND row_count < 1000 THEN 1 ELSE 0 END) AS "Tables <1,000 rows",
    SUM(CASE WHEN row_count >= 1000 AND row_count < 10000 THEN 1 ELSE 0 END) AS "Tables <10,000 rows",
    SUM(CASE WHEN row_count >= 10000 THEN 1 ELSE 0 END) AS "Tables >10,000 rows",
    SUM(row_count) AS "Total Rows Across All Tables"
FROM table_row_counts;

-- Optional: Export results as CSV-friendly format
-- Uncomment the following to get CSV output
/*
\copy (SELECT schema_name, table_name, row_count FROM table_row_counts ORDER BY row_count DESC) TO 'table_row_counts.csv' CSV HEADER;
*/

-- Clean up
DROP TABLE IF EXISTS table_row_counts;

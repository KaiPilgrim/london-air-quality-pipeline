
import duckdb
import subprocess
import sys
from datetime import date
from pathlib import Path
from fetch_data import site_codes, extract_measurements
from transform import get_year


def update_data(start, end, db_path="data/london_air_quality.duckdb"):

    #  Validation for dates and database
    if date.fromisoformat(start) >= date.fromisoformat(end):
        raise ValueError("End date must be after start date.")

    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    #  Extract or reuse raw JSON files
    raw_files = []

    for site in site_codes:
        filename = f"no2_{site}_{start}_{end}.json"
        filepath = Path("data/raw") / filename

        if not filepath.exists():
            extract_measurements(site, start, end)
        else:
            print(f"Already downloaded: {filename}")

        raw_files.append(filename)

    #  Connect to DuckDB database
    con = duckdb.connect(db_path)

    before = con.execute(
        "SELECT COUNT(*) FROM measurements"
    ).fetchone()[0]

        #  Create a temporary table
    con.execute("""
        CREATE TEMP TABLE temp_measurements AS
        SELECT *
        FROM measurements
        WHERE FALSE
    """)

    seen_keys = set()
    duplicate_source_keys = 0

    # Transform incoming records
    with con.appender("temp_measurements") as app:
        for filename in raw_files:
            for row in get_year(filename):
                key = (
                    row["site_code"],
                    row["pollutant_code"],
                    row["measured_at_gmt"]
                )

                if row["measured_at_gmt"] is None:
                        continue

                if key in seen_keys:
                    duplicate_source_keys += 1
                    continue

                seen_keys.add(key)

                app.append_row(
                    row["site_code"],
                    row["pollutant_code"],
                    row["measured_at_gmt"],
                    row["value"],
                    row["source_file"]
                )

    # Insert new measurements only
    con.execute("""
        INSERT OR IGNORE INTO measurements
        SELECT *
        FROM temp_measurements
    """)

    after = con.execute(
        "SELECT COUNT(*) FROM measurements"
    ).fetchone()[0]

    latest = con.execute("""
        SELECT MAX(measured_at_gmt)
        FROM measurements
    """).fetchone()[0]

    # Report results
    print(f"\nRecords before: {before}")
    print(f"Records after: {after}")
    print(f"New records added: {after - before}")
    print(f"Duplicate keys within new files: {duplicate_source_keys}")
    print(f"Latest measurement timestamp: {latest}")

    con.close()

    # Refresh dashboard exports for the main database
    if db_path == "data/london_air_quality.duckdb":
        subprocess.run(
            [sys.executable, "src/export_results.py"],
            check=True
        )

    return after - before


# =========================
# Testing
# =========================

"""
# Create a test copy:
#cp data/london_air_quality.duckdb data/test_update.duckdb 

# Example test:
update_data("2026-11-01", "2026-11-04","data/test_update.duckdb")

"""
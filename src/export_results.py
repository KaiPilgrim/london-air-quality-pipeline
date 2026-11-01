import duckdb
from pathlib import Path

# Connect to the existing database
con = duckdb.connect("data/london_air_quality.duckdb", read_only=True)

# Create the output folder if it doesn't exist
output_folder = Path("data/processed")
output_folder.mkdir(parents=True, exist_ok=True)

# SQL files and their corresponding output files
queries = {
    "annual_no2": "sql/annual_no2.sql",
    "monthly_no2": "sql/monthly_no2.sql",
    "ulez_comparison": "sql/ulez_comparison.sql"
}

for name, sql_file in queries.items():
    # Read the SQL query from its file
    with open(sql_file, "r") as f:
        query = f.read().strip().rstrip(";")

    output_file = output_folder / f"{name}.csv"

    # Execute the SQL and export its results directly
    con.execute(f"""
        COPY ({query})
        TO '{output_file}'
        (HEADER, DELIMITER ',')
    """)

    print(f"Exported: {output_file}")

con.close()

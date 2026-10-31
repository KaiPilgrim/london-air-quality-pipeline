import duckdb
from transform import clean_sites, clean_pollutants, valid_site_pollutants, full_measurements

# Links con variable to database. Creates if one does not exist. 
con = duckdb.connect("data/london_air_quality.duckdb")

# Creation of sites and pollutants table
con.execute("""
    CREATE OR REPLACE TABLE sites (
        site_code VARCHAR PRIMARY KEY,
        site_name VARCHAR,
        site_type VARCHAR,
        latitude DOUBLE,
        longitude DOUBLE,
        local_authority VARCHAR,
        date_opened DATE,
        date_closed DATE,
        data_owner VARCHAR,
        data_manager VARCHAR,
        site_url VARCHAR
    )
""")

con.execute("""
    CREATE OR REPLACE TABLE pollutants (
        pollutant_code VARCHAR PRIMARY KEY,
        pollutant_name VARCHAR,
        description VARCHAR,
        health_effect VARCHAR,
        info_url VARCHAR
    )
""")

con.execute("""
    CREATE OR REPLACE TABLE site_pollutants (
        site_code VARCHAR,
        pollutant_code VARCHAR,
        monitoring_started DATE,
        monitoring_finished DATE
    )
""")

con.execute("""
    CREATE OR REPLACE TABLE measurements(
        site_code VARCHAR,
        pollutant_code VARCHAR,
        measured_at_gmt TIMESTAMP,
        value DOUBLE,
        source_file VARCHAR,
        PRIMARY KEY (site_code, pollutant_code, measured_at_gmt)
    )
""")

# Populating tables

with con.appender("sites") as app:
    for site in clean_sites:
        app.append_row(
            site["site_code"],
            site["site_name"],
            site["site_type"],
            site["latitude"],
            site["longitude"],
            site["local_authority"],
            site["date_opened"],
            site["date_closed"],
            site["data_owner"],
            site["data_manager"],
            site["site_url"]
        )

with con.appender("pollutants") as app:
    for chemical in clean_pollutants:
        app.append_row(
            chemical["pollutant_code"],
            chemical["pollutant_name"],
            chemical["description"],
            chemical["health_effect"],
            chemical["info_url"]
        )

with con.appender("site_pollutants") as app:
    for entry in valid_site_pollutants:
        app.append_row(
            entry["site_code"],
            entry["pollutant_code"],
            entry["monitoring_started"],
            entry["monitoring_finished"]
        )

with con.appender("measurements") as app:
    for row in full_measurements:
        app.append_row(
            row["site_code"],
            row["pollutant_code"],
            row["measured_at_gmt"],
            row["value"],
            row["source_file"]
        )

print(con.execute("SELECT COUNT(*) FROM sites").fetchone()[0])
print(con.execute("SELECT COUNT(*) FROM pollutants").fetchone()[0])
print(con.execute("SELECT COUNT(*) FROM site_pollutants").fetchone()[0])
print(con.execute("SELECT COUNT(*) FROM measurements").fetchone()[0])


q = """
    SELECT sp.site_code, sp.pollutant_code
FROM site_pollutants sp
LEFT JOIN sites s ON sp.site_code = s.site_code
LEFT JOIN pollutants p ON sp.pollutant_code = p.pollutant_code
WHERE s.site_code IS NULL
   OR p.pollutant_code IS NULL;
"""

q2 = """
    SELECT COUNT(*) FROM measurements;
"""

q3 = """
    SELECT COUNT(*)
FROM measurements
WHERE value IS NULL;
"""
results = con.execute(q).fetchall()
results2 = con.execute(q2).fetchall()
results3 = con.execute(q3).fetchall()

print(f"Unmatched references: {len(results)}")
print(f"Total hourly records: {results2}")
print(f"Missing measurements: {results3}")
con.close()
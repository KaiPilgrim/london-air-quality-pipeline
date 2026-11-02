# London Air Quality Explorer

**How has nitrogen dioxide (NO₂) changed across selected London monitoring stations and what can we observe around the 2023 ULEZ expansion?**

This project takes air quality measurements from the London Air Quality Network (LAQN), turns API responses into structured data and presents the results in a simple dashboard. 

## What I built and who for

I wanted to investigate something that affects Londoners directly: whether air pollution levels have changed over time, particularly around the expansion of London's Ultra Low Emission Zone (ULEZ) in August 2023. I focused on nitrogen dioxide a pollutant closely associated with road traffic, to explore how measurements differed before and after the expansion.

I selected 11 monitoring stations across central and north London giving me a manageable dataset covering different locations and station histories. Using historical readings from 2016–2025 I built a data pipeline and dashboard to explore these changes over time.

The dashboard is intended for London residents and people working with local data who want to understand air quality trends without reading API responses or writing SQL. Users can select a station, explore annual and monthly NO₂ measurements and compare readings before and after the 2023 ULEZ expansion.

**This is an exploration of measured changes and not proof that ULEZ caused them.** The selected stations do not represent every part of London.

## The data

The data comes from the London Air Quality Network.

| | Historical dataset |
| --- | --- |
| Pollutant | Nitrogen dioxide (NO₂), measured in µg/m³ |
| Period | 1 January 2016 to 31 December 2025 |
| Monitoring stations | 11 selected sites |
| Raw readings | 110 annual JSON responses, plus 3 metadata JSON files |
| Hourly records loaded | 964,392 |
| Recorded readings | 826,573 |
| Missing readings | 137,819 |

The original API responses are kept in `data/raw/`, rather than being overwritten with cleaned data. This makes it possible to revisit the extraction and transformation steps. The three metadata files describe monitoring sites, pollutant definitions and which pollutants are monitored at each site.

### Cleaning and data quality

- Dates and timestamps are converted to appropriate types and measured values to numbers.
- Missing readings are stored as **NULL** and **not zero** so they do not falsely reduce the averages.
- Duplicate and invalid site pollutant records are excluded.
- The dashboard displays annual and monthly averages only when at least **75% of the API hourly rows** for that period contain a reading.

That last check assesses completeness among rows returned by the API, it does not independently verify that every expected hour was returned. Station coverage also varies over time with some stations having substantial gaps. These limitations matter when comparing sites or years.

## How it works

```text
LAQN API
   |
   v
Raw JSON files (data/raw/)
   |
   v
transform.py  -->  build_database.py  -->  DuckDB
                                           |
New date range --> update_data.py ---------+
                   (insert new keys only)  |
                                           v
                                       SQL queries
                                           |
                                           v
                                    export_results.py
                                           |
                                           v
                                 data/processed/*.csv
                                           |
                                           v
                                   Streamlit dashboard
```

The project has four tables in DuckDB: `sites`, `pollutants`, `site_pollutants` and `measurements`. Each hourly measurement is identified by **station, pollutant and GMT timestamp**. These three fields form a composite primary key preventing two stored records from having the same identity.

The scripts have separate responsibilities:

| File | Purpose |
| --- | --- |
| `src/fetch_data.py` | Calls the API and saves raw JSON responses |
| `src/transform.py` | Cleans metadata and converts raw measurements to consistent records |
| `src/build_database.py` | Builds the initial database from the saved historical files |
| `src/update_data.py` | Fetches or reuses a chosen date range and inserts only new measurement keys |
| `sql/*.sql` | Calculates annual trends, monthly trends and the ULEZ comparison |
| `src/export_results.py` | Exports query results to CSV for the dashboard |
| `app.py` | Displays the results with Streamlit |

### How the updater works

`update_data(start, end, db_path)` checks for a saved JSON response for each of the 11 stations. If a file is missing it requests that date range from the API, if the file exists it reuses that to avoid unnecessary requests.

The incoming measurements are transformed and loaded into a temporary DuckDB table. An `INSERT OR IGNORE` operation then adds only measurement keys that are not already in the destination database. The script reports record counts before and after loading, the number added and the latest timestamp stored.

I tested this against a **separate copy of the database** to protect the original historical analysis:

| Test | Result |
| --- | --- |
| Load 1 October–1 November 2026, inclusive | 8,448 new hourly records |
| Repeat the same request | 0 new records |
| Request an overlapping period, 15 October–1 November | 0 new records |

The initial build and the updater serve different purposes. `build_database.py` creates the database from scratch as it is not intended to run after each update. The updater preserves existing rows. It does not replace previously stored readings if the API later corrects a value. Those are limitations I would address in a more mature pipeline.

### Understanding the ULEZ comparison

The SQL compares **September 2022 – August 2023** with **September 2023 – August 2024**, around the London ULEZ expansion in August 2023. To make the periods more comparable I paired the same calendar months one year apart, required at least 75% of returned hourly readings per month and kept stations with at least nine matching month pairs. The summary averages are weighted by the number of recorded readings.

Eight stations met these rules. All eight showed lower average NO₂ in the later period, with observed changes ranging from approximately **−4.4% to −20.6%**. Weather, traffic patterns, wider trends and differences between monitoring locations could all contribute so these figures should not be interpreted as an estimate of ULEZ's causal effect.

## How to run it

Run these commands from the **repository root**. The project was developed on macOS using Python 3.13.

### 1. Set up the project

**Requirements:** Git and Python 3.13 (developed and tested using Python 3.13.9).

Make sure Git and Python 3.13 are installed before starting.

**Clone the repository and set up the environment**

```bash
git clone https://github.com/KaiPilgrim/london-air-quality-pipeline.git
cd london-air-quality-pipeline
```
This downloads the project from GitHub and opens the project directory.

**Create and activate a virtual environment:**
```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

This creates an isolated Python 3.13 environment, keeping the project's dependencies separate from other installations.


**Upgrade pip and install the required packages:**

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This updates the Python package installer and installs the dependencies needed to build the database, process the air quality data and run the dashboard.


**Note:** These commands are for macOS and Linux. On Windows, use `py -3.13 -m venv .venv` to create the environment and `.venv\Scripts\Activate.ps1` to activate it in PowerShell.

### 2. Build the historical dataset and run the dashboard

```bash
python src/build_database.py
python src/export_results.py
python -m streamlit run app.py
```

The repository contains the original 2016–2025 JSON responses so the historical database can be recreated without downloading the data again. DuckDB is generated locally at `data/london_air_quality.duckdb`. The processed CSVs are also included in the repository so the dashboard can run using those outputs without a fresh rebuild.

`build_database.py` recreates the historical database tables from the saved JSON files. Use it for initial setup not for adding new readings.

`export_results.py` generates the processed CSV files from the database for the dashboard.

`app.py` launches the Streamlit dashboard allowing users to explore the processed air quality data.

**Note:** Close any other programs connected to the DuckDB database before building or exporting to avoid potential file locking conflicts.

### 3. Run the updater

To add new readings to the existing database without rebuilding it open the updater in interactive Python:

```bash
python -i src/update_data.py
```

Run the function with your chosen date range:

```bash
update_data("2026-10-01", "2026-11-02")
```

The updater checks for existing JSON files, retrieves missing data from the API and inserts only new records into the main database. It then refreshes the dashboard CSVs.

The end date is exclusive meaning measurements from that date are not included. For example an end date of `2025-11-02` includes readings up to and including 1 November 2025. You can change the dates to retrieve a more recent period. Enter ``exit()`` to close Python.

### 4. Test Updater (optional)
You can test how the pipeline adds new readings without changing the original historical database.

First create a test copy in terminal:

```bash
cp data/london_air_quality.duckdb data/test_update.duckdb
```

Then open the update script in interactive Python:

```bash
python -i src/update_data.py
```

At the `>>>` prompt, run the function twice with the same dates:

```python
update_data("2026-10-01", "2026-11-02", "data/test_update.duckdb")
update_data("2026-10-01", "2026-11-02", "data/test_update.duckdb")
```

The first run should insert any missing records for that period, the second should report 0 new records. To exit Python enter `exit()`.

The test copy protects the main 2016–2025 database. When using a test database the script does not refresh the dashboard CSVs which remain based on the original historical database. Updating the main database instead uses the function's default `db_path` and also runs the CSV exporter which in turn changes the dashboard CSVs with the latest available data.

No API key is required. A live update does require internet access. Reusing the same date ranged files avoids repeat API requests but it also means updated values for a previously cached period are not automatically fetched.

## What I would do next

- **Automate daily updates:** Schedule the pipeline to collect new air quality readings every 24 hours with logging to track successful runs and errors.

- **Improve data validation:** Add more checks for missing values, duplicates, inconsistent measurements and unusual readings before storing the data.

- **Track data ingestion:** Add timestamps to record when measurements were inserted or updated, making it easier to monitor new data and investigate changes.

- **Expand the ULEZ analysis:** Create separate charts for each ULEZ expansion to better visualise how pollution levels changed before and after each stage.

- **Include more monitoring sites and pollutants:** Expand the dataset, improve how monitoring sites are grouped and allow multiple pollutants to be compared on the same dashboard.

- **Introduce a data selection interface:** Allow users to select monitoring sites, pollutant codes and date ranges rather than having these predefined in the code.

- **Investigate the impact of ULEZ:** Explore methods of estimating how much ULEZ contributed to changes in pollution levels accounting for other factors that may have influenced the results.

## Where AI helped

I used AI as a learning and development tool. It helped me understand the API and Python concepts, SQL querying and a helper to debug errors for parts of the pipeline, queries and dashboard.


## Sources

Air quality data: London Air Quality Network (LAQN). This is an independent exploratory project and not an official evaluation of ULEZ.

- [London Air Quality Network](https://www.londonair.org.uk/)
- [Environmental Research Group air-quality API](https://api.erg.ic.ac.uk/AirQuality/help)
- [API documentation](https://api.erg.ic.ac.uk/AirQuality/Information/Documentation/pdf)


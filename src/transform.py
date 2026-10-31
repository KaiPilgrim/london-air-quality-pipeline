import json, os
from datetime import datetime

# =========================
# Format functions
# =========================

# to_float() checks to see if value is equal to none or empty string. 
# if so return none. Function then returns the value as float type.
def to_float(value):
    if value is None or str(value).strip() == "":
        return None

    return float(value)

# to_date() checks if date is empty or none, if so then return none
# Otherwise convert to python date data type.
def to_date(value):
    if not value:
        return None

    return datetime.fromisoformat(value).date()

def to_datetime(value):
    if not value:
        return None

    return datetime.fromisoformat(value)

# =========================
# Site Transformation
# =========================

# opens the 'sites.json' and returns site data as a dict stored in site data
with open("data/raw/sites.json", "r") as f:
    site_data = json.load(f)

sites = site_data["Sites"]["Site"] # data is inside nested brackets


clean_sites = []

for site in sites:
    clean_sites.append({
        "site_code": site["@SiteCode"],
        "site_name": site["@SiteName"],
        "site_type": site["@SiteType"],
        "latitude": to_float(site.get("@Latitude")),
        "longitude": to_float(site.get("@Longitude")),
        "local_authority": site.get("@LocalAuthorityName"),
        "date_opened": to_date(site.get("@DateOpened")),
        "date_closed": to_date(site.get("@DateClosed")),
        "data_owner": site.get("@DataOwner"),
        "data_manager": site.get("@DataManager"),
        "site_url": site.get("@SiteLink")
    })


missing_coordinates = [
    site for site in clean_sites
    if site["latitude"] is None or site["longitude"] is None
]

print(f"Total sites: {len(clean_sites)}")
print(f"Sites with missing coordinates: {len(missing_coordinates)}")
print(missing_coordinates)


# =========================
# Pollutant Transformation
# =========================

with open("data/raw/pollutants.json", "r") as f:
    pollutant_data = json.load(f)

pollutants = pollutant_data["AirQualitySpecies"]["Species"]

print(f"Total pollutants: {len(pollutants)}")


clean_pollutants = []

for chemical in pollutants:
    clean_pollutants.append({
        "pollutant_code": chemical["@SpeciesCode"],
        "pollutant_name": chemical["@SpeciesName"],
        "description": chemical["@Description"],
        "health_effect": chemical["@HealthEffect"],
        "info_url": chemical["@Link"]
    })

print(f"Pollutants transformed: {len(clean_pollutants)}")

# =========================
# Site_Pollutant Transformation
# =========================

with open("data/raw/site_pollutants.json", "r") as f:
    site_pollutant_data = json.load(f)

site_pollutants = site_pollutant_data["Sites"]["Site"]

clean_site_pollutants = []
valid_site_pollutants = []
invalid_site_pollutants = []

for site in site_pollutants:
    species = site["Species"]
    if isinstance(species, dict):
        species = [species]
    for chemical in species:
        clean_site_pollutants.append({
            "site_code": site["@SiteCode"],
            "pollutant_code": chemical["@SpeciesCode"],
            "monitoring_started": to_date(chemical.get("@DateMeasurementStarted")),
            "monitoring_finished": to_date(chemical.get("@DateMeasurementFinished"))
            })

t_records = 0
u_records = 0
dupes = 0
invalid_dates = 0
seen = set()

for entry in clean_site_pollutants:
    t_records += 1
    entry_tuple = tuple(sorted(entry.items()))

    if entry_tuple in seen:
        print(f"Found duplicate: {entry}")
        dupes += 1
        continue
        
    seen.add(entry_tuple)
    u_records += 1

    started = entry["monitoring_started"]
    finished = entry["monitoring_finished"]

    if started and finished and started > finished:
        print(f"Invalid date range - Site: {entry['site_code']}, Pollutant: {entry['pollutant_code']}, Started: {started}, Finished: {finished}")
        invalid_dates += 1
        invalid_site_pollutants.append(entry)
    else:
        valid_site_pollutants.append(entry)

print(f"\n\nTotal records: {t_records}")
print(f"Unique records: {u_records} (Valid: {len(valid_site_pollutants)}, Invalid: {len(invalid_site_pollutants)})")
print(f"Exact duplicates excluded: {dupes}\n")


# =========================
# Full measurements
# =========================

def get_year(file):
    with open(f"data/raw/{file}", "r") as f:
        year = json.load(f)

    data = year["RawAQData"]
    clean_measurements = []

    for hour in data["Data"]:
        clean_measurements.append({
            "site_code": data["@SiteCode"],
            "pollutant_code": data["@SpeciesCode"],
            "measured_at_gmt": to_datetime(hour.get("@MeasurementDateGMT")),
            "value": to_float(hour.get("@Value")),
            "source_file": file
            })
    return clean_measurements

folder_path = "data/raw"

no2_files = sorted([
    f
    for f in os.listdir(folder_path)
    if f.startswith("no2_") and f.endswith(".json")
])


full_measurements = []
total_missing = 0

for entry in no2_files:
    full_measurements.extend(get_year(entry))

for row in full_measurements:
    if row["value"] is None:
        total_missing += 1

unique_stations = {row["site_code"] for row in full_measurements}

print(f"NO2 files found: {len(no2_files)}")
print(f"Total hourly records: {len(full_measurements)}\nMissing Measurements: {total_missing}\nUnique stations: {len(unique_stations)}")


measure_dupes = set()
duplicate_keys_count = 0
for row in full_measurements:
    measurement_key = (row["site_code"], row["pollutant_code"], row["measured_at_gmt"])
    if measurement_key in measure_dupes:
            duplicate_keys_count += 1
    else:
        measure_dupes.add(measurement_key)

print(f"Duplicate measurement keys: {duplicate_keys_count}")


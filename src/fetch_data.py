import requests
from datetime import date

url = "https://api.erg.ic.ac.uk/AirQuality" #Base URL
endpoint = {
    "sites": "/Information/MonitoringSites/GroupName=London/Json",
    "site_pollutants": "/Information/MonitoringSiteSpecies/GroupName=London/Json",
    "pollutants": "/Information/Species/Json"
}

site_codes = ["EN1", "EN4", "IS2", "WM0", "WM5", "CE2", "HG1", "HG4", "BL0", "EN7", "BT4"]
observed_years = ["2016","2017","2018","2019","2020","2021","2022","2023","2024","2025","2026"]
start_date = "2016-10-24"
end_date = "2026-10-24"

# extract function will add join the endpoint to the base url and save the api response
def extract(endpoint_name): 
    r = requests.get(url+endpoint[endpoint_name])
    r.raise_for_status()

    with open(f"data/raw/{endpoint_name}.json", "wb") as f:
        f.write(r.content)
    return

#extract_measurements function will get the air quality data for a given station during the requested
#date range and store that data locally.

def extract_measurements(site_code, start, end):
    path = (
        f"/Data/SiteSpecies/SiteCode={site_code}"
        f"/SpeciesCode=NO2/StartDate={start}/EndDate={end}/Json"
    )

    r = requests.get(url + path)
    r.raise_for_status()

    with open(f"data/raw/no2_{site_code}_{start}_{end}.json", "wb") as f:
        f.write(r.content)

    records = r.json()["RawAQData"]["Data"]
    expected_hours = (
        date.fromisoformat(end) - date.fromisoformat(start)
        ).days * 24
    valid = sum(row["@Value"] != "" for row in records)
    completeness = valid / expected_hours * 100
    print(f"{site_code} ({start}): {completeness:.2f}% complete")






#for i in endpoint:
#    extract(i)

#extract_measurements("WM5", "2018-01-01", "2019-01-01") #test

for year in range(2018, 2025):
    start = f"{year}-01-01"
    end = f"{year + 1}-01-01"
    for site in site_codes:
        extract_measurements(site, start, end)

#extract_measurements("WM0", "2019-01-01", "2020-01-01")


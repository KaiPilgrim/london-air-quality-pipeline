import requests

url = "https://api.erg.ic.ac.uk/AirQuality"
endpoint = {
    "sites": "/Information/MonitoringSites/GroupName=London/Json",
    "site_pollutants": "/Information/MonitoringSiteSpecies/GroupName=London/Json",
    "pollutants": "/Information/Species/Json"
}

site_codes = ["EN1", "EN4", "IS2", "WM0"]

start_date = "2016-10-24"
end_date = "2026-10-24"

def extract(endpoint_name):
    r = requests.get(url+endpoint[endpoint_name])
    r.raise_for_status()

    with open(f"data/raw/{endpoint_name}.json", "wb") as f:
        f.write(r.content)
    return


for i in endpoint:
    extract(i)


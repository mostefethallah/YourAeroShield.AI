import os
import requests

API_KEY = os.environ.get("AIRNOW_API_KEY")
ZIP_CODE = "10001"  # Manhattan, NY, just for testing

url = "https://www.airnowapi.org/aq/observation/zipCode/current/"
params = {
    "format": "application/json",
    "zipCode": ZIP_CODE,
    "distance": 25,
    "API_KEY": API_KEY,
}

response = requests.get(url, params=params, timeout=10)
print("Status code:", response.status_code)

data = response.json()
for entry in data:
    print(entry["ParameterName"], "-", entry["AQI"], "AQI, category:", entry["Category"]["Name"])

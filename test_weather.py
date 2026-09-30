import requests

HEADERS = {"User-Agent": "YourAeroShield.AI-prototype (youraeroshield@gmail.com)"}
LAT, LON = 40.7128, -74.0060

# 1. Ask NOAA about our location
url = f"https://api.weather.gov/points/{LAT},{LON}"
points = requests.get(url, headers=HEADERS, timeout=10).json()
stations_url = points["properties"]["observationStations"]

# 2. Get nearby stations and pick the first (closest)
stations = requests.get(stations_url, headers=HEADERS, timeout=10).json()
station_id = stations["features"][0]["properties"]["stationIdentifier"]
print("Station:", station_id)

# 3. Get that station's latest reading
url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
obs = requests.get(url, headers=HEADERS, timeout=10).json()
p = obs["properties"]

print("Time:", p["timestamp"])
print("Temperature (C):", p["temperature"]["value"])
print("Humidity (%):", p["relativeHumidity"]["value"])
print("Wind speed (km/h):", p["windSpeed"]["value"])

import os
import requests
import psycopg2
from datetime import datetime, timezone

HEADERS = {"User-Agent": "AirGuard.AI-prototype (youraeroshield@gmail.com)"}
LAT, LON = 40.7128, -74.0060
ZIP_CODE = "10001"
API_KEY = os.environ.get("AIRNOW_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")


def collect_one_reading():
    points = requests.get(f"https://api.weather.gov/points/{LAT},{LON}", headers=HEADERS, timeout=10).json()
    stations_url = points["properties"]["observationStations"]
    stations = requests.get(stations_url, headers=HEADERS, timeout=10).json()
    station_id = stations["features"][0]["properties"]["stationIdentifier"]

    obs = requests.get(
        f"https://api.weather.gov/stations/{station_id}/observations/latest",
        headers=HEADERS, timeout=10
    ).json()["properties"]

    airnow_resp = requests.get(
        "https://www.airnowapi.org/aq/observation/zipCode/current/",
        params={"format": "application/json", "zipCode": ZIP_CODE, "distance": 25, "API_KEY": API_KEY},
        timeout=10,
    ).json()

    pm25_aqi = None
    ozone_aqi = None
    for entry in airnow_resp:
        if entry["ParameterName"] == "PM2.5":
            pm25_aqi = entry["AQI"]
        elif entry["ParameterName"] == "O3":
            ozone_aqi = entry["AQI"]

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "station_id": station_id,
        "temperature_c": obs["temperature"]["value"],
        "humidity_pct": obs["relativeHumidity"]["value"],
        "wind_kmh": obs["windSpeed"]["value"],
        "pm25_aqi": pm25_aqi,
        "ozone_aqi": ozone_aqi,
    }


def save_reading(row):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO readings (timestamp_utc, station_id, temperature_c, humidity_pct, wind_kmh, pm25_aqi, ozone_aqi)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        row["timestamp_utc"], row["station_id"], row["temperature_c"],
        row["humidity_pct"], row["wind_kmh"], row["pm25_aqi"], row["ozone_aqi"],
    ))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    try:
        row = collect_one_reading()
        save_reading(row)
        print("Saved:", row["timestamp_utc"], row["pm25_aqi"], row["temperature_c"])
    except Exception as e:
        print("Error:", e)

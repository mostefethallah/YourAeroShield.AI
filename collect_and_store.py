import os
import requests
import psycopg2
from datetime import datetime, timezone

HEADERS = {"User-Agent": "YourAeroShield-prototype (yoUR.com)"}
LAT, LON = 40.7128, -74.0060
ZIP_CODES = ["10001", "07302", "06902"]  # New York first, then Jersey City, Stamford
API_KEY = os.environ.get("AIRNOW_API_KEY")
DATABASE_URL = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")


def fetch_airnow(zip_code):
    try:
        r = requests.get(
            "https://www.airnowapi.org/aq/observation/current/ziplatlong/",
            params={"format": "application/json", "zipCode": zip_code, "API_KEY": API_KEY},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"AirNow unavailable for {zip_code}:", e)
        return []
    if not isinstance(data, list):
        print(f"AirNow returned no data for {zip_code}:", data)
        return []
    return data


def get_air_quality():
    result = {"pm25_aqi": None, "pm25_site": None, "ozone_aqi": None, "ozone_site": None}
    for zip_code in ZIP_CODES:
        for entry in fetch_airnow(zip_code):
            name = entry.get("parameterName")
            aqi = entry.get("nowcastAQI")
            site = f'{entry.get("siteName")} ({zip_code})'
            if aqi is None:
                continue
            if name == "PM2.5" and result["pm25_aqi"] is None:
                result["pm25_aqi"], result["pm25_site"] = aqi, site
            elif name in ("O3", "OZONE") and result["ozone_aqi"] is None:
                result["ozone_aqi"], result["ozone_site"] = aqi, site
        if result["pm25_aqi"] is not None and result["ozone_aqi"] is not None:
            break
    return result


def collect_one_reading():
    points = requests.get(f"https://api.weather.gov/points/{LAT},{LON}", headers=HEADERS, timeout=10).json()
    stations = requests.get(points["properties"]["observationStations"], headers=HEADERS, timeout=10).json()
    station_id = stations["features"][0]["properties"]["stationIdentifier"]
    obs = requests.get(
        f"https://api.weather.gov/stations/{station_id}/observations/latest",
        headers=HEADERS, timeout=10,
    ).json()["properties"]

    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "station_id": station_id,
        "temperature_c": obs["temperature"]["value"],
        "humidity_pct": obs["relativeHumidity"]["value"],
        "wind_kmh": obs["windSpeed"]["value"],
    }
    row.update(get_air_quality())
    return row


def save_reading(row):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO readings (timestamp_utc, station_id, temperature_c, humidity_pct, wind_kmh,
                              pm25_aqi, ozone_aqi, pm25_site, ozone_site)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row["timestamp_utc"], row["station_id"], row["temperature_c"], row["humidity_pct"],
        row["wind_kmh"], row["pm25_aqi"], row["ozone_aqi"], row["pm25_site"], row["ozone_site"],
    ))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    try:
        row = collect_one_reading()
        save_reading(row)
        print("Saved:", row["timestamp_utc"], row["pm25_aqi"], row["temperature_c"], row["ozone_aqi"],
              "| PM2.5 from", row["pm25_site"], "| ozone from", row["ozone_site"])
    except Exception as e:
        print("Error:", e)

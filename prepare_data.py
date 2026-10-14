import os
import pandas as pd
import psycopg2

DB_URL = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")

# EPA PM2.5 breakpoints: (AQI low, AQI high, µg/m³ low, µg/m³ high)
PM25_BREAKPOINTS = [
    (0, 50, 0.0, 9.0), (51, 100, 9.1, 35.4), (101, 150, 35.5, 55.4),
    (151, 200, 55.5, 125.4), (201, 300, 125.5, 225.4), (301, 500, 225.5, 325.4),
]

def aqi_to_pm25(aqi):
    if aqi is None or pd.isna(aqi):
        return None
    for i_lo, i_hi, c_lo, c_hi in PM25_BREAKPOINTS:
        if i_lo <= aqi <= i_hi:
            return round((aqi - i_lo) / (i_hi - i_lo) * (c_hi - c_lo) + c_lo, 1)
    return None

# 1. Load everything from Neon
conn = psycopg2.connect(DB_URL)
df = pd.read_sql(
    "SELECT timestamp_utc, temperature_c, humidity_pct, wind_kmh, pm25_aqi, ozone_aqi, pm25_site "
    "FROM readings ORDER BY timestamp_utc", conn)
conn.close()

# 2. Clean types and convert AQI -> µg/m³
for col in ["temperature_c", "humidity_pct", "wind_kmh", "pm25_aqi", "ozone_aqi"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df["t"] = pd.to_datetime(df["timestamp_utc"], utc=True)
df["pm25_ugm3"] = df["pm25_aqi"].apply(aqi_to_pm25).astype(float)
df["pm25_fallback"] = df["pm25_site"].notna() & ~df["pm25_site"].fillna("").str.endswith("(10001)")

# 3. One row per hour (AirNow updates hourly)
hourly = df.set_index("t").resample("1h").agg({
    "temperature_c": "mean", "humidity_pct": "mean", "wind_kmh": "mean",
    "pm25_ugm3": "mean", "ozone_aqi": "mean", "pm25_fallback": "max",
})

# 4. Measure gaps
missing = hourly["pm25_ugm3"].isna()
runs = missing.groupby((~missing).cumsum()).sum()
longest_gap = int(runs.max()) if len(runs) else 0

# 5. Save
os.makedirs("data", exist_ok=True)
hourly.to_csv("data/outdoor_hourly.csv")

print("Raw readings:        ", len(df))
print("Period:              ", hourly.index.min(), "->", hourly.index.max())
print("Hours in period:     ", len(hourly))
print("Hours with PM2.5:    ", int((~missing).sum()), f"({(~missing).mean():.0%})")
print("Longest gap (hours): ", longest_gap)
print("Hours from fallback: ", int(hourly["pm25_fallback"].fillna(False).astype(bool).sum()))
print("PM2.5 µg/m³ min/mean/max:",
      round(hourly["pm25_ugm3"].min(), 1), "/",
      round(hourly["pm25_ugm3"].mean(), 1), "/",
      round(hourly["pm25_ugm3"].max(), 1))
print("Saved: data/outdoor_hourly.csv")

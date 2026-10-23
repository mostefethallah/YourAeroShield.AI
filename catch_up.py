import os, psycopg2
from psycopg2.extras import execute_values

src = psycopg2.connect(os.environ["NEON_DATABASE_URL"])
dst = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
s, d = src.cursor(), dst.cursor()

TABLES = {
    "readings": ["timestamp_utc", "station_id", "temperature_c", "humidity_pct", "wind_kmh",
                 "pm25_aqi", "ozone_aqi", "pm25_site", "ozone_site"],
    "indoor_readings": ["timestamp_utc", "room_id", "pm25_ugm3", "temperature_c",
                        "humidity_pct", "co2_ppm", "is_simulated"],
}

for table, cols in TABLES.items():
    d.execute(f"SELECT timestamp_utc FROM {table}")
    have = {r[0] for r in d.fetchall()}
    s.execute(f"SELECT {', '.join(cols)} FROM {table} WHERE timestamp_utc > now() - interval '2 days'")
    missing = [r for r in s.fetchall() if r[0] not in have]
    if missing:
        execute_values(d, f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s", missing)
        dst.commit()
    print(f"{table}: added {len(missing)} missing rows")

import os
import psycopg2
from psycopg2.extras import execute_values

src = psycopg2.connect(os.environ["NEON_DATABASE_URL"])      # read only
dst = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
s, d = src.cursor(), dst.cursor()

TABLES = {
    "readings": ["timestamp_utc", "station_id", "temperature_c", "humidity_pct", "wind_kmh",
                 "pm25_aqi", "ozone_aqi", "pm25_site", "ozone_site"],
    "indoor_readings": ["timestamp_utc", "room_id", "pm25_ugm3", "temperature_c",
                        "humidity_pct", "co2_ppm", "is_simulated"],
}

d.execute("SELECT id FROM rooms")
known_rooms = {r[0] for r in d.fetchall()}

for table, cols in TABLES.items():
    d.execute(f"SELECT COUNT(*) FROM {table}")
    if d.fetchone()[0] > 0:
        print(f"{table}: Supabase already has data, skipped (prevents duplicates)")
        continue
    s.execute(f"SELECT {', '.join(cols)} FROM {table} ORDER BY timestamp_utc")
    rows = s.fetchall()
    skipped = 0
    if table == "indoor_readings":
        kept = [r for r in rows if r[1] in known_rooms]
        skipped = len(rows) - len(kept)
        rows = kept
    execute_values(d, f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s", rows, page_size=500)
    dst.commit()
    msg = f"{table}: copied {len(rows)} rows"
    if skipped:
        msg += f" (skipped {skipped} with an unknown room)"
    print(msg)

for table in TABLES:
    s.execute(f"SELECT COUNT(*) FROM {table}")
    n_src = s.fetchone()[0]
    d.execute(f"SELECT COUNT(*) FROM {table}")
    n_dst = d.fetchone()[0]
    print(f"Check {table}: Neon {n_src} | Supabase {n_dst}")

src.close()
dst.close()

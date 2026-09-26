import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        id SERIAL PRIMARY KEY,
        timestamp_utc TIMESTAMPTZ NOT NULL,
        station_id TEXT,
        temperature_c REAL,
        humidity_pct REAL,
        wind_kmh REAL,
        pm25_aqi INTEGER,
        ozone_aqi INTEGER
    );
""")

conn.commit()
cur.close()
conn.close()

print("Table 'readings' is ready.")

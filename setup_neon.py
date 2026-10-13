import os
import psycopg2

url = os.environ.get("NEON_DATABASE_URL")

if not url:
    print("NEON_DATABASE_URL not found")
else:
    conn = psycopg2.connect(url)
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
    cur.execute("SELECT COUNT(*) FROM readings;")
    print("Table ready on Neon. Rows:", cur.fetchone()[0])

    cur.close()
    conn.close()

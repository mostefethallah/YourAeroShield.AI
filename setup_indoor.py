import os
import psycopg2

conn = psycopg2.connect(os.environ["NEON_DATABASE_URL"])
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS indoor_readings (
        id SERIAL PRIMARY KEY,
        timestamp_utc TIMESTAMPTZ NOT NULL,
        room_id TEXT NOT NULL,
        pm25_ugm3 REAL,
        temperature_c REAL,
        humidity_pct REAL,
        co2_ppm REAL,
        is_simulated BOOLEAN NOT NULL DEFAULT TRUE
    );
""")

conn.commit()
cur.close()
conn.close()
print("Table 'indoor_readings' is ready on Neon.")

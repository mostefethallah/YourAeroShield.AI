import os
import psycopg2
from datetime import datetime, timezone, timedelta

conn = psycopg2.connect(os.environ["NEON_DATABASE_URL"])
cur = conn.cursor()

since = datetime.now(timezone.utc) - timedelta(hours=24)

cur.execute("SELECT COUNT(*) FROM readings WHERE timestamp_utc >= %s;", (since,))
print("Outdoor readings (last 24h):", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM indoor_readings WHERE timestamp_utc >= %s;", (since,))
print("Indoor readings (last 24h):", cur.fetchone()[0])

cur.execute("SELECT timestamp_utc, pm25_aqi, temperature_c FROM readings ORDER BY id DESC LIMIT 5;")
print("\nLast 5 outdoor readings:")
for row in cur.fetchall():
    print(" ", row)

cur.close()
conn.close()

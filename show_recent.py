import os
import psycopg2

conn = psycopg2.connect(os.environ["NEON_DATABASE_URL"])
cur = conn.cursor()

print("=== Last 5 outdoor readings ===")
cur.execute("SELECT timestamp_utc, station_id, temperature_c, humidity_pct, pm25_aqi, ozone_aqi FROM readings ORDER BY id DESC LIMIT 5;")
for row in cur.fetchall():
    print(row)

print("\n=== Last 5 indoor readings (simulated) ===")
cur.execute("SELECT timestamp_utc, room_id, pm25_ugm3, temperature_c, humidity_pct, co2_ppm FROM indoor_readings ORDER BY id DESC LIMIT 5;")
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()

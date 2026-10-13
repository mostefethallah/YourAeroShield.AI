import os, psycopg2

conn = psycopg2.connect(os.environ["NEON_DATABASE_URL"])

cur = conn.cursor()
cur.execute("""
    SELECT DATE(timestamp_utc) AS jour,
           COUNT(*) AS total,
           COUNT(*) FILTER (WHERE pm25_aqi IS NULL) AS pm25_vide,
           COUNT(*) FILTER (WHERE ozone_aqi IS NULL) AS ozone_vide
    FROM readings
    WHERE timestamp_utc > now() - interval '7 days'
    GROUP BY jour ORDER BY jour
""")
print("jour        total  pm25_vide  ozone_vide")
for r in cur.fetchall():
    print(r[0], f"{r[1]:>6} {r[2]:>10} {r[3]:>11}")
conn.close()

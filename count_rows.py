import os
import psycopg2

conn = psycopg2.connect(os.environ["NEON_DATABASE_URL"])
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM readings;")
print("outdoor:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM indoor_readings;")
print("indoor:", cur.fetchone()[0])

cur.close()
conn.close()

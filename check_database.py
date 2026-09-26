import os
import psycopg2

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

cur.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 5;")
rows = cur.fetchall()

for r in rows:
    print(r)

cur.close()
conn.close()

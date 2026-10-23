import os, psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

print("== Tables and row counts ==")
cur.execute("""select relname, n_live_tup from pg_stat_user_tables order by relname""")
for t, n in cur.fetchall():
    cur.execute(f'select count(*) from "{t}"')
    print(f"{t}: {cur.fetchone()[0]} rows")

TABLE = "readings"  # change to your main table name
print(f"\n== Last 10 gaps in {TABLE} ==")
cur.execute(f"""select created_at,
  created_at - lag(created_at) over (order by created_at)
  from {TABLE} order by created_at desc limit 10""")
for ts, gap in cur.fetchall():
    print(ts, "gap:", gap)

cur.execute(f"select now() - max(created_at) from {TABLE}")
print("\nTime since last row:", cur.fetchone()[0])

print("\n== Rows per day (expect ~288) ==")
cur.execute(f"""select date(created_at), count(*) from {TABLE}
  group by 1 order by 1 desc limit 7""")
for d, n in cur.fetchall():
    print(d, n)

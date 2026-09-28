import os
import math
import random
from datetime import datetime, timezone
import psycopg2

DATABASE_URL = os.environ["NEON_DATABASE_URL"]
ROOM_ID = "sim-room-1"


def get_latest_outdoor_pm25_aqi(cur):
    cur.execute("SELECT pm25_aqi FROM readings WHERE pm25_aqi IS NOT NULL ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    return row[0] if row else 20


def make_reading(outdoor_aqi):
    now = datetime.now(timezone.utc)
    hour = now.hour + now.minute / 60

    # CO2: baseline ~450 ppm, higher in the daytime (a smooth curve peaking mid-afternoon UTC)
    occupancy = max(0.0, math.sin((hour - 12) / 24 * 2 * math.pi + math.pi / 2))
    co2 = 450 + 500 * occupancy + random.gauss(0, 30)

    temperature = 22 + random.gauss(0, 0.5)
    humidity = 45 + random.gauss(0, 3)

    # PM2.5: small base level plus a fraction of the outdoor level
    pm25 = max(0.0, 3 + 0.15 * outdoor_aqi + random.gauss(0, 1))

    return {
        "timestamp_utc": now.isoformat(),
        "room_id": ROOM_ID,
        "pm25_ugm3": round(pm25, 2),
        "temperature_c": round(temperature, 2),
        "humidity_pct": round(humidity, 2),
        "co2_ppm": round(co2, 1),
    }


if __name__ == "__main__":
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    outdoor_aqi = get_latest_outdoor_pm25_aqi(cur)
    r = make_reading(outdoor_aqi)

    cur.execute("""
        INSERT INTO indoor_readings
            (timestamp_utc, room_id, pm25_ugm3, temperature_c, humidity_pct, co2_ppm, is_simulated)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
    """, (r["timestamp_utc"], r["room_id"], r["pm25_ugm3"],
          r["temperature_c"], r["humidity_pct"], r["co2_ppm"]))

    conn.commit()
    cur.close()
    conn.close()
    print("Saved simulated reading:", r)

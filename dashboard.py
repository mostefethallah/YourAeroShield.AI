import os
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="YourAeroShield", layout="wide")
DB_URL = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")

# EPA PM2.5 breakpoints: (AQI low, AQI high, µg/m³ low, µg/m³ high)
PM25_BREAKPOINTS = [
    (0, 50, 0.0, 9.0), (51, 100, 9.1, 35.4), (101, 150, 35.5, 55.4),
    (151, 200, 55.5, 125.4), (201, 300, 125.5, 225.4), (301, 500, 225.5, 325.4),
]

def aqi_to_pm25(aqi):
    if aqi is None or pd.isna(aqi):
        return None
    for i_lo, i_hi, c_lo, c_hi in PM25_BREAKPOINTS:
        if i_lo <= aqi <= i_hi:
            return round((aqi - i_lo) / (i_hi - i_lo) * (c_hi - c_lo) + c_lo, 1)
    return None

@st.cache_data(ttl=300)
def load(days):
    conn = psycopg2.connect(DB_URL)
    outdoor = pd.read_sql(
        "SELECT timestamp_utc, temperature_c, humidity_pct, pm25_aqi, ozone_aqi FROM readings "
        "WHERE timestamp_utc > now() - %s * interval '1 day' ORDER BY timestamp_utc",
        conn, params=(days,))
    indoor = pd.read_sql(
        "SELECT timestamp_utc, room_id, pm25_ugm3, temperature_c, humidity_pct, co2_ppm FROM indoor_readings "
        "WHERE timestamp_utc > now() - %s * interval '1 day' ORDER BY timestamp_utc",
        conn, params=(days,))
    conn.close()
    return outdoor, indoor

st.title("YourAeroShield")
st.caption("Outdoor: NOAA + EPA AirNow (New York, ZIP 10001) · Indoor: sim-room-1 (simulated data)")

days = st.sidebar.slider("Days of history", 1, 14, 3)
outdoor, indoor = load(days)
for col in ["temperature_c", "humidity_pct", "pm25_aqi", "ozone_aqi"]:
    outdoor[col] = pd.to_numeric(outdoor[col], errors="coerce")
for col in ["pm25_ugm3", "temperature_c", "humidity_pct", "co2_ppm"]:
    indoor[col] = pd.to_numeric(indoor[col], errors="coerce")

for df in (outdoor, indoor):
    df["t"] = pd.to_datetime(df["timestamp_utc"], utc=True).dt.floor("15min")
outdoor = outdoor.drop_duplicates("t", keep="last")
indoor = indoor.drop_duplicates(["t", "room_id"], keep="last")
outdoor["pm25_ugm3"] = pd.to_numeric(outdoor["pm25_aqi"].apply(aqi_to_pm25), errors="coerce")

# Latest readings
lo = outdoor.dropna(subset=["pm25_ugm3"]).tail(1)
li = indoor.tail(1)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Outdoor PM2.5 (µg/m³)", f'{lo["pm25_ugm3"].iloc[0]:.1f}' if len(lo) else "—")
c2.metric("Indoor PM2.5 (µg/m³)", f'{li["pm25_ugm3"].iloc[0]:.1f}' if len(li) else "—")
c3.metric("Indoor CO₂ (ppm)", f'{li["co2_ppm"].iloc[0]:.0f}' if len(li) else "—")
c4.metric("Indoor humidity (%)", f'{li["humidity_pct"].iloc[0]:.0f}' if len(li) else "—")

# Charts
def compare(col_out, col_in):
    o = outdoor.set_index("t")[col_out].rename("Outdoor")
    i = indoor.groupby("t")[col_in].mean().rename("Indoor")
    return pd.concat([o, i], axis=1).sort_index()

st.subheader("PM2.5: outdoor vs indoor (µg/m³)")
st.line_chart(compare("pm25_ugm3", "pm25_ugm3"))
st.subheader("Temperature: outdoor vs indoor (°C)")
st.line_chart(compare("temperature_c", "temperature_c"))

# Mold risk
now = pd.Timestamp.now(tz="UTC")
st.subheader("Mold risk (last 48 h)")
recent = indoor[indoor["t"] > now - pd.Timedelta(hours=48)]
for room, g in recent.groupby("room_id"):
    h60 = (g["humidity_pct"] >= 60).sum() * 0.25
    h70 = (g["humidity_pct"] >= 70).sum() * 0.25
    level = "High" if h70 >= 24 else "Elevated" if h60 >= 12 else "Low"
    st.write(f"**{room}**: {level} ({h60:.1f} h above 60% humidity, {h70:.1f} h above 70%)")

# Pipeline health
st.subheader("Pipeline health (last 24 h)")
o24 = outdoor[outdoor["t"] > now - pd.Timedelta(hours=24)]
last = outdoor["t"].max()
h1, h2, h3 = st.columns(3)
h1.metric("Outdoor readings", f"{len(o24)} / 96")
h2.metric("Missing PM2.5", int(o24["pm25_aqi"].isna().sum()))
h3.metric("Minutes since last reading",
          f"{(now - last).total_seconds() / 60:.0f}" if pd.notna(last) else "—")

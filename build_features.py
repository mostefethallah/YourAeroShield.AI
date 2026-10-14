import numpy as np
import pandas as pd

h = pd.read_csv("data/outdoor_hourly.csv", index_col=0, parse_dates=True)
h.index = pd.to_datetime(h.index, utc=True)

def fill_short_gaps(s, max_len=2):
    isna = s.isna()
    gap_len = isna.groupby((~isna).cumsum()).transform("sum")
    filled = s.interpolate(method="time", limit_area="inside")
    return s.where(~(isna & (gap_len <= max_len)), filled)

raw_pm = h["pm25_ugm3"]                 # real measurements only (used for targets)
pm = fill_short_gaps(raw_pm)            # short gaps filled (used for inputs)

# Weather: keep only columns with enough coverage
weather = []
for col in ["temperature_c", "humidity_pct", "wind_kmh", "ozone_aqi"]:
    s = fill_short_gaps(h[col])
    coverage = s.notna().mean()
    if coverage >= 0.8 * pm.notna().mean():
        h[col] = s
        weather.append(col)
    else:
        print(f"Skipped {col}: only {coverage:.0%} coverage")

f = pd.DataFrame(index=h.index)
# What we know now about PM2.5
f["pm25_now"] = pm
for lag in [1, 2, 3, 6]:
    f[f"pm25_lag{lag}"] = pm.shift(lag)
f["pm25_change_1h"] = pm - pm.shift(1)
f["pm25_mean_3h"] = pm.rolling(3).mean()
# Weather now
for col in weather:
    f[col] = h[col]
# Time of day (New York local time), as a circle so 23h is close to 0h
local = h.index.tz_convert("America/New_York")
f["hour_sin"] = np.sin(2 * np.pi * local.hour / 24)
f["hour_cos"] = np.cos(2 * np.pi * local.hour / 24)
f["weekend"] = (local.dayofweek >= 5).astype(int)
# Targets: REAL future values
f["target_1h"] = raw_pm.shift(-1)
f["target_3h"] = raw_pm.shift(-3)

features = [c for c in f.columns if not c.startswith("target")]
f.to_csv("data/features.csv")

print("Features used:", ", ".join(features))
print("Hours in table:            ", len(f))
print("Usable examples for +1h:   ", len(f[features + ["target_1h"]].dropna()))
print("Usable examples for +3h:   ", len(f[features + ["target_3h"]].dropna()))
print("Saved: data/features.csv")

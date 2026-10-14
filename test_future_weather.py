import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

f = pd.read_csv("data/features.csv", index_col=0, parse_dates=True)
base = [c for c in f.columns if not c.startswith("target")]
weather = [c for c in ["temperature_c", "humidity_pct", "wind_kmh"] if c in f.columns]

for h in [1, 3]:
    target = f"target_{h}h"
    future = []
    for c in weather:
        f[f"{c}_in{h}h"] = f[c].shift(-h)      # actual weather h hours later ("perfect forecast")
        future.append(f"{c}_in{h}h")

    d = f[base + future + [target]].dropna()   # same rows for every model = fair comparison
    split = int(len(d) * 0.7)
    tr, te = d.iloc[:split], d.iloc[split:]
    pers = mean_absolute_error(te[target], te["pm25_now"])

    print(f"\n=== Forecast +{h}h | train {len(tr)} h, test {len(te)} h ===")
    print(f"  {'Persistence':<32} error {pers:.2f} µg/m³")
    for name, cols in [("Model, current weather only", base),
                       ("Model + perfect future weather", base + future)]:
        rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0)
        rf.fit(tr[cols], tr[target])
        mae = mean_absolute_error(te[target], rf.predict(te[cols]))
        print(f"  {name:<32} error {mae:.2f} µg/m³   vs persistence: {(pers - mae) / pers * 100:+.0f}%")

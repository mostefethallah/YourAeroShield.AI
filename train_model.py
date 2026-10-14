import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

f = pd.read_csv("data/features.csv", index_col=0, parse_dates=True)
features = [c for c in f.columns if not c.startswith("target")]

for target in ["target_1h", "target_3h"]:
    d = f[features + [target]].dropna()
    split = int(len(d) * 0.7)                      # chronological split, no shuffling
    train, test = d.iloc[:split], d.iloc[split:]
    X_tr, y_tr = train[features], train[target]
    X_te, y_te = test[features], test[target]

    results = {"Persistence (no change)": X_te["pm25_now"]}
    ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(X_tr, y_tr)
    results["Linear regression"] = ridge.predict(X_te)
    rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0).fit(X_tr, y_tr)
    results["Random forest"] = rf.predict(X_te)

    base = mean_absolute_error(y_te, results["Persistence (no change)"])
    print(f"\n=== Forecast {target.replace('target_', '+')} ===")
    print(f"Train: {len(train)} h | Test: {len(test)} h ({test.index.min():%b %d} -> {test.index.max():%b %d})")
    print(f"Typical PM2.5 in test: {y_te.mean():.1f} µg/m³")
    for name, pred in results.items():
        mae = mean_absolute_error(y_te, pred)
        gain = (base - mae) / base * 100
        print(f"  {name:<25} error {mae:.2f} µg/m³   vs persistence: {gain:+.0f}%")

    top = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False).head(4)
    print("  Most useful features:", ", ".join(f"{k} ({v:.0%})" for k, v in top.items()))

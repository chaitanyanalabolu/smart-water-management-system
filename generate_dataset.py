"""
generate_dataset.py
--------------------
Generates a realistic, synthetic hourly water-usage dataset for a
village-level smart water monitoring pilot: 20 households across
4 wards, 21 days of hourly flow readings, with genuine daily usage
patterns (morning/evening peaks), a handful of injected leaks
(continuous overnight flow), a couple of sudden-spike bursts, and
per-household daily limits for threshold-alert testing.

Output: /home/claude/water_project/data/household_water_usage.csv
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)

N_DAYS = 21
START = datetime(2026, 6, 1)
WARDS = {
    "Ward 1": [f"H{str(i).zfill(3)}" for i in range(1, 6)],
    "Ward 2": [f"H{str(i).zfill(3)}" for i in range(6, 11)],
    "Ward 3": [f"H{str(i).zfill(3)}" for i in range(11, 16)],
    "Ward 4": [f"H{str(i).zfill(3)}" for i in range(16, 21)],
}
HOUSEHOLD_WARD = {h: w for w, hs in WARDS.items() for h in hs}
HOUSEHOLDS = list(HOUSEHOLD_WARD.keys())

# Each household has its own baseline "family size" factor and daily limit
rng_sizes = rng.integers(2, 7, size=len(HOUSEHOLDS))  # family members
BASE_DAILY_LITRES = {h: int(sz * 55 + rng.normal(0, 15)) for h, sz in zip(HOUSEHOLDS, rng_sizes)}
DAILY_LIMIT = {h: int(BASE_DAILY_LITRES[h] * 1.35) for h in HOUSEHOLDS}  # limit ~35% above typical baseline

# Typical hourly usage shape (fraction of daily total per hour, 24 values, sums to 1)
HOURLY_SHAPE = np.array([
    0.010, 0.006, 0.004, 0.004, 0.008, 0.035,   # 00-05 (very low, pre-dawn)
    0.085, 0.110, 0.095, 0.060, 0.045, 0.035,   # 06-11 (morning peak)
    0.040, 0.035, 0.030, 0.030, 0.035, 0.045,   # 12-17 (midday)
    0.075, 0.095, 0.070, 0.035, 0.020, 0.015,   # 18-23 (evening peak)
])
HOURLY_SHAPE = HOURLY_SHAPE / HOURLY_SHAPE.sum()

# Households / days chosen to have injected anomalies for realistic testing
LEAK_EVENTS = [  # (household, start_day_index, duration_days) - continuous overnight flow
    ("H003", 8, 3),
    ("H012", 14, 4),
    ("H018", 5, 2),
]
SPIKE_EVENTS = [  # (household, day_index, hour) - sudden one-off burst (e.g. burst pipe / tap left open)
    ("H007", 10, 13),
    ("H015", 17, 9),
]

rows = []
for day_idx in range(N_DAYS):
    date = START + timedelta(days=day_idx)
    for h in HOUSEHOLDS:
        base = max(BASE_DAILY_LITRES[h], 60)
        # weekday/weekend slightly higher usage on weekends
        weekend_mult = 1.12 if date.weekday() >= 5 else 1.0
        day_total = base * weekend_mult * rng.normal(1.0, 0.08)
        hourly = HOURLY_SHAPE * day_total
        hourly = hourly * rng.normal(1.0, 0.10, size=24)  # per-hour noise
        hourly = np.clip(hourly, 0, None)

        is_leak_day = any(h == lh and (lday <= day_idx < lday + ldur) for lh, lday, ldur in LEAK_EVENTS)
        if is_leak_day:
            # continuous low-level overnight flow (01:00-05:00) that shouldn't be there
            leak_rate = rng.uniform(4.0, 8.0)  # litres/hour leaking
            for hr in range(1, 6):
                hourly[hr] += leak_rate

        for lh, lday, hr in SPIKE_EVENTS:
            if h == lh and day_idx == lday:
                hourly[hr] += rng.uniform(60, 110)  # burst event

        for hour in range(24):
            ts = date + timedelta(hours=hour)
            rows.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "date": date.strftime("%Y-%m-%d"),
                "hour": hour,
                "household_id": h,
                "ward": HOUSEHOLD_WARD[h],
                "flow_litres": round(float(hourly[hour]), 2),
            })

df = pd.DataFrame(rows)

# Daily cumulative usage per household (litres so far that day, updated hourly)
df = df.sort_values(["household_id", "timestamp"]).reset_index(drop=True)
df["cumulative_daily_litres"] = df.groupby(["household_id", "date"])["flow_litres"].cumsum().round(2)

# Attach each household's configured daily limit
df["daily_limit_litres"] = df["household_id"].map(DAILY_LIMIT)

# Ground-truth labels (only known because we injected them - useful to score the detector)
def is_labelled_anomaly(row):
    for lh, lday, ldur in LEAK_EVENTS:
        day_idx = (datetime.strptime(row["date"], "%Y-%m-%d") - START).days
        if row["household_id"] == lh and lday <= day_idx < lday + ldur and 1 <= row["hour"] <= 5:
            return 1
    for lh, lday, hr in SPIKE_EVENTS:
        day_idx = (datetime.strptime(row["date"], "%Y-%m-%d") - START).days
        if row["household_id"] == lh and day_idx == lday and row["hour"] == hr:
            return 1
    return 0

df["ground_truth_anomaly"] = df.apply(is_labelled_anomaly, axis=1)

out_path = "/home/claude/water_project/data/household_water_usage.csv"
df.to_csv(out_path, index=False)
print(f"Wrote {len(df)} rows to {out_path}")
print(df.head(10).to_string(index=False))
print("\nAnomaly rows injected:", df["ground_truth_anomaly"].sum())

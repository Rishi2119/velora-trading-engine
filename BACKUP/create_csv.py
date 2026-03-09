import pandas as pd
from datetime import datetime, timedelta
import os

rows = []
start = datetime(2026, 2, 1, 9, 15)
price = 1.1000

for i in range(100):
    open_p = price
    high = open_p + 0.0015
    low = open_p - 0.0010
    close = open_p + 0.0008

    rows.append({
        "time": start + timedelta(minutes=15 * i),
        "open": round(open_p, 5),
        "high": round(high, 5),
        "low": round(low, 5),
        "close": round(close, 5),
        "volume": 1000 + i * 10
    })

    price = close

os.makedirs("data", exist_ok=True)

df = pd.DataFrame(rows)
df.to_csv("data/EURUSD_M15.csv", index=False)

print("CSV CREATED SUCCESSFULLY")

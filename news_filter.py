import pandas as pd
from datetime import timedelta

NEWS_BLOCK_MINUTES = 30  # block before & after event

def load_news(path="news_calendar.csv"):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    return df


def is_news_blocked(current_time, news_df):
    for _, row in news_df.iterrows():
        if row["impact"] != "HIGH":
            continue

        start = row["time"] - timedelta(minutes=NEWS_BLOCK_MINUTES)
        end = row["time"] + timedelta(minutes=NEWS_BLOCK_MINUTES)

        if start <= current_time <= end:
            return True, row["event"]

    return False, None

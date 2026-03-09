import pandas as pd

def optimize_journal(path="logs/trade_journal.csv"):
    df = pd.read_csv(path)

    print("\n📊 OPTIMIZATION REPORT")
    print("=" * 30)

    # Keep only trades
    trades = df[df["decision"].str.contains("TRADE")]

    if trades.empty:
        print("No trades yet. Run engine longer.")
        return

    # ---- BASIC STATS ----
    print("\n🔹 BASIC STATS")
    print("Total Trades:", len(trades))
    print("Long Trades:", len(trades[trades["decision"].str.contains("LONG")]))
    print("Short Trades:", len(trades[trades["decision"].str.contains("SHORT")]))
    print("Average RR:", round(trades["rr"].mean(), 2))

    # ---- RR DISTRIBUTION ----
    print("\n🔹 RR DISTRIBUTION")
    print(trades["rr"].value_counts().sort_index())

    # ---- SESSION ANALYSIS ----
    print("\n🔹 SESSION PERFORMANCE")
    print(trades["session"].value_counts())

    # ---- REGIME ANALYSIS ----
    print("\n🔹 REGIME BLOCK ANALYSIS")
    blocked = df[df["session"] == "REGIME"]
    print("Blocked by regime:", len(blocked))

    # ---- REASON ANALYSIS ----
    print("\n🔹 MOST COMMON BLOCK REASONS")
    print(df["reasons"].value_counts().head(5))

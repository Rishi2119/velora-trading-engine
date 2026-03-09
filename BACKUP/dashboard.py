import pandas as pd
import matplotlib.pyplot as plt

def show_dashboard(path="logs/trade_journal.csv"):
    df = pd.read_csv(path)

    trades = df[df["decision"].str.contains("TRADE")]
    if trades.empty:
        print("No trades to visualize yet.")
        return

    # ---- RR Distribution ----
    plt.figure()
    trades["rr"].dropna().plot(kind="hist", bins=20)
    plt.title("RR Distribution")
    plt.xlabel("RR")
    plt.ylabel("Frequency")
    plt.show()

    # ---- Long vs Short ----
    plt.figure()
    trades["decision"].value_counts().plot(kind="bar")
    plt.title("Long vs Short Trades")
    plt.ylabel("Count")
    plt.show()

    # ---- Block Reasons ----
    plt.figure()
    df["session"].value_counts().plot(kind="bar")
    plt.title("Decision Context (Session / News / Regime)")
    plt.ylabel("Count")
    plt.show()

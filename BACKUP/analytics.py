import pandas as pd

def analyze_journal(path="logs/trade_journal.csv"):
    df = pd.read_csv(path)

    total = len(df)
    trades = df[df["decision"] == "TRADE"]
    no_trades = df[df["decision"] == "NO TRADE"]

    win_rate = len(trades) / total * 100 if total else 0
    avg_rr = trades["rr"].mean()

    print("\n📊 ANALYTICS REPORT")
    print("Total candles:", total)
    print("Trades taken:", len(trades))
    print("Trades blocked:", len(no_trades))
    print("Trade frequency:", round(win_rate, 2), "%")
    print("Average RR:", round(avg_rr, 2))

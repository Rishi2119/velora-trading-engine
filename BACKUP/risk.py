class RiskManager:
    def __init__(self, max_daily_loss, max_daily_trades, max_concurrent):
        self.max_daily_loss = max_daily_loss
        self.max_daily_trades = max_daily_trades
        self.max_concurrent = max_concurrent

        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.current_positions = 0

    # -------------------------
    # GLOBAL PERMISSION CHECK
    # -------------------------
    def can_trade(self):
        if self.daily_pnl <= -self.max_daily_loss:
            return False, "Max daily loss reached"

        if self.daily_trades >= self.max_daily_trades:
            return False, "Max daily trades reached"

        if self.current_positions >= self.max_concurrent:
            return False, "Max concurrent trades reached"

        return True, "OK"

    # -------------------------
    # TRADE REGISTRATION
    # -------------------------
    def add_trade(self):
        self.daily_trades += 1
        self.current_positions += 1

    def close_trade(self, pnl):
        self.daily_pnl += pnl
        self.current_positions = max(0, self.current_positions - 1)

    # -------------------------
    # DAILY RESET
    # -------------------------
    def reset_daily(self):
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.current_positions = 0

    # -------------------------
    # VALIDATE RR
    # -------------------------
    def validate_trade(self, entry, sl, tp, direction, min_rr):
        risk = abs(entry - sl)
        reward = abs(tp - entry)

        if risk <= 0:
            return False, "Invalid stop loss"

        rr = reward / risk

        if rr < min_rr:
            return False, f"RR too low ({rr:.2f})"

        return True, "Valid"

    # -------------------------
    # POSITION SIZE (FOREX)
    # -------------------------
    def calculate_position_size(self, balance, risk_pct, entry, sl, symbol):
        risk_amount = balance * risk_pct
        stop_pips = abs(entry - sl) * 10000  # EURUSD standard

        if stop_pips == 0:
            return 0.0

        lot_size = risk_amount / (stop_pips * 10)  # $10 per pip per lot
        return round(lot_size, 2)

    # -------------------------
    # RR CALC
    # -------------------------
    def calculate_rr(self, entry, sl, tp):
        return round(abs(tp - entry) / abs(entry - sl), 2)

    # -------------------------
    # STATS
    # -------------------------
    def get_stats(self):
        return {
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "open_positions": self.current_positions
        }

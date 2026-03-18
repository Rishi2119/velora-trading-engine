# 🌍 Multi-Pair Trading System Setup Guide

## What You're Getting

A trading system that trades **5 currency pairs simultaneously**:
- 💶 EURUSD
- 🇨🇦 USDCAD
- 💷 GBPUSD
- 🇨🇭 USDCHF
- 🇳🇿 NZDUSD

**Account:** $500
**Strategy:** S/R Rejection on all pairs
**Risk:** $5 per trade (1% of $500)

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Download Data

Run the data downloader:

```bash
python download_multi_pair_data.py
```

This will download M15 data for all 5 pairs and save them in the `data/` folder.

Expected output:
```
📥 MT5 Data Downloader for Multiple Pairs
✅ Connected to MT5

Downloading EURUSD...
   ✅ Downloaded 24000 candles
   💾 Saved to: data/EURUSD_M15.csv

Downloading USDCAD...
   ✅ Downloaded 24000 candles
   💾 Saved to: data/USDCAD_M15.csv

... (etc for all pairs)

✅ Successfully downloaded: 5/5 pairs
```

### Step 2: Configure

File `multi_pair_config.py` is already set up with:
- ✅ $500 account balance
- ✅ All 5 pairs enabled
- ✅ 1% risk per trade ($5)
- ✅ S/R strategy enabled

**No changes needed!** (Unless you want to customize)

### Step 3: Run

```bash
python multi_pair_runner.py
```

Expected output:
```
🚀 MULTI-PAIR TRADING SYSTEM with S/R Strategy

⚙️ MULTI-PAIR TRADING SYSTEM CONFIGURATION
💰 Account:
   Balance: $500
   Risk per Trade: 1.0% ($5.0)

📊 Trading Pairs (5 enabled):
   ✅ EURUSD
   ✅ USDCAD
   ✅ GBPUSD
   ✅ USDCHF
   ✅ NZDUSD

🔄 Starting Multi-Pair Trading Loop
   Trading 5 pairs simultaneously
```

---

## 📊 How It Works

### Multi-Pair Logic

The system:
1. Loads data for all 5 pairs
2. Monitors ALL pairs simultaneously
3. Takes setups on ANY pair that meets criteria
4. Manages risk across ALL pairs combined

### Example Scenario

```
Iteration 1:
  EURUSD: No setup
  USDCAD: ✅ S/R SETUP - Takes trade
  GBPUSD: No setup
  USDCHF: No setup
  NZDUSD: No setup

Iteration 2:
  EURUSD: ✅ S/R SETUP - Takes trade
  USDCAD: Already has trade (max 1 per pair)
  GBPUSD: No setup
  USDCHF: No setup
  NZDUSD: ✅ S/R SETUP - Takes trade

Now have 3 trades open (max allowed)
System won't take more until one closes
```

### Risk Management

**Per Trade:**
- Risk: 1% = $5
- Max loss per trade: $5

**Limits:**
- Max daily loss: $50 (10% of account)
- Max total trades: 3 at once
- Max per pair: 1 trade at a time
- Max daily trades: 15

**Protection:**
- If lose $50 in a day → stops trading
- If 3 trades open → waits for one to close
- Kill switch available

---

## ⚙️ Configuration Options

### Change Risk Per Trade

Edit `multi_pair_config.py`:

```python
# More conservative (0.5%)
RISK_PER_TRADE = 0.005  # $2.50 per trade

# Default (1%)
RISK_PER_TRADE = 0.01   # $5 per trade

# Aggressive (2%) - Not recommended for $500
RISK_PER_TRADE = 0.02   # $10 per trade
```

### Enable/Disable Pairs

```python
TRADING_PAIRS = [
    {
        'symbol': 'EURUSD',
        'data_file': 'data/EURUSD_M15.csv',
        'enabled': True  # ← Change to False to disable
    },
    # ... etc
]
```

### Adjust Limits

```python
MAX_TOTAL_TRADES = 3        # Max 3 trades across all pairs
MAX_TRADES_PER_PAIR = 1     # Max 1 trade per pair
MAX_DAILY_LOSS = 50         # Stop after $50 loss
```

### Split Risk Across Pairs

```python
SPLIT_RISK_ACROSS_PAIRS = True
# If True: splits 1% across active trades
# Example: With 2 trades open, each risks 0.5%
# If False: each trade risks full 1%
```

---

## 📈 What You'll See

### When Running

```
================================================================================
Iteration 10
================================================================================

📊 Status: PnL $15.00 | Trades 5/15 | Open 2/3
   EURUSD: Candle 1000/24000 | Trades: 1/1
   USDCAD: Candle 1000/24000 | Trades: 0/1
   GBPUSD: Candle 1000/24000 | Trades: 1/1
   USDCHF: Candle 1000/24000 | Trades: 0/1
   NZDUSD: Candle 1000/24000 | Trades: 0/1
```

### When Setup Detected

```
================================================================================
💡 GBPUSD S/R SETUP at 2024-01-15 14:30:00
================================================================================
   Type: support_rejection
   Zone: 1.27345
   Direction: LONG

   💰 TRADE DETAILS:
   Entry: 1.27345
   Stop:  1.27295 (50.0 pips)
   Target: 1.27445
   RR: 2.0:1
   Size: 0.10 lots
   Risk: $5.00

   📝 PAPER TRADE
```

---

## 🎯 Strategy Per Pair

Each pair uses the same S/R strategy:

**BUY Setup:**
- H1: Uptrend (price > EMA200, EMA50 > EMA200)
- M15: Price at support zone
- M15: Bullish rejection candle
- M15: RSI > 40
- RR: >= 2:1

**SELL Setup:**
- H1: Downtrend
- M15: Price at resistance zone
- M15: Bearish rejection candle
- M15: RSI < 60
- RR: >= 2:1

---

## 📊 Monitoring

### Check Logs

```bash
# Trade journal (all pairs)
cat logs/trade_journal.csv

# Performance stats
cat logs/performance.json
```

### Check Performance

```python
from performance import PerformanceTracker

perf = PerformanceTracker()
perf.print_summary()
```

---

## 🔍 Troubleshooting

### "Data file not found"

Run the data downloader:
```bash
python download_multi_pair_data.py
```

### "Failed to download [PAIR]"

Some brokers use different symbol names:
- USDCAD might be "USDCADm" or "USDCAD.m"
- Check in MT5 Market Watch

Edit `download_multi_pair_data.py`:
```python
PAIRS = [
    "EURUSD",
    "USDCADm",  # ← Add suffix if needed
    # etc
]
```

### Too Many/Few Setups

Adjust in `multi_pair_config.py`:

```python
# For MORE setups:
SR_ZONE_TOLERANCE = 0.0003  # Wider zones (30 pips)
SR_MIN_RR = 1.5             # Lower RR requirement

# For FEWER (quality) setups:
SR_ZONE_TOLERANCE = 0.0001  # Tighter zones (10 pips)
SR_MIN_RR = 2.5             # Higher RR requirement
```

### "Max concurrent trades hit"

This is working correctly! System limits total trades to 3.

To change:
```python
MAX_CONCURRENT_TRADES = 5  # Allow up to 5 total
```

---

## 💡 Tips for $500 Account

### Risk Management

✅ **DO:**
- Keep risk at 1% ($5 per trade)
- Respect daily loss limit ($50 = 10%)
- Start with max 2-3 concurrent trades
- Test for 2+ weeks paper trading

❌ **DON'T:**
- Risk more than 2% per trade
- Disable daily loss limits
- Trade all 5 pairs at once (too much exposure)
- Go live without extensive testing

### Realistic Expectations

**Good Week:**
- 5-10 trades total (all pairs)
- 60% win rate
- $25-50 profit
- 5-10% account growth

**Bad Week:**
- Hit daily loss limit 1-2 days
- 40% win rate
- -$50 to -$100 loss
- -10% to -20% drawdown

**After 1 Month:**
- Should see consistent pattern
- Win rate should stabilize
- Risk management working
- Ready to decide on live trading

---

## 🎓 Advanced Features

### Add More Pairs

Edit `multi_pair_config.py`:

```python
TRADING_PAIRS = [
    # ... existing pairs ...
    {
        'symbol': 'AUDUSD',
        'data_file': 'data/AUDUSD_M15.csv',
        'enabled': True
    }
]
```

Then download data:
```bash
# Edit download_multi_pair_data.py, add "AUDUSD" to PAIRS list
python download_multi_pair_data.py
```

### Remove Pairs

Set `enabled: False`:

```python
{
    'symbol': 'NZDUSD',
    'data_file': 'data/NZDUSD_M15.csv',
    'enabled': False  # ← Won't trade this pair
}
```

---

## ✅ Testing Checklist

### Week 1: Setup
- [ ] All 5 data files downloaded
- [ ] System runs without errors
- [ ] Sees all 5 pairs
- [ ] Detects setups on various pairs
- [ ] Logs trades correctly

### Week 2: Validation
- [ ] Position sizing correct for each pair
- [ ] Risk limits working (per pair and total)
- [ ] No more than 3 trades at once
- [ ] Daily loss limit stops trading
- [ ] Kill switch works

### Week 3-4: Performance
- [ ] Win rate > 50%
- [ ] Setups distributed across pairs
- [ ] Risk management holding up
- [ ] Comfortable with system behavior

---

## 🚀 Ready to Go!

You have:
- ✅ Multi-pair system configured
- ✅ $500 account settings
- ✅ 5 currency pairs
- ✅ S/R strategy on all pairs
- ✅ Proper risk management
- ✅ Data downloader
- ✅ Complete documentation

**Next steps:**
1. Download data: `python download_multi_pair_data.py`
2. Run system: `python multi_pair_runner.py`
3. Test for 2+ weeks
4. Track performance
5. Only then consider live trading

Good luck! 🎉

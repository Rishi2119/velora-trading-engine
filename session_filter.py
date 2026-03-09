from datetime import time

LONDON_START = time(7, 0)
LONDON_END = time(16, 0)

NY_START = time(12, 0)
NY_END = time(21, 0)

def is_trading_session(dt):
    t = dt.time()

    in_london = LONDON_START <= t <= LONDON_END
    in_newyork = NY_START <= t <= NY_END

    return in_london or in_newyork


import random
from agent.utils.logger import logger

class SentimentAnalyzer:
    def __init__(self):
        # In a real scenario, this would initialize API clients (e.g., Finnhub, AlphaVantage)
        self.sources = ["news", "social_media", "market_reports"]

    def get_market_sentiment(self, symbol="EURUSD"):
        """
        Fetches or simulates market sentiment for a given symbol.
        Returns a dictionary with sentiment score (-1.0 to 1.0) and a brief summary.
        """
        logger.info(f"Analyzing market sentiment for {symbol}...")
        
        # Simulated sentiment logic for MVP
        # Randomly assign a bias for testing purposes
        score = round(random.uniform(-1.0, 1.0), 2)
        
        if score > 0.5:
            summary = "Highly bullish sentiment. Major news outlets reporting positive economic indicators."
            label = "BULLISH"
        elif score > 0.1:
            summary = "Slightly positive sentiment. Minor favorable reports."
            label = "SLIGHTLY_BULLISH"
        elif score < -0.5:
            summary = "Highly bearish sentiment. Negative economic news breaking."
            label = "BEARISH"
        elif score < -0.1:
            summary = "Slightly negative sentiment. Minor unfavorable reports."
            label = "SLIGHTLY_BEARISH"
        else:
            summary = "Neutral sentiment. No significant market-moving news."
            label = "NEUTRAL"
            
        sentiment_data = {
            "symbol": symbol,
            "score": score,
            "label": label,
            "summary": summary
        }
        
        logger.debug(f"Sentiment for {symbol}: {label} ({score})")
        return sentiment_data

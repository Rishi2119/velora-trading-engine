"""
AI Finance Agent Team for Trading System
Provides intelligent market analysis, sentiment analysis, and trade recommendations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


class MarketAnalysisAgent:
    """
    Analyzes market conditions and provides insights
    """
    
    def __init__(self):
        self.name = "Market Analysis Agent"
        self.role = "Technical & Fundamental Analysis"
    
    def analyze_market_structure(self, df):
        """Analyze market structure and trend"""
        if len(df) < 50:
            return {"trend": "UNKNOWN", "strength": 0, "confidence": 0}
        
        # Calculate EMAs
        ema20 = df['close'].ewm(span=20).mean().iloc[-1]
        ema50 = df['close'].ewm(span=50).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # Determine trend
        if ema20 > ema50 and current_price > ema20:
            trend = "BULLISH"
            strength = min(((ema20 - ema50) / ema50) * 1000, 100)
        elif ema20 < ema50 and current_price < ema20:
            trend = "BEARISH"
            strength = min(((ema50 - ema20) / ema50) * 1000, 100)
        else:
            trend = "NEUTRAL"
            strength = 50
        
        # Calculate volatility
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * 100
        
        # Price momentum
        price_change_20 = ((current_price - df['close'].iloc[-20]) / df['close'].iloc[-20]) * 100
        
        analysis = {
            "trend": trend,
            "strength": strength,
            "volatility": volatility,
            "momentum_20": price_change_20,
            "confidence": min(abs(strength), 100),
            "current_price": current_price,
            "ema20": ema20,
            "ema50": ema50
        }
        
        return analysis
    
    def identify_support_resistance(self, df, lookback=50):
        """Identify key support and resistance levels"""
        if len(df) < lookback:
            return {"support": [], "resistance": []}
        
        recent = df.tail(lookback)
        current_price = df['close'].iloc[-1]
        
        # Find swing highs and lows
        highs = recent['high'].values
        lows = recent['low'].values
        
        # Support levels (recent lows)
        support_candidates = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                if lows[i] < current_price:  # Only below current price
                    support_candidates.append(lows[i])
        
        # Resistance levels (recent highs)
        resistance_candidates = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                if highs[i] > current_price:  # Only above current price
                    resistance_candidates.append(highs[i])
        
        # Get closest levels
        support = sorted(support_candidates, reverse=True)[:3]
        resistance = sorted(resistance_candidates)[:3]
        
        return {
            "support": support,
            "resistance": resistance,
            "nearest_support": support[0] if support else None,
            "nearest_resistance": resistance[0] if resistance else None
        }
    
    def generate_report(self, df):
        """Generate comprehensive market analysis report"""
        structure = self.analyze_market_structure(df)
        levels = self.identify_support_resistance(df)
        
        report = f"""
🔍 Market Analysis Report
{'='*50}

📊 Market Structure:
   Trend: {structure['trend']}
   Strength: {structure['strength']:.1f}/100
   Volatility: {structure['volatility']:.2f}%
   Momentum (20): {structure['momentum_20']:.2f}%
   Confidence: {structure['confidence']:.1f}%

💹 Price Levels:
   Current: {structure['current_price']:.5f}
   EMA20: {structure['ema20']:.5f}
   EMA50: {structure['ema50']:.5f}

🎯 Key Levels:
   Nearest Support: {levels['nearest_support']:.5f if levels['nearest_support'] else 'N/A'}
   Nearest Resistance: {levels['nearest_resistance']:.5f if levels['nearest_resistance'] else 'N/A'}

{'='*50}
"""
        
        return report, structure, levels


class SentimentAnalysisAgent:
    """
    Analyzes market sentiment from price action
    """
    
    def __init__(self):
        self.name = "Sentiment Analysis Agent"
        self.role = "Market Sentiment & Psychology"
    
    def analyze_sentiment(self, df):
        """Analyze market sentiment from price action"""
        if len(df) < 20:
            return {"sentiment": "NEUTRAL", "score": 50}
        
        # Recent price action
        recent = df.tail(20)
        
        # Bullish/Bearish candles
        bullish_candles = (recent['close'] > recent['open']).sum()
        bearish_candles = (recent['close'] < recent['open']).sum()
        
        # Volume trend (if available)
        volume_increasing = False
        if 'volume' in df.columns:
            vol_recent = recent['volume'].tail(5).mean()
            vol_prev = recent['volume'].head(5).mean()
            volume_increasing = vol_recent > vol_prev * 1.2
        
        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Calculate sentiment score
        sentiment_score = 50  # Neutral baseline
        
        # Adjust based on candles
        sentiment_score += (bullish_candles - bearish_candles) * 2
        
        # Adjust based on RSI
        if current_rsi > 60:
            sentiment_score += 10
        elif current_rsi < 40:
            sentiment_score -= 10
        
        # Adjust based on volume
        if volume_increasing:
            sentiment_score += 5
        
        # Clamp between 0-100
        sentiment_score = max(0, min(100, sentiment_score))
        
        # Determine sentiment label
        if sentiment_score >= 65:
            sentiment = "BULLISH"
        elif sentiment_score <= 35:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        return {
            "sentiment": sentiment,
            "score": sentiment_score,
            "rsi": current_rsi,
            "bullish_candles": bullish_candles,
            "bearish_candles": bearish_candles,
            "volume_increasing": volume_increasing
        }
    
    def generate_report(self, df):
        """Generate sentiment analysis report"""
        analysis = self.analyze_sentiment(df)
        
        report = f"""
😊 Sentiment Analysis Report
{'='*50}

📊 Market Sentiment: {analysis['sentiment']}
   Score: {analysis['score']:.0f}/100

📈 Indicators:
   RSI: {analysis['rsi']:.1f}
   Bullish Candles (20): {analysis['bullish_candles']}
   Bearish Candles (20): {analysis['bearish_candles']}
   Volume Trend: {'Increasing 📈' if analysis['volume_increasing'] else 'Stable'}

{'='*50}
"""
        
        return report, analysis


class TradeRecommendationAgent:
    """
    Provides trade recommendations based on analysis
    """
    
    def __init__(self):
        self.name = "Trade Recommendation Agent"
        self.role = "Trade Signal Generation"
    
    def generate_recommendation(self, market_analysis, sentiment_analysis, sr_levels):
        """Generate trade recommendation"""
        
        trend = market_analysis['trend']
        trend_strength = market_analysis['strength']
        sentiment = sentiment_analysis['sentiment']
        sentiment_score = sentiment_analysis['score']
        current_price = market_analysis['current_price']
        
        # Decision matrix
        recommendations = []
        confidence = 0
        
        # Strong bullish scenario
        if trend == "BULLISH" and sentiment == "BULLISH" and trend_strength > 60:
            recommendations.append({
                "action": "BUY",
                "reason": "Strong bullish trend + positive sentiment",
                "confidence": 80,
                "entry": current_price,
                "stop": sr_levels.get('nearest_support', current_price * 0.998),
                "target": sr_levels.get('nearest_resistance', current_price * 1.015)
            })
        
        # Strong bearish scenario
        elif trend == "BEARISH" and sentiment == "BEARISH" and trend_strength > 60:
            recommendations.append({
                "action": "SELL",
                "reason": "Strong bearish trend + negative sentiment",
                "confidence": 80,
                "entry": current_price,
                "stop": sr_levels.get('nearest_resistance', current_price * 1.002),
                "target": sr_levels.get('nearest_support', current_price * 0.985)
            })
        
        # Moderate bullish
        elif trend == "BULLISH" and sentiment in ["BULLISH", "NEUTRAL"]:
            recommendations.append({
                "action": "BUY",
                "reason": "Bullish trend alignment",
                "confidence": 60,
                "entry": current_price,
                "stop": current_price * 0.998,
                "target": current_price * 1.01
            })
        
        # Moderate bearish
        elif trend == "BEARISH" and sentiment in ["BEARISH", "NEUTRAL"]:
            recommendations.append({
                "action": "SELL",
                "reason": "Bearish trend alignment",
                "confidence": 60,
                "entry": current_price,
                "stop": current_price * 1.002,
                "target": current_price * 0.99
            })
        
        # Conflicting signals - wait
        else:
            recommendations.append({
                "action": "WAIT",
                "reason": "Conflicting signals - trend and sentiment not aligned",
                "confidence": 40,
                "entry": None,
                "stop": None,
                "target": None
            })
        
        return recommendations
    
    def generate_report(self, recommendations):
        """Generate recommendation report"""
        
        report = "🎯 Trade Recommendations\n" + "="*50 + "\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            report += f"Recommendation #{i}:\n"
            report += f"   Action: {rec['action']}\n"
            report += f"   Reason: {rec['reason']}\n"
            report += f"   Confidence: {rec['confidence']}%\n"
            
            if rec['entry']:
                report += f"   Entry: {rec['entry']:.5f}\n"
                report += f"   Stop: {rec['stop']:.5f}\n"
                report += f"   Target: {rec['target']:.5f}\n"
                
                # Calculate RR
                if rec['action'] == 'BUY':
                    risk = abs(rec['entry'] - rec['stop'])
                    reward = abs(rec['target'] - rec['entry'])
                else:
                    risk = abs(rec['stop'] - rec['entry'])
                    reward = abs(rec['entry'] - rec['target'])
                
                if risk > 0:
                    rr = reward / risk
                    report += f"   Risk/Reward: {rr:.2f}:1\n"
            
            report += "\n"
        
        report += "="*50
        
        return report


class AIFinanceAgentTeam:
    """
    Coordinating team of AI agents for comprehensive market analysis
    """
    
    def __init__(self):
        self.market_agent = MarketAnalysisAgent()
        self.sentiment_agent = SentimentAnalysisAgent()
        self.recommendation_agent = TradeRecommendationAgent()
        
        print("🤖 AI Finance Agent Team Initialized")
        print(f"   - {self.market_agent.name}")
        print(f"   - {self.sentiment_agent.name}")
        print(f"   - {self.recommendation_agent.name}")
    
    def analyze(self, df, symbol="UNKNOWN"):
        """
        Comprehensive analysis by all agents
        
        Args:
            df: Price dataframe
            symbol: Trading symbol
        
        Returns:
            Complete analysis with reports and recommendations
        """
        print(f"\n🤖 AI Agents analyzing {symbol}...")
        
        # Market Analysis
        market_report, market_analysis, sr_levels = self.market_agent.generate_report(df)
        
        # Sentiment Analysis
        sentiment_report, sentiment_analysis = self.sentiment_agent.generate_report(df)
        
        # Generate Recommendations
        recommendations = self.recommendation_agent.generate_recommendation(
            market_analysis, sentiment_analysis, sr_levels
        )
        recommendation_report = self.recommendation_agent.generate_report(recommendations)
        
        # Combined report
        full_report = f"""
{'='*80}
🤖 AI FINANCE AGENT TEAM ANALYSIS - {symbol}
{'='*80}

{market_report}

{sentiment_report}

{recommendation_report}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
"""
        
        return {
            'full_report': full_report,
            'market_analysis': market_analysis,
            'sentiment_analysis': sentiment_analysis,
            'sr_levels': sr_levels,
            'recommendations': recommendations,
            'timestamp': datetime.now()
        }
    
    def get_top_recommendation(self, df, symbol="UNKNOWN"):
        """Get the top recommendation from analysis"""
        analysis = self.analyze(df, symbol)
        
        if analysis['recommendations']:
            top_rec = max(analysis['recommendations'], key=lambda x: x['confidence'])
            return top_rec
        
        return None
    
    def should_trade(self, df, min_confidence=60):
        """
        Determine if conditions are favorable for trading
        
        Args:
            df: Price dataframe
            min_confidence: Minimum confidence threshold
        
        Returns:
            (should_trade, recommendation)
        """
        top_rec = self.get_top_recommendation(df)
        
        if top_rec and top_rec['action'] != 'WAIT' and top_rec['confidence'] >= min_confidence:
            return True, top_rec
        
        return False, top_rec

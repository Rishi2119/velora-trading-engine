"""
Phase 10 — AI Performance Optimizer
Provides a pure Python grid-search optimizer to find the best strategy parameters 
based on historical OHLCV data. Optimizes for Sharpe Ratio, Win Rate, and Drawdown.
"""
import itertools
import logging
import math
from typing import Dict, Any, List, Type
import pandas as pd
import numpy as np

from backend.app.analytics.backtester import Backtester
from backend.app.strategies.strategy_manager import BaseStrategy

logger = logging.getLogger(__name__)


def calculate_sharpe_ratio(trades: List[Dict], risk_free_rate: float = 0.0) -> float:
    """Approximate Sharpe Ratio based on trade outcomes (PnL array)."""
    if not trades or len(trades) < 2:
        return 0.0
        
    pnls = [t['pnl'] for t in trades]
    mean_pnl = np.mean(pnls)
    std_pnl = np.std(pnls)
    
    if std_pnl == 0:
        return 0.0
        
    # Simplified Sharpe per trade (unannualized for simple comparison)
    return (mean_pnl - risk_free_rate) / std_pnl


class PerformanceOptimizer:
    """
    Grid Search Optimizer for Trading Strategies.
    Evaluates combinations of parameters and ranks them by performance score.
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        
    def optimize(
        self, 
        symbol: str, 
        df: pd.DataFrame, 
        strategy_class: Type, 
        param_grid: Dict[str, List[Any]], 
        target_metric: str = "sharpe"
    ) -> Dict[str, Any]:
        """
        Run a brute-force grid search over the strategy parameters.
        Returns the best params and the top 5 results.
        """
        logger.info(f"Starting Grid Optimizer for {strategy_class.__name__} on {symbol}")
        
        # 1. Generate all parameter combinations
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        results = []
        
        # We share one Backtester instance to leverage cached features internally
        bt = Backtester(initial_balance=self.initial_balance)
        
        for combo in combinations:
            params = dict(zip(keys, combo))
            
            # Instantiate the test strategy with these params
            test_strategy = strategy_class(**params)
            
            # Monkey-patch the backtester's strategy manager to ONLY use this single strategy
            bt.strategy_manager.strategies = [test_strategy]
            
            # Run the backtest
            report = bt.run_backtest(symbol, df)
            
            if report.get("status") != "COMPLETED" or report.get("total_trades", 0) == 0:
                continue
                
            # Score Calculation
            sharpe = calculate_sharpe_ratio(report["trades"])
            win_rate = report.get("win_rate_pct", 0.0)
            roi = report.get("roi_pct", 0.0)
            drawdown = report.get("max_drawdown_pct", 100.0)
            
            # Composite Scoring could be added, but for now we follow target_metric
            if target_metric == "sharpe":
                score = sharpe
            elif target_metric == "roi":
                score = roi
            elif target_metric == "win_rate":
                score = win_rate
            elif target_metric == "safe":
                # Maximize ROI while heavily penalizing drawdown
                score = roi - (drawdown * 2.0)
            else:
                score = sharpe
                
            results.append({
                "params": params,
                "score": round(score, 4),
                "sharpe": round(sharpe, 4),
                "roi_pct": roi,
                "win_rate_pct": win_rate,
                "max_drawdown_pct": drawdown,
                "total_trades": report.get("total_trades", 0)
            })
            
        if not results:
            return {"status": "FAILED", "reason": "No valid trade configurations found in grid."}
            
        # Sort results descending by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        best = results[0]
        logger.info(f"Optimization complete. Best score: {best['score']} with params: {best['params']}")
        
        return {
            "status": "COMPLETED",
            "best_params": best["params"],
            "best_score": best["score"],
            "target_metric": target_metric,
            "top_5_results": results[:5]
        }

# Singleton
performance_optimizer = PerformanceOptimizer()

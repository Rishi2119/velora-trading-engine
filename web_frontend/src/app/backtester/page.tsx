"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { Play, Activity, Clock, Shield } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function BacktesterPage() {
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any>(null);
    const [form, setForm] = useState({
        symbol: "EURUSD",
        timeframe: "M15",
        days: 30,
        strategy: "EmaRsi_Trend"
    });

    const runBacktest = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/v1/backtest/run`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(form)
            });
            const data = await res.json();
            setResults(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    <div className="flex items-center gap-3 mb-6" style={{ justifyContent: "space-between" }}>
                        <div>
                            <h1>Backtester Engine</h1>
                            <p className="text-muted text-sm">Vectorized historical strategy evaluation</p>
                        </div>
                    </div>

                    <div className="grid-2 mb-6">
                        <div className="card">
                            <h3 className="mb-4">Configuration</h3>
                            <div className="form-group">
                                <label className="form-label">Symbol</label>
                                <input className="form-input" value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Timeframe</label>
                                <select className="form-input" value={form.timeframe} onChange={e => setForm({ ...form, timeframe: e.target.value })}>
                                    <option value="M1">M1</option>
                                    <option value="M5">M5</option>
                                    <option value="M15">M15</option>
                                    <option value="H1">H1</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Lookback (Days)</label>
                                <input type="number" className="form-input" value={form.days} onChange={e => setForm({ ...form, days: Number(e.target.value) })} />
                            </div>
                            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} onClick={runBacktest} disabled={loading}>
                                <Play size={16} /> {loading ? "Computing..." : "Run Backtest"}
                            </button>
                        </div>

                        {results && (
                            <div className="card">
                                <h3 className="mb-4">Results Map</h3>
                                <div className="grid-2">
                                    <div className="stat-card">
                                        <div className="stat-label">Total Return</div>
                                        <div className="stat-value" style={{ color: results.roi_pct >= 0 ? "var(--green)" : "var(--red)" }}>
                                            {results.roi_pct?.toFixed(2)}%
                                        </div>
                                    </div>
                                    <div className="stat-card">
                                        <div className="stat-label">Win Rate</div>
                                        <div className="stat-value">{results.win_rate_pct?.toFixed(1)}%</div>
                                    </div>
                                    <div className="stat-card">
                                        <div className="stat-label">Max Drawdown</div>
                                        <div className="stat-value" style={{ color: "var(--red)" }}>
                                            {results.max_drawdown_pct?.toFixed(2)}%
                                        </div>
                                    </div>
                                    <div className="stat-card">
                                        <div className="stat-label">Sharpe Ratio</div>
                                        <div className="stat-value">{results.sharpe_ratio?.toFixed(2)}</div>
                                    </div>
                                    <div className="stat-card" style={{ gridColumn: "span 2" }}>
                                        <div className="stat-label">Total Trades Executed</div>
                                        <div className="stat-value">{results.trades_count}</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

"use client";
import { useEffect, useState } from "react";
import {
    AreaChart, Area, BarChart, Bar, ResponsiveContainer,
    Tooltip, XAxis, YAxis, CartesianGrid
} from "recharts";
import { TrendingUp, DollarSign, Target, Zap, Activity, BarChart3, Clock } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AnalyticsMetrics() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState(30);

    useEffect(() => {
        setLoading(true);
        fetch(`${API}/api/v1/analytics/performance?days=${days}`)
            .then(r => r.json())
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [days]);

    const s = data?.summary || {};
    const curve = data?.equity_curve?.length > 0 ? data.equity_curve : [{ date: new Date().toLocaleDateString(), balance: s.balance || 0 }];
    const symbolData = Object.entries(data?.by_symbol || {}).map(([k, v]: any) => ({
        name: k, trades: v.trades, pnl: v.pnl, win_rate: v.win_rate
    }));

    const fmt = (v: number) => {
        if (v === undefined || v === null) return "0.00";
        return v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };

    const MILESTONES = [
        { id: 1, label: "First Trade Executed", reached: s.total_trades > 0 },
        { id: 2, label: "Positive Weekly Close", reached: s.total_pnl > 0 },
        { id: 3, label: "Psychology Master (3-Day Streak)", reached: true },
        { id: 4, label: "First $100 Profit", reached: s.total_pnl >= 100 },
    ];

    const StatCard = ({ label, value, icon: Icon, color = "var(--cyan)", sub }: any) => (
        <div className="glass-card" style={{ padding: "1.25rem" }}>
            <div className="flex-between mb-3">
                <span className="text-muted text-xs uppercase font-bold" style={{ letterSpacing: "0.1em" }}>{label}</span>
                <Icon size={14} style={{ color }} />
            </div>
            <div className="orbitron" style={{ fontSize: "1.4rem", fontWeight: 700, color: "white" }}>{value}</div>
            {sub && <div className="text-muted" style={{ fontSize: "10px", marginTop: "4px" }}>{sub}</div>}
        </div>
    );

    if (loading && !data) {
        return (
            <div className="flex-center" style={{ height: "60vh" }}>
                <Activity size={32} className="text-cyan pulse" />
            </div>
        );
    }

    return (
        <div className="fade-in">
            {/* Header & Filter Tabs */}
            <div className="flex-between mb-8">
                <div>
                    <h1 style={{ fontSize: "1.8rem" }}>Performance Metrics</h1>
                    <div className="text-muted text-xs uppercase mt-2">Analytical Core — Data Segmented by {days} Days</div>
                </div>
                <div style={{ display: "flex", background: "rgba(255,255,255,0.03)", padding: "4px", borderRadius: "100px", border: "1px solid var(--glass-border)" }}>
                    {[7, 30, 90, 365].map(d => (
                        <button
                            key={d}
                            onClick={() => setDays(d)}
                            style={{
                                padding: "6px 16px", borderRadius: "100px", border: "none",
                                background: days === d ? "var(--cyan)" : "transparent",
                                color: days === d ? "var(--bg-deep)" : "var(--text-main)",
                                fontSize: "10px", fontWeight: 800, cursor: "pointer",
                                transition: "all 0.3s",
                                boxShadow: days === d ? "0 0 10px var(--cyan)" : "none"
                            }}
                        >
                            {d === 365 ? "1Y" : d + "D"}
                        </button>
                    ))}
                </div>
            </div>

            {/* Progress & Insight Row */}
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
                {/* Milestone System */}
                <div className="glass-card" style={{ padding: "1.5rem", background: "linear-gradient(90deg, rgba(240, 180, 41, 0.03) 0%, transparent 100%)" }}>
                    <div className="display mb-4" style={{ fontSize: "0.8rem", color: "var(--gold)" }}>Velora Progress Milestones</div>
                    <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                        {MILESTONES.map(m => (
                            <div key={m.id} style={{ 
                                padding: "8px 16px", borderRadius: "100px", fontSize: "11px", fontWeight: 700,
                                background: m.reached ? "var(--gold)" : "rgba(255,255,255,0.03)",
                                color: m.reached ? "var(--bg-deep)" : "var(--text-muted)",
                                border: m.reached ? "none" : "1px solid var(--glass-border)",
                                boxShadow: m.reached ? "0 0 15px rgba(240, 180, 41, 0.4)" : "none",
                                display: "flex", alignItems: "center", gap: "6px"
                            }}>
                                {m.reached ? "✓" : "○"} {m.label}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Performance Insight */}
                <div className="glass-card" style={{ padding: "1.5rem", borderLeft: "3px solid var(--violet)" }}>
                    <div className="display mb-2" style={{ fontSize: "0.7rem", color: "var(--violet)" }}>AI Insight</div>
                    <div style={{ fontSize: "0.9rem", color: "var(--text-main)", fontStyle: "italic", lineHeight: "1.4" }}>
                        "Your win rate is holding stable. Focus on reducing average loss to unlock the next equity tier."
                    </div>
                </div>
            </div>

            {/* 6-Card Stats Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1.5rem", marginBottom: "2rem" }}>
                <StatCard label="Total Net P&L" value={`${s.total_pnl >= 0 ? "+" : ""}$${fmt(s.total_pnl)}`} icon={TrendingUp} color={s.total_pnl >= 0 ? "var(--success)" : "var(--danger)"} sub={s.total_trades > 0 ? "Consolidated across all clusters" : "No trades recorded yet"} />
                <StatCard label="Current Balance" value={`$${fmt(s.balance)}`} icon={DollarSign} color="var(--cyan)" sub="Available for neural allocation" />
                <StatCard label="Win Rate" value={`${(s.win_rate || 0).toFixed(1)}%`} icon={Target} color="var(--violet)" sub={`${s.winning_trades || 0}W / ${s.losing_trades || 0}L`} />
                <StatCard label="Profit Factor" value={(s.profit_factor || 0).toFixed(2)} icon={Zap} color="var(--warning)" sub="Gross Profits vs Gross Losses" />
                <StatCard label="Avg Risk:Reward" value={(s.avg_rr || 0).toFixed(1)} icon={Activity} color="white" sub="Executed expectancy ratio" />
                <StatCard label="Max Drawdown" value={`-$${fmt(Math.abs(s.max_drawdown || 0))}`} icon={BarChart3} color="var(--danger)" sub="Peak-to-trough max loss" />
            </div>


            {/* Charts Section */}
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem" }}>
                {/* Equity Curve */}
                <div className="glass-card" style={{ padding: "1.5rem" }}>
                    <div className="display mb-8" style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "10px" }}>
                        <Activity size={16} className="text-cyan" />
                        Equity Trajectory
                    </div>
                    <div style={{ width: "100%", height: 300 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={curve}>
                                <defs>
                                    <linearGradient id="curveGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--cyan)" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="var(--cyan)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 245, 255, 0.05)" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    axisLine={false} tickLine={false}
                                    tick={{ fill: "var(--text-muted)", fontSize: 10, fontFamily: "DM Mono" }}
                                />
                                <YAxis
                                    domain={["auto", "auto"]}
                                    axisLine={false} tickLine={false}
                                    tick={{ fill: "var(--text-muted)", fontSize: 10, fontFamily: "DM Mono" }}
                                    tickFormatter={(v) => `$${v.toLocaleString()}`}
                                />
                                <Tooltip
                                    contentStyle={{ background: "var(--bg-deep)", border: "1px solid var(--glass-border)", borderRadius: "8px", fontFamily: "DM Mono" }}
                                    itemStyle={{ color: "var(--cyan)" }}
                                />
                                <Area
                                    type="monotone" dataKey="balance"
                                    stroke="var(--cyan)" strokeWidth={3}
                                    fill="url(#curveGrad)"
                                    filter="drop-shadow(0 0 5px var(--cyan-glow))"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Performance by Symbol */}
                <div className="glass-card" style={{ padding: "1.5rem" }}>
                    <div className="display mb-8" style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "10px" }}>
                        <BarChart3 size={16} className="text-violet" />
                        Asset Performance
                    </div>
                    <div style={{ width: "100%", height: 300 }}>
                        {symbolData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={symbolData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" horizontal={false} />
                                    <XAxis type="number" hide />
                                    <YAxis
                                        dataKey="name" type="category"
                                        axisLine={false} tickLine={false}
                                        tick={{ fill: "white", fontSize: 10, fontFamily: "DM Mono", fontWeight: 700 }}
                                    />
                                    <Tooltip
                                        contentStyle={{ background: "var(--bg-deep)", border: "1px solid var(--glass-border)", borderRadius: "8px", fontFamily: "DM Mono" }}
                                    />
                                    <Bar
                                        dataKey="pnl"
                                        fill="var(--violet)"
                                        radius={[0, 4, 4, 0]}
                                        background={{ fill: "rgba(255,255,255,0.02)" }}
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex-center h-full flex-col opacity-30">
                                <BarChart3 size={48} className="mb-4" />
                                <div className="display" style={{ fontSize: "0.7rem" }}>No asset data available</div>
                            </div>
                        )}
                    </div>
                </div>

            </div>

            {/* Bottom Bar: Stats */}
            <div className="glass-card mt-6" style={{ padding: "1.25rem 2rem", background: "rgba(0, 245, 255, 0.02)" }}>
                <div className="flex-between">
                    <div style={{ display: "flex", gap: "3rem" }}>
                        <div>
                            <div className="text-muted text-xs uppercase font-bold mb-1">Total Signals</div>
                            <div className="orbitron" style={{ color: "white" }}>{s.total_trades || 0} EXEC</div>
                        </div>
                        <div>
                            <div className="text-muted text-xs uppercase font-bold mb-1">Avg Win</div>
                            <div className="orbitron" style={{ color: "var(--success)" }}>+${fmt(s.avg_win || 0)}</div>
                        </div>
                        <div>
                            <div className="text-muted text-xs uppercase font-bold mb-1">Avg Loss</div>
                            <div className="orbitron" style={{ color: "var(--danger)" }}>-${fmt(Math.abs(s.avg_loss || 0))}</div>
                        </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                        <div className="text-muted text-xs uppercase font-bold mb-1">Last Data Ingest</div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <Clock size={12} className="text-cyan" />
                            <span className="mono text-xs text-white">12.4s ago</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

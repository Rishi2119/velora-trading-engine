"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { analytics } from "@/lib/api";
import { BarChart3, TrendingUp, TrendingDown, Target } from "lucide-react";
import {
    AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis,
    BarChart, Bar, CartesianGrid
} from "recharts";

export default function AnalyticsPage() {
    const [performance, setPerformance] = useState<any>(null);
    const [equity, setEquity] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const [perfRes, eqRes] = await Promise.all([
                    analytics.performance(90),
                    analytics.equityCurve(90)
                ]);
                setPerformance(perfRes);
                setEquity(eqRes.curve || []);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    const fmt = (v: number | undefined, d = 2) => v?.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }) ?? "0.00";

    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    <div className="mb-6">
                        <h1 className="flex items-center gap-2"><BarChart3 size={28} color="var(--brand-primary)" /> Analytics & Performance</h1>
                        <p className="text-muted text-sm mt-1">Detailed breakdown of trading strategies and outcomes over the last 90 days.</p>
                    </div>

                    {loading ? (
                        <div className="flex-center py-12"><div className="spinner"></div></div>
                    ) : (
                        <>
                            {/* Top Stats */}
                            <div className="grid-4 mb-6">
                                <div className="stat-card">
                                    <div className="stat-label text-muted">Total Net Profit</div>
                                    <div className={`stat-value ${performance?.summary?.net_profit >= 0 ? "text-green" : "text-red"}`}>
                                        ${fmt(performance?.summary?.net_profit)}
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-label text-muted">Profit Factor</div>
                                    <div className="stat-value">{fmt(performance?.summary?.profit_factor)}</div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-label text-muted">Recovery Factor</div>
                                    <div className="stat-value">{fmt(performance?.summary?.recovery_factor)}</div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-label text-muted">Max Drawdown</div>
                                    <div className="stat-value text-red">-${fmt(Math.abs(performance?.summary?.max_drawdown ?? 0))}</div>
                                </div>
                            </div>

                            {/* Charts Grid */}
                            <div className="grid-2 mb-6">
                                {/* Equity Curve 90d */}
                                <div className="card">
                                    <h3 className="mb-4">Equity Curve (90d)</h3>
                                    <ResponsiveContainer width="100%" height={260}>
                                        <AreaChart data={equity} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                            <defs>
                                                <linearGradient id="eqGradLg" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                            <XAxis dataKey="date" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
                                            <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
                                            <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 8 }} />
                                            <Area type="monotone" dataKey="balance" stroke="#8b5cf6" strokeWidth={2} fill="url(#eqGradLg)" />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>

                                {/* Monthly Breakdown */}
                                <div className="card">
                                    <h3 className="mb-4">Monthly Return</h3>
                                    <ResponsiveContainer width="100%" height={260}>
                                        <BarChart data={performance?.monthly || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                            <XAxis dataKey="month" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
                                            <YAxis tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
                                            <Tooltip
                                                contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 8 }}
                                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                            />
                                            <Bar dataKey="pnl" fill="url(#barGrad)">
                                                {
                                                    (performance?.monthly || []).map((entry: any, index: number) => (
                                                        <cell key={`cell-${index}`} fill={entry.pnl >= 0 ? "var(--green)" : "var(--red)"} />
                                                    ))
                                                }
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Detailed Metrics */}
                            <div className="card">
                                <h3 className="mb-4">Trade Statistics</h3>
                                <div className="grid-4">
                                    <div>
                                        <div className="text-muted text-xs uppercase mb-1">Total Trades</div>
                                        <div className="font-bold text-lg">{performance?.summary?.total_trades || 0}</div>
                                    </div>
                                    <div>
                                        <div className="text-muted text-xs uppercase mb-1">Win Rate</div>
                                        <div className="font-bold text-lg text-brand">{(performance?.summary?.win_rate || 0).toFixed(1)}%</div>
                                    </div>
                                    <div>
                                        <div className="text-muted text-xs uppercase mb-1">Avg Win</div>
                                        <div className="font-bold text-lg text-green">${fmt(performance?.summary?.avg_win)}</div>
                                    </div>
                                    <div>
                                        <div className="text-muted text-xs uppercase mb-1">Avg Loss</div>
                                        <div className="font-bold text-lg text-red">-${fmt(Math.abs(performance?.summary?.avg_loss ?? 0))}</div>
                                    </div>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}

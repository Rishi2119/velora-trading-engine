"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { trading, ai, market, type TradeStats, type AgentStatus, type PriceTick } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import {
    AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis
} from "recharts";
import {
    DollarSign, TrendingUp, Activity, Shield, Brain, AlertTriangle, Wifi, WifiOff
} from "lucide-react";

// ── Auth guard ────────────────────────────────────────────────────────────────
function useAuth() {
    const router = useRouter();
    useEffect(() => {
        if (typeof window !== "undefined" && !localStorage.getItem("velora_token")) {
            router.replace("/login");
        }
    }, [router]);
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({
    label, value, sub, color = "var(--text-primary)", icon: Icon
}: {
    label: string; value: string; sub?: string; color?: string; icon: any;
}) {
    return (
        <div className="stat-card fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <span className="stat-label">{label}</span>
                <div style={{ padding: 8, background: "var(--bg-elevated)", borderRadius: 8 }}>
                    <Icon size={14} color="var(--text-secondary)" />
                </div>
            </div>
            <div className="stat-value" style={{ color }}>{value}</div>
            {sub && <div className="text-xs text-muted mt-1">{sub}</div>}
        </div>
    );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function DashboardPage() {
    useAuth();
    const [stats, setStats] = useState<TradeStats | null>(null);
    const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
    const [prices, setPrices] = useState<PriceTick[]>([]);
    const [equityData, setEquityData] = useState<any[]>([]);
    const [trades, setTrades] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchAll = useCallback(async () => {
        try {
            const [s, a, p, perf, hist] = await Promise.allSettled([
                trading.stats(),
                ai.thoughts(),
                market.prices(),
                trading.performance(30),
                trading.openPositions(),
            ]);
            if (s.status === "fulfilled") setStats(s.value);
            if (a.status === "fulfilled") setAgentStatus(a.value);
            if (p.status === "fulfilled") setPrices(p.value.prices);
            if (perf.status === "fulfilled") setEquityData(perf.value.daily || []);
            if (hist.status === "fulfilled") setTrades(hist.value.trades?.slice(0, 8) || []);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
        const interval = setInterval(fetchAll, 5000);
        return () => clearInterval(interval);
    }, [fetchAll]);

    const pnlColor = (v: number) => v >= 0 ? "var(--green)" : "var(--red)";
    const fmt = (v: number, d = 2) => v?.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }) ?? "—";

    if (loading) {
        return (
            <div className="layout">
                <Sidebar />
                <main className="main-content flex-center">
                    <div style={{ textAlign: "center" }}>
                        <div className="spinner" style={{ width: 32, height: 32, margin: "0 auto 12px" }} />
                        <p className="text-muted">Loading dashboard…</p>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    {/* Header */}
                    <div className="flex items-center gap-3 mb-6" style={{ justifyContent: "space-between" }}>
                        <div>
                            <h1>Dashboard</h1>
                            <p className="text-muted text-sm">Real-time trading overview</p>
                        </div>
                        <div className="flex items-center gap-2">
                            {stats?.mt5_connected ? (
                                <span className="badge badge-green"><span className="live-dot" style={{ marginRight: 4 }} />Live MT5</span>
                            ) : (
                                <span className="badge badge-yellow">Demo Mode</span>
                            )}
                            {stats?.kill_switch_active && (
                                <span className="badge badge-red"><AlertTriangle size={10} style={{ marginRight: 4 }} />Kill Switch ON</span>
                            )}
                        </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid-4 mb-6">
                        <StatCard
                            label="Account Balance"
                            value={`$${fmt(stats?.account_balance ?? 0)}`}
                            sub={`${stats?.currency ?? "USD"} account`}
                            icon={DollarSign}
                        />
                        <StatCard
                            label="Total P&L"
                            value={`${(stats?.total_pnl ?? 0) >= 0 ? "+" : ""}$${fmt(stats?.total_pnl ?? 0)}`}
                            sub={`Drawdown: -$${Math.abs(stats?.max_drawdown ?? 0).toFixed(2)}`}
                            color={pnlColor(stats?.total_pnl ?? 0)}
                            icon={TrendingUp}
                        />
                        <StatCard
                            label="Win Rate"
                            value={`${(stats?.win_rate ?? 0).toFixed(1)}%`}
                            sub={`${stats?.winning_trades ?? 0}W / ${stats?.losing_trades ?? 0}L`}
                            color="var(--brand-primary)"
                            icon={Activity}
                        />
                        <StatCard
                            label="Open Positions"
                            value={String(stats?.open_trades_count ?? 0)}
                            sub={`P&L: ${(stats?.open_pnl ?? 0) >= 0 ? "+" : ""}$${fmt(stats?.open_pnl ?? 0)}`}
                            color={pnlColor(stats?.open_pnl ?? 0)}
                            icon={Shield}
                        />
                    </div>

                    {/* Equity Chart + AI Status */}
                    <div className="grid-2 mb-6">
                        {/* Equity Curve */}
                        <div className="card">
                            <h3 className="mb-4">Equity Curve</h3>
                            <ResponsiveContainer width="100%" height={200}>
                                <AreaChart data={equityData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="date" hide />
                                    <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
                                    <Tooltip
                                        contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
                                        labelStyle={{ color: "var(--text-secondary)" }}
                                    />
                                    <Area type="monotone" dataKey="balance" stroke="#6366f1" strokeWidth={2} fill="url(#eqGrad)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>

                        {/* AI Agent */}
                        <div className="card">
                            <div className="flex items-center gap-2 mb-4" style={{ justifyContent: "space-between" }}>
                                <h3>AI Agent</h3>
                                <span className={`badge ${agentStatus?.is_running ? "badge-green" : "badge-yellow"}`}>
                                    {agentStatus?.is_running ? "RUNNING" : "STOPPED"}
                                </span>
                            </div>
                            {agentStatus ? (
                                <>
                                    <div className="mb-3">
                                        <div className="stat-label mb-1">Last Decision</div>
                                        <span className={`badge ${agentStatus.latest_decision === "TRADE" ? "badge-green" : agentStatus.latest_decision === "NO TRADE" ? "badge-red" : "badge-purple"}`}>
                                            {agentStatus.latest_decision || "HOLD"}
                                        </span>
                                    </div>
                                    <div className="mb-3">
                                        <div className="stat-label mb-1">Confidence</div>
                                        <div style={{ background: "var(--bg-elevated)", borderRadius: 100, height: 6, overflow: "hidden" }}>
                                            <div style={{ width: `${(agentStatus.confidence * 100).toFixed(0)}%`, height: "100%", background: "var(--gradient-brand)", borderRadius: 100 }} />
                                        </div>
                                        <div className="text-xs text-muted mt-1">{((agentStatus.confidence ?? 0) * 100).toFixed(0)}%</div>
                                    </div>
                                    <div>
                                        <div className="stat-label mb-1">Latest Thought</div>
                                        <p className="text-sm" style={{ color: "var(--text-secondary)", lineHeight: 1.6, maxHeight: 80, overflow: "hidden" }}>
                                            {agentStatus.latest_thought || "No thoughts yet."}
                                        </p>
                                    </div>
                                </>
                            ) : (
                                <p className="text-muted text-sm">Agent status unavailable</p>
                            )}
                        </div>
                    </div>

                    {/* Live Prices */}
                    <div className="card mb-6">
                        <div className="flex items-center gap-2 mb-4" style={{ justifyContent: "space-between" }}>
                            <h3>Live Prices</h3>
                            <span className="badge badge-blue"><Wifi size={10} style={{ marginRight: 4 }} />Streaming</span>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                            {prices.map(p => (
                                <div key={p.symbol} style={{
                                    flex: "1 1 140px", background: "var(--bg-elevated)", borderRadius: 10,
                                    padding: "12px 16px", border: "1px solid var(--border)"
                                }}>
                                    <div className="stat-label">{p.symbol}</div>
                                    <div className="font-bold mono" style={{ fontSize: "1rem" }}>{p.bid.toFixed(5)}</div>
                                    <div className="text-xs text-muted">Spread: {p.spread}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Recent Trades */}
                    <div className="card">
                        <h3 className="mb-4">Recent Positions</h3>
                        {trades.length === 0 ? (
                            <p className="text-muted text-sm">No trades yet.</p>
                        ) : (
                            <div className="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>ID</th><th>Symbol</th><th>Direction</th>
                                            <th>Strategy</th><th>Lots</th><th>P&L</th><th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {trades.map((t: any) => (
                                            <tr key={t.trade_id}>
                                                <td className="mono text-xs">{t.trade_id}</td>
                                                <td className="font-semibold">{t.symbol}</td>
                                                <td>
                                                    <span className={`badge ${t.direction === "BUY" || t.direction === "LONG" ? "badge-green" : "badge-red"}`}>
                                                        {t.direction}
                                                    </span>
                                                </td>
                                                <td className="text-muted text-sm">{t.strategy}</td>
                                                <td className="mono">{t.lots}</td>
                                                <td className="mono font-bold" style={{ color: pnlColor(t.pnl) }}>
                                                    {t.pnl >= 0 ? "+" : ""}${fmt(t.pnl)}
                                                </td>
                                                <td>
                                                    <span className={`badge ${t.status === "OPEN" ? "badge-green" : "badge-blue"}`}>{t.status}</span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

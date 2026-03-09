"use client";
import { useEffect, useState, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import { trading, type Trade } from "@/lib/api";
import { TrendingUp, Activity, Shield, History, Power, PowerOff } from "lucide-react";

export default function TradingPage() {
    const [activeTab, setActiveTab] = useState<"positions" | "history">("positions");
    const [positions, setPositions] = useState<Trade[]>([]);
    const [history, setHistory] = useState<Trade[]>([]);
    const [loading, setLoading] = useState(true);
    const [mt5Connected, setMt5Connected] = useState(false);
    const [killSwitch, setKillSwitch] = useState(false);
    const [killLoading, setKillLoading] = useState(false);

    const fetchTradingData = useCallback(async () => {
        try {
            const [posRes, histRes, stats] = await Promise.allSettled([
                trading.openPositions(),
                trading.history(7), // last 7 days history
                trading.stats()
            ]);
            if (posRes.status === "fulfilled") setPositions(posRes.value.trades || []);
            if (histRes.status === "fulfilled") setHistory(histRes.value.trades || []);
            if (stats.status === "fulfilled") {
                setMt5Connected(stats.value.mt5_connected);
                setKillSwitch(stats.value.kill_switch_active);
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTradingData();
        const interval = setInterval(fetchTradingData, 5000);
        return () => clearInterval(interval);
    }, [fetchTradingData]);

    const toggleKillSwitch = async () => {
        setKillLoading(true);
        try {
            if (killSwitch) {
                await trading.deactivateKillSwitch();
                setKillSwitch(false);
            } else {
                await trading.activateKillSwitch();
                setKillSwitch(true);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setKillLoading(false);
        }
    };

    const pnlColor = (v: number) => v >= 0 ? "var(--green)" : "var(--red)";
    const fmt = (v: number, d = 2) => v?.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }) ?? "—";

    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    {/* Header */}
                    <div className="flex items-center gap-3 mb-6" style={{ justifyContent: "space-between" }}>
                        <div>
                            <h1 className="flex items-center gap-2"><TrendingUp size={28} color="var(--brand-primary)" /> Trading Execution</h1>
                            <p className="text-muted text-sm mt-1">Manage positions and review trade history</p>
                        </div>
                        <div className="flex gap-3 items-center">
                            <button
                                className={`btn ${killSwitch ? "btn-danger" : "btn-secondary"}`}
                                onClick={toggleKillSwitch}
                                disabled={killLoading}
                            >
                                {killSwitch ? <PowerOff size={16} /> : <Power size={16} />}
                                {killLoading ? "..." : killSwitch ? "DEACTIVATE KILL SWITCH" : "ACTIVATE KILL SWITCH"}
                            </button>
                        </div>
                    </div>

                    <div className="grid-3 mb-6">
                        <div className="stat-card">
                            <div className="stat-label">MT5 Connection</div>
                            <div className="flex items-center gap-2 mt-2">
                                {mt5Connected ? (
                                    <><span className="live-dot" style={{ width: 12, height: 12, display: "inline-block" }} /> <span className="font-bold text-green">CONNECTED</span></>
                                ) : (
                                    <><span className="live-dot" style={{ width: 12, height: 12, display: "inline-block", background: "var(--red)", boxShadow: "0 0 6px var(--red)" }} /> <span className="font-bold text-red">DISCONNECTED</span></>
                                )}
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Open Positions</div>
                            <div className="stat-value">{positions.length}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">7D Trading Volume</div>
                            <div className="stat-value">{history.length} trades</div>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="card">
                        <div className="flex gap-4 mb-4 border-b border-[var(--border)] pb-2">
                            <button
                                className={`font-semibold ${activeTab === "positions" ? "text-brand" : "text-muted"}`}
                                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1rem" }}
                                onClick={() => setActiveTab("positions")}
                            >
                                <Shield size={16} style={{ display: "inline", marginBottom: -2, marginRight: 6 }} />
                                Open Positions
                            </button>
                            <button
                                className={`font-semibold ${activeTab === "history" ? "text-brand" : "text-muted"}`}
                                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1rem" }}
                                onClick={() => setActiveTab("history")}
                            >
                                <History size={16} style={{ display: "inline", marginBottom: -2, marginRight: 6 }} />
                                Trade History
                            </button>
                        </div>

                        {loading && positions.length === 0 && history.length === 0 ? (
                            <div className="flex-center py-8"><span className="spinner"></span></div>
                        ) : (
                            <div className="table-wrapper">
                                {activeTab === "positions" && (
                                    <table>
                                        <thead>
                                            <tr><th>ID</th><th>Symbol</th><th>Direction</th><th>Entry</th><th>SL</th><th>TP</th><th>Lots</th><th>P&L</th></tr>
                                        </thead>
                                        <tbody>
                                            {positions.length > 0 ? positions.map(t => (
                                                <tr key={t.trade_id}>
                                                    <td className="mono text-xs">{t.trade_id}</td>
                                                    <td className="font-semibold">{t.symbol}</td>
                                                    <td><span className={`badge ${t.direction.includes("BUY") ? "badge-green" : "badge-red"}`}>{t.direction}</span></td>
                                                    <td className="mono">{fmt(t.entry, 5)}</td>
                                                    <td className="mono text-red">{t.stop_loss ? fmt(t.stop_loss, 5) : "—"}</td>
                                                    <td className="mono text-green">{t.take_profit ? fmt(t.take_profit, 5) : "—"}</td>
                                                    <td className="mono">{fmt(t.lots, 2)}</td>
                                                    <td className="mono font-bold" style={{ color: pnlColor(t.pnl) }}>
                                                        {t.pnl >= 0 ? "+" : ""}${fmt(t.pnl)}
                                                    </td>
                                                </tr>
                                            )) : <tr><td colSpan={8} className="text-center text-muted py-8">No open positions.</td></tr>}
                                        </tbody>
                                    </table>
                                )}

                                {activeTab === "history" && (
                                    <table>
                                        <thead>
                                            <tr><th>Time</th><th>Symbol</th><th>Direction</th><th>Lots</th><th>P&L</th><th>Status</th></tr>
                                        </thead>
                                        <tbody>
                                            {history.length > 0 ? history.map((t, i) => (
                                                <tr key={t.trade_id || i}>
                                                    <td className="text-xs text-muted">{new Date(t.timestamp).toLocaleString()}</td>
                                                    <td className="font-semibold">{t.symbol}</td>
                                                    <td><span className={`badge ${t.direction.includes("BUY") ? "badge-green" : "badge-red"}`}>{t.direction}</span></td>
                                                    <td className="mono">{fmt(t.lots, 2)}</td>
                                                    <td className="mono font-bold" style={{ color: pnlColor(t.pnl) }}>
                                                        {t.pnl >= 0 ? "+" : ""}${fmt(t.pnl)}
                                                    </td>
                                                    <td><span className="badge badge-blue">{t.status}</span></td>
                                                </tr>
                                            )) : <tr><td colSpan={6} className="text-center text-muted py-8">No trading history available.</td></tr>}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

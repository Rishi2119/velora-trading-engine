"use client";
import { useEffect, useState, useCallback } from "react";
import { trading, type Trade } from "@/lib/api";
import {
    TrendingUp, Activity, Shield, History,
    Power, RefreshCw, AlertTriangle, ArrowUpRight,
    ArrowDownRight, Trash2, Wifi
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function TradingTerminal() {
    const [positions, setPositions] = useState<Trade[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [killWorking, setKillWorking] = useState(false);
    const [toast, setToast] = useState<{message: string, type: "success" | "danger" | "gold"} | null>(null);
    const [burstActive, setBurstActive] = useState(false);

    const showToast = (message: string, type: "success" | "danger" | "gold") => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const triggerBurst = () => {
        setBurstActive(true);
        setTimeout(() => setBurstActive(false), 1000);
    };

    const fetchData = useCallback(async () => {
        try {
            const [posRes, statsRes] = await Promise.allSettled([
                trading.openPositions(),
                fetch(`${API}/api/v1/engine/status`).then(r => r.json())
            ]);

            if (posRes.status === "fulfilled") setPositions(posRes.value.trades || []);
            if (statsRes.status === "fulfilled") setStats(statsRes.value);
        } catch (err) {
            console.error("Terminal fetch error:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const t = setInterval(fetchData, 3000);
        return () => clearInterval(t);
    }, [fetchData]);

    const handleKill = async () => {
        if (!confirm("ACTIVATE KILL SWITCH? This will liquidate all positions.")) return;
        setKillWorking(true);
        try {
            await fetch(`${API}/api/v1/engine/kill`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("velora_token")}` }
            });
            await fetchData();
        } finally {
            setKillWorking(false);
        }
    };

    const handleClose = async (ticket: string, posPnl: number) => {
        try {
            await fetch(`${API}/api/v1/trading/close/${ticket}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${localStorage.getItem("velora_token")}` }
            });
            await fetchData();
            if (posPnl > 0) {
                showToast(`✓ Trade Closed — +$${fmt(posPnl)} profit captured`, "gold");
                triggerBurst();
            } else {
                showToast(`Trade Closed`, "success");
            }
        } catch (err) {
            console.error("Close error:", err);
            showToast("Error closing trade", "danger");
        }
    };

    const fmt = (v: number, d = 2) => v?.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }) ?? "0.00";
    const pnl = stats?.mt5?.account?.profit || 0;

    return (
        <div className="fade-in">
            {/* 4-Card Metric Row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1.5rem", marginBottom: "2.5rem" }}>
                {/* MT5 Status */}
                <div className="glass-card delay-1" style={{ padding: "1.25rem" }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold">Bridge Connectivity</span>
                        <Wifi size={14} className={stats?.mt5?.connected ? "text-success" : "text-danger"} />
                    </div>
                    <div className="flex-center" style={{ gap: "10px", justifyContent: "flex-start" }}>
                        <div style={{
                            width: 10, height: 10, borderRadius: "50%",
                            background: stats?.mt5?.connected ? "var(--success)" : "var(--danger)",
                            boxShadow: `0 0 10px ${stats?.mt5?.connected ? "var(--success)" : "var(--danger)"}`
                        }} />
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            {stats?.mt5?.connected ? (
                                <span className="orbitron" style={{ fontSize: "1.2rem", fontWeight: 700, color: "white" }}>SYNC_ACTIVE</span>
                            ) : (
                                <>
                                    <RefreshCw size={14} className="text-warning spin" style={{ animation: "spin 2s linear infinite" }} />
                                    <span style={{ fontSize: "0.8rem", color: "var(--warning)", fontFamily: "DM Sans" }}>Bridge Offline — MT5 Reconnecting...</span>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Open Positions */}
                <div className="glass-card delay-2" style={{ padding: "1.25rem" }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold">Live Clusters</span>
                        <Shield size={14} className="text-violet" />
                    </div>
                    <div className="orbitron" style={{ fontSize: "2rem", fontWeight: 700, color: "white" }}>
                        {positions.length}
                    </div>
                </div>

                {/* Floating P&L */}
                <div className="glass-card delay-3" style={{ padding: "1.25rem", transition: "all 0.3s", ...(burstActive ? { borderColor: "var(--gold)", boxShadow: "0 0 30px rgba(240, 180, 41, 0.4)", transform: "scale(1.02)" } : {}) }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold">Unrealized P&L</span>
                        <Activity size={14} className={pnl >= 0 ? "text-success" : "text-danger"} />
                    </div>
                    <div className="orbitron" style={{ fontSize: "1.8rem", fontWeight: 700, color: pnl >= 0 ? "var(--success)" : "var(--danger)" }}>
                        {pnl >= 0 ? "+" : ""}{fmt(pnl)}
                    </div>
                </div>

                {/* Daily Volume */}
                <div className="glass-card delay-4" style={{ padding: "1.25rem" }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold">Daily Intensity</span>
                        <TrendingUp size={14} className="text-cyan" />
                    </div>
                    <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
                        <span className="orbitron" style={{ fontSize: "1.8rem", fontWeight: 700, color: "white" }}>
                            {stats?.risk?.daily_trades || 0}
                        </span>
                        <span className="text-muted text-xs uppercase">Orders</span>
                    </div>
                </div>
            </div>

            {/* Positions Table Section */}
            <div className="glass-card delay-5" style={{ padding: 0 }}>
                <div style={{ padding: "1.5rem 2rem", borderBottom: "1px solid var(--glass-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div className="display" style={{ fontSize: "1rem" }}>Execution Matrix</div>
                    <div style={{ display: "flex", gap: "1rem" }}>
                        <div className="badge-futuristic text-violet" style={{ background: "rgba(123, 97, 255, 0.05)" }}>MT5 Terminal v4280</div>
                    </div>
                </div>

                <div style={{ overflowX: "auto" }}>
                    <table className="velora-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Symbol</th>
                                <th>Direction</th>
                                <th>Entry</th>
                                <th>SL / TP</th>
                                <th>Lots</th>
                                <th>P&L</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {positions.length > 0 ? positions.map(pos => (
                                <tr key={pos.trade_id}>
                                    <td className="orbitron" style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{pos.trade_id}</td>
                                    <td style={{ fontWeight: 800, color: "white", letterSpacing: "0.05em" }}>{pos.symbol}</td>
                                    <td>
                                        <span className="badge-futuristic" style={{
                                            background: pos.direction.includes("BUY") ? "rgba(0, 255, 136, 0.05)" : "rgba(255, 61, 107, 0.05)",
                                            color: pos.direction.includes("BUY") ? "var(--success)" : "var(--danger)",
                                            display: "inline-flex", alignItems: "center", gap: "6px"
                                        }}>
                                            {pos.direction.includes("BUY") ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                                            {pos.direction.includes("BUY") ? "LONG" : "SHORT"}
                                        </span>
                                    </td>
                                    <td className="orbitron" style={{ fontSize: "0.85rem" }}>{fmt(pos.entry, 5)}</td>
                                    <td>
                                        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                                            <span className="text-danger" style={{ fontSize: "10px" }}>{pos.stop_loss ? fmt(pos.stop_loss, 5) : "—"}</span>
                                            <span className="text-success" style={{ fontSize: "10px" }}>{pos.take_profit ? fmt(pos.take_profit, 5) : "—"}</span>
                                        </div>
                                    </td>
                                    <td className="orbitron" style={{ fontSize: "0.85rem" }}>{fmt(pos.lots, 2)}</td>
                                    <td className="orbitron" style={{ fontSize: "0.9rem", fontWeight: 700, color: pos.pnl >= 0 ? "var(--success)" : "var(--danger)" }}>
                                        {pos.pnl >= 0 ? "+" : ""}{fmt(pos.pnl)}
                                    </td>
                                    <td>
                                        <button
                                            className="btn-outline-danger"
                                            style={{ padding: "4px 8px", fontSize: "10px" }}
                                            onClick={() => handleClose(pos.trade_id, pos.pnl)}
                                        >
                                            <Trash2 size={12} />
                                        </button>
                                    </td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan={8} style={{ padding: "4rem", textAlign: "center" }}>
                                        <div className="flex-center" style={{ flexDirection: "column", opacity: 0.8 }}>
                                            <Shield size={48} className="mb-4 text-success" style={{ opacity: 0.8 }} />
                                            <div style={{ fontSize: "1rem", color: "var(--success)", fontFamily: "DM Sans", fontWeight: 600 }}>No Open Trades — Capital Protected</div>
                                            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "12px", fontFamily: "DM Sans", fontStyle: "italic" }}>"Every great trader started with zero trades."</div>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Today's Performance Mini Bar */}
            <div style={{
                marginTop: "1.5rem", padding: "1rem 1.5rem", background: "rgba(0, 245, 255, 0.02)", 
                border: "1px solid var(--glass-border)", borderRadius: "8px",
                display: "flex", justifyContent: "space-between", alignItems: "center"
            }}>
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontFamily: "DM Sans" }}>Today's Performance</span>
                <div style={{ display: "flex", gap: "2rem", fontFamily: "DM Sans", fontSize: "0.85rem" }}>
                    <span>Trades: <strong style={{ color: "white" }}>{stats?.risk?.daily_trades || 0}</strong></span>
                    <span>Won: <strong style={{ color: "var(--success)" }}>0</strong></span>
                    <span>Lost: <strong style={{ color: "var(--danger)" }}>0</strong></span>
                    <span>Net: <strong style={{ color: "white" }}>{pnl >= 0 ? "+" : ""}${fmt(pnl)}</strong></span>
                </div>
            </div>

            {/* Toast Notification */}
            {toast && (
                <div style={{
                    position: "fixed", bottom: "2rem", left: "50%", transform: "translateX(-50%)", zIndex: 1000,
                    background: toast.type === "gold" ? "var(--gold)" : toast.type === "danger" ? "var(--danger)" : "var(--success)",
                    color: toast.type === "gold" ? "var(--bg-deep)" : "white",
                    padding: "12px 24px", borderRadius: "8px", fontWeight: 700,
                    boxShadow: `0 0 20px ${toast.type === "gold" ? "var(--gold)" : toast.type === "danger" ? "var(--danger)" : "var(--success)"}`,
                    animation: "slideUpFade 0.3s ease-out forwards", fontFamily: "DM Sans"
                }}>
                    {toast.message}
                </div>
            )}

            {/* Kill Switch Button */}
            <div style={{ position: "fixed", bottom: "2rem", right: "2rem", zIndex: 100 }}>
                <button
                    onClick={handleKill}
                    disabled={killWorking}
                    style={{
                        background: "rgba(255, 184, 0, 0.1)", color: "var(--warning)", border: "1px solid var(--warning)",
                        display: "flex", alignItems: "center", gap: "10px", padding: "0.75rem 1.5rem", borderRadius: "8px",
                        boxShadow: "0 0 15px rgba(255, 184, 0, 0.15)", transition: "all 0.3s",
                        fontFamily: "DM Sans", textTransform: "none", fontWeight: 600, cursor: "pointer"
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = "var(--danger)";
                        e.currentTarget.style.color = "white";
                        e.currentTarget.style.borderColor = "var(--danger)";
                        e.currentTarget.style.boxShadow = "0 0 20px rgba(255, 61, 107, 0.4)";
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = "rgba(255, 184, 0, 0.1)";
                        e.currentTarget.style.color = "var(--warning)";
                        e.currentTarget.style.borderColor = "var(--warning)";
                        e.currentTarget.style.boxShadow = "0 0 15px rgba(255, 184, 0, 0.15)";
                    }}
                >
                    <Shield size={18} />
                    {killWorking ? "DISARMING..." : "Emergency Stop"}
                </button>
            </div>
        </div>
    );
}

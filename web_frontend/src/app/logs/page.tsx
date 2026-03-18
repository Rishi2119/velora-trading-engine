"use client";
import { useEffect, useState, useCallback } from "react";
import {
    FileText, RefreshCw, Download, Filter,
    Search, ChevronLeft, ChevronRight, Activity,
    TrendingUp, TrendingDown, Clock, AlertCircle
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUSES = ["ALL", "EXECUTED", "PAPER", "ERROR", "REJECTED"];

export default function TradeJournal() {
    const [trades, setTrades] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("ALL");
    const [page, setPage] = useState(0);
    const PAGE_SIZE = 15;

    const fetchData = useCallback(async () => {
        try {
            const token = localStorage.getItem("velora_token");
            const res = await fetch(`${API}/api/v1/trading/journal?limit=200`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            const data = await res.json();
            setTrades(data.trades || []);
        } catch (err) {
            console.error("Journal fetch error:", err);
            setTrades([]);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleExport = () => {
        if (trades.length === 0) return;
        
        const headers = ["Timestamp", "Symbol", "Decision", "Price", "Exit Price", "PnL", "Status"];
        const csvRows = [
            headers.join(","),
            ...trades.map(t => [
                new Date(t.timestamp).toISOString(),
                t.symbol,
                t.decision,
                t.price,
                t.exit_price || "",
                t.pnl || 0,
                t.status
            ].join(","))
        ];
        
        const blob = new Blob([csvRows.join("\n")], { type: "text/csv" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.setAttribute("hidden", "");
        a.setAttribute("href", url);
        a.setAttribute("download", `velora_trades_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    useEffect(() => {
        fetchData();
        const t = setInterval(fetchData, 15000);
        return () => clearInterval(t);
    }, [fetchData]);

    const filtered = filter === "ALL" ? trades : trades.filter(t => t.status === filter);
    const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
    const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

    const getCount = (s: string) => s === "ALL" ? trades.length : trades.filter(t => t.status === s).length;

    if (loading && trades.length === 0) {
        return (
            <div className="flex-center" style={{ height: "60vh" }}>
                <Activity size={32} className="text-cyan pulse" />
            </div>
        );
    }

    return (
        <div className="fade-in">
            {/* Header & Export */}
            <header className="flex-between mb-8">
                <div>
                    <h1 style={{ fontSize: "1.8rem" }}>Trade Journal</h1>
                    <div className="text-muted text-xs uppercase mt-1">Audit Trail — {trades.length} Verified Records</div>
                </div>
                <div style={{ display: "flex", gap: "1rem" }}>
                    <button 
                        className="btn-cyan" 
                        style={{ background: "rgba(255,255,255,0.05)", color: "white", border: "1px solid var(--glass-border)", boxShadow: "none" }}
                        onClick={handleExport}
                        disabled={trades.length === 0}
                    >
                        <Download size={14} className="mr-2" /> EXPORT CSV
                    </button>
                    <button className="btn-cyan" onClick={fetchData}>
                        <RefreshCw size={14} className="mr-2" /> Sync Logs
                    </button>
                </div>
            </header>

            {/* Filter Pills */}
            <div className="glass-card mb-6" style={{ padding: "8px" }}>
                <div style={{ display: "flex", gap: "8px" }}>
                    {STATUSES.map(s => (
                        <button
                            key={s}
                            onClick={() => { setFilter(s); setPage(0); }}
                            style={{
                                padding: "8px 16px", borderRadius: "8px", border: "none",
                                background: filter === s ? "var(--cyan)" : "transparent",
                                color: filter === s ? "var(--bg-deep)" : "var(--text-main)",
                                fontSize: "10px", fontWeight: 800, cursor: "pointer",
                                display: "flex", alignItems: "center", gap: "8px",
                                transition: "all 0.3s"
                            }}
                        >
                            {s}
                            <span style={{
                                padding: "2px 6px", borderRadius: "100px",
                                background: filter === s ? "rgba(0,0,0,0.15)" : "rgba(255,255,255,0.05)",
                                color: filter === s ? "var(--bg-deep)" : "var(--text-muted)",
                                fontSize: "9px"
                            }}>{getCount(s)}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Matrix Table */}
            <div className="glass-card mb-6" style={{ padding: 0 }}>
                {paged.length > 0 ? (
                    <div style={{ overflowX: "auto" }}>
                        <table className="velora-table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Asset</th>
                                    <th>Vector</th>
                                    <th>Exec Price</th>
                                    <th>Exit Price</th>
                                    <th>P&L Delta</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {paged.map((t, i) => (
                                    <tr key={t.id || i}>
                                        <td className="orbitron" style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{new Date(t.timestamp).toLocaleTimeString()}</td>
                                        <td style={{ fontWeight: 800, color: "white" }}>{t.symbol}</td>
                                        <td>
                                            <span className="badge-futuristic" style={{
                                                color: t.decision?.includes("BUY") ? "var(--success)" :
                                                    t.decision?.includes("SELL") ? "var(--danger)" : "var(--warning)"
                                            }}>
                                                {t.decision?.includes("BUY") ? "LONG_EXE" :
                                                    t.decision?.includes("SELL") ? "SHORT_EXE" : "NEUTRAL"}
                                            </span>
                                        </td>
                                        <td className="orbitron" style={{ fontSize: "0.85rem" }}>{t.price?.toFixed(5)}</td>
                                        <td className="orbitron" style={{ fontSize: "0.85rem" }}>{t.exit_price?.toFixed(5) || "—"}</td>
                                        <td className="orbitron" style={{
                                            fontSize: "0.9rem", fontWeight: 700,
                                            color: (t.pnl || 0) >= 0 ? "var(--success)" : "var(--danger)"
                                        }}>
                                            {(t.pnl || 0) >= 0 ? "+" : ""}{(t.pnl || 0).toFixed(2)}
                                        </td>
                                        <td>
                                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                                <div style={{ width: 4, height: 4, borderRadius: "50%", background: t.status === "EXECUTED" ? "var(--success)" : "var(--warning)" }} />
                                                <span style={{ fontSize: "9px", fontWeight: 800, color: "var(--text-muted)" }}>{t.status}</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div style={{ padding: "6rem 2rem", textAlign: "center", position: "relative" }}>
                        <div style={{
                            position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)",
                            fontSize: "12rem", fontWeight: 900, color: "rgba(0, 245, 255, 0.03)", pointerEvents: "none",
                            fontFamily: "Syne", letterSpacing: "-0.05em"
                        }}>
                            VELORA
                        </div>
                        <div className="flex-center" style={{ flexDirection: "column", position: "relative", zIndex: 1 }}>
                            <FileText size={48} className="mb-6 text-muted" style={{ opacity: 0.3 }} />
                            <div className="display" style={{ fontSize: "1rem", color: "white", marginBottom: "1rem" }}>Building Your Legacy</div>
                            <div className="text-muted" style={{ maxWidth: "400px", margin: "0 auto", lineHeight: "1.6", fontSize: "0.9rem" }}>
                                Your trading history will appear here as Velora executes trades. Every decision is logged for full transparency.
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Pagination Matrix */}
            {totalPages > 1 && (
                <div className="flex-between">
                    <div className="text-muted text-xs uppercase" style={{ letterSpacing: "0.05em" }}>Page {page + 1} of {totalPages} — Syncing...</div>
                    <div style={{ display: "flex", gap: "10px" }}>
                        <button
                            className="btn-cyan"
                            style={{ padding: "8px 12px", background: "rgba(255,255,255,0.05)", border: "1px solid var(--glass-border)" }}
                            onClick={() => setPage(p => Math.max(0, p - 1))}
                            disabled={page === 0}
                        >
                            <ChevronLeft size={16} />
                        </button>
                        <button
                            className="btn-cyan"
                            style={{ padding: "8px 12px", background: "rgba(255,255,255,0.05)", border: "1px solid var(--glass-border)" }}
                            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                            disabled={page === totalPages - 1}
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

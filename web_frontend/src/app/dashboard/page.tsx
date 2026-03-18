"use client";
import { useEffect, useState, useCallback } from "react";
import VeloraAgentPanel from "@/components/VeloraAgentPanel";
import {
    Brain, Clock, Shield, Target,
    RefreshCw, ChevronRight, Zap,
    DollarSign, TrendingUp
} from "lucide-react";
import { ai, trading } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─────────────────────────────────────────────────────────────────────────────
// UI COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

function ConfidenceGauge({ value }: { value: number }) {
    const radius = 45;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (value * circumference);

    return (
        <div className="flex-center" style={{ position: "relative", width: 120, height: 120 }}>
            <svg style={{ transform: "rotate(-90deg)", width: 120, height: 120 }}>
                <circle
                    cx="60" cy="60" r={radius}
                    stroke="rgba(0, 245, 255, 0.05)" strokeWidth="8" fill="transparent"
                />
                <circle
                    cx="60" cy="60" r={radius}
                    stroke="var(--cyan)" strokeWidth="8" fill="transparent"
                    strokeDasharray={circumference}
                    style={{ strokeDashoffset: offset, transition: "stroke-dashoffset 1.5s ease" }}
                    strokeLinecap="round"
                    filter="drop-shadow(0 0 8px var(--cyan))"
                />
            </svg>
            <div style={{ position: "absolute", textAlign: "center" }}>
                <div className="orbitron" style={{ fontSize: "1.4rem", fontWeight: 900, color: "white" }}>
                    {(value * 100).toFixed(0)}%
                </div>
                <div style={{ fontSize: "0.6rem", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase" }}>Velocity</div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
    const [aiStatus, setAiStatus] = useState<any>(null);
    const [engineStatus, setEngineStatus] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [uptime, setUptime] = useState("00:00:00");

    const fetchAll = useCallback(async () => {
        try {
            const [aiRes, engineRes, tradeStats] = await Promise.all([
                ai.status(),
                fetch(`${API}/engine/status`).then(r => r.json()),
                trading.stats()
            ]);
            setAiStatus(aiRes);
            setEngineStatus({ ...engineRes, ...tradeStats });
        } catch (err) {
            console.error("Dashboard fetch error:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
        const t = setInterval(fetchAll, 3000);
        return () => clearInterval(t);
    }, [fetchAll]);

    // Uptime ticker
    useEffect(() => {
        if (!aiStatus?.uptime_seconds) {
            setUptime("00:00:00");
            return;
        }
        const timer = setInterval(() => {
            const h = Math.floor(aiStatus.uptime_seconds / 3600).toString().padStart(2, "0");
            const m = Math.floor((aiStatus.uptime_seconds % 3600) / 60).toString().padStart(2, "0");
            const s = (aiStatus.uptime_seconds % 60).toString().padStart(2, "0");
            setUptime(`${h}:${m}:${s}`);
        }, 1000);
        return () => clearInterval(timer);
    }, [aiStatus?.uptime_seconds]);

    const toggleAgent = async () => {
        setActionLoading(true);
        try {
            if (aiStatus?.is_running) {
                await ai.stop();
            } else {
                await ai.start();
            }
            await fetchAll();
        } catch (err) {
            console.error("Toggle agent error:", err);
        } finally {
            setActionLoading(false);
        }
    };

    if (loading && !aiStatus) {
        return (
            <div className="flex-center" style={{ height: "60vh" }}>
                <div style={{ textAlign: "center" }}>
                    <RefreshCw size={32} className="text-cyan" style={{ animation: "spin 2s linear infinite" }} />
                    <div className="display mt-4" style={{ fontSize: "0.8rem", letterSpacing: "0.2em", color: "var(--cyan)" }}>SYNCING NEURAL LINK...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="fade-in">
            {/* Header Content */}
            <div className="flex-between mb-8">
                <div>
                    <h1 style={{ fontSize: "1.8rem", letterSpacing: "-0.03em" }}>Intelligence Deck</h1>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "6px" }}>
                        <span className="badge-futuristic text-cyan">Node-01</span>
                        <span className="text-muted text-xs uppercase" style={{ letterSpacing: "0.1em" }}>Autonomous Trading Cluster — Verified</span>
                    </div>
                </div>
                <div style={{ display: "flex", gap: "1rem" }}>
                    <button
                        className="btn-cyan"
                        onClick={toggleAgent}
                        disabled={actionLoading}
                        style={{ 
                            minWidth: "200px", 
                            background: aiStatus?.is_running ? "var(--danger)" : "linear-gradient(135deg, var(--cyan), var(--violet))", 
                            color: aiStatus?.is_running ? "white" : "var(--bg-deep)",
                            animation: !aiStatus?.is_running ? "pulseGlow 2.5s infinite" : "none"
                        }}
                    >
                        {actionLoading ? "Processing..." : aiStatus?.is_running ? "DISCONNECT AGENT" : <><span style={{marginRight: "8px", fontSize: "1.2rem"}}>🚀</span> START VELORA AI</>}
                    </button>
                </div>
            </div>

            {/* Daily Greeting */}
            <div style={{ marginBottom: "2rem", padding: "1rem 1.5rem", background: "rgba(0, 245, 255, 0.02)", borderLeft: "3px solid var(--gold)", borderRadius: "4px" }}>
                <div style={{ color: "var(--text-main)", fontSize: "0.95rem", fontFamily: "DM Sans" }}>
                    Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}, Rishi. {new Date().getHours() >= 8 && new Date().getHours() < 16 ? "London session is active." : "Next session opens soon."} Velora is monitoring 3 pairs. Capital is protected.
                </div>
            </div>

            {/* Top Stat Cards (4-column) */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1.25rem", marginBottom: "2rem" }}>
                {/* Current Balance */}
                <div className="glass-card delay-1" style={{ padding: "1.25rem", borderLeft: "3px solid var(--cyan)" }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold" style={{ letterSpacing: "0.1em" }}>Capital Base</span>
                        <DollarSign size={14} className="text-cyan" />
                    </div>
                    <div className="orbitron" style={{ fontSize: "1.4rem", fontWeight: 700, color: "white" }}>
                        ${(engineStatus?.account_balance || 0).toLocaleString()}
                    </div>
                    <div className="text-muted" style={{ fontSize: "10px", marginTop: "4px" }}>MT5 Secured Balance</div>
                </div>

                {/* Floating Equity */}
                <div className="glass-card delay-2" style={{ padding: "1.25rem", borderLeft: "3px solid var(--violet)" }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold" style={{ letterSpacing: "0.1em" }}>Floating Equity</span>
                        <TrendingUp size={14} className="text-violet" />
                    </div>
                    <div className="orbitron" style={{ fontSize: "1.4rem", fontWeight: 700, color: "white" }}>
                        ${(engineStatus?.equity || 0).toLocaleString()}
                    </div>
                    <div style={{ fontSize: "10px", marginTop: "4px", color: (engineStatus?.open_pnl || 0) >= 0 ? "var(--success)" : "var(--danger)" }}>
                        {(engineStatus?.open_pnl >= 0 ? "+" : "")}${(engineStatus?.open_pnl || 0).toFixed(2)} Live P&L
                    </div>
                </div>

                {/* Agent Status */}
                <div className="glass-card delay-3" style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "1.25rem" }}>
                    <div style={{ position: "relative" }}>
                        <Brain size={32} className={aiStatus?.is_running ? "text-cyan" : "text-muted"} />
                        {aiStatus?.is_running && (
                            <div style={{
                                position: "absolute", top: -2, right: -2, width: 8, height: 8,
                                borderRadius: "50%", background: "var(--success)",
                                border: "2px solid var(--bg-deep)", boxShadow: "0 0 8px var(--success)"
                            }} />
                        )}
                    </div>
                    <div>
                        <div className="text-muted text-xs uppercase font-bold" style={{ letterSpacing: "0.1em" }}>Intelligence</div>
                        <div className="display" style={{ fontSize: "0.9rem", color: aiStatus?.is_running ? "white" : "var(--text-muted)" }}>
                            {aiStatus?.is_running ? "ACTIVE" : "STANDBY"}
                        </div>
                    </div>
                </div>

                {/* Session Uptime */}
                <div className="glass-card delay-4" style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "1.25rem" }}>
                    <Clock size={20} className="text-warning" />
                    <div>
                        <div className="text-muted text-xs uppercase font-bold" style={{ letterSpacing: "0.1em" }}>Uptime</div>
                        <div className="orbitron" style={{ fontSize: "1.1rem", fontWeight: 700, color: "white" }}>{uptime}</div>
                    </div>
                </div>
            </div>

            {/* Main Panel - 2 Column */}
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem" }}>

                {/* LEFT: Reasoning Feed */}
                <div className="delay-4">
                    <VeloraAgentPanel status={aiStatus} />
                </div>

                {/* RIGHT: Signal Summary Mini Panel */}
                <div className="glass-card delay-5" style={{ padding: "1.5rem" }}>
                    <div className="display mb-6" style={{ fontSize: "0.8rem", color: "white", display: "flex", alignItems: "center", gap: "8px" }}>
                        <Target size={14} className="text-cyan" />
                        Target Intelligence
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span className="text-muted text-xs uppercase">Target Pool</span>
                            <span className="orbitron" style={{ fontSize: "0.9rem", color: "white" }}>EURUSD</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span className="text-muted text-xs uppercase">Core Logic</span>
                            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "white" }}>BREAKOUT_V2</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span className="text-muted text-xs uppercase">Last Decision</span>
                            <span className="badge-futuristic" style={{
                                color: aiStatus?.latest_decision === "BUY" ? "var(--success)" :
                                    aiStatus?.latest_decision === "SELL" ? "var(--danger)" : "var(--warning)"
                            }}>
                                {aiStatus?.latest_decision || "HOLD"}
                            </span>
                        </div>

                        <div style={{ borderTop: "1px solid var(--glass-border)", paddingTop: "1.25rem" }}>
                            <div className="flex-between mb-3">
                                <span className="text-muted text-xs uppercase">Confidence Intensity</span>
                                <span className="text-xs font-bold" style={{ color: "var(--cyan)" }}>{((aiStatus?.confidence || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div style={{ height: "6px", background: "rgba(255,255,255,0.05)", borderRadius: "3px", overflow: "hidden" }}>
                                <div style={{
                                    width: `${(aiStatus?.confidence || 0) * 100}%`,
                                    height: "100%", 
                                    background: "linear-gradient(90deg, var(--cyan), var(--violet), var(--cyan))",
                                    backgroundSize: "200% 100%",
                                    boxShadow: "0 0 10px var(--cyan)",
                                    transition: "width 1s ease",
                                    animation: "gradientSlide 2s linear infinite"
                                }} />
                            </div>
                        </div>

                        {/* Risk Status Indicator */}
                        <div style={{ borderTop: "1px solid var(--glass-border)", paddingTop: "1.25rem", paddingBottom: "0.25rem" }}>
                            <div className="flex-between">
                                <span className="text-muted text-xs uppercase">Risk Status</span>
                                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                    <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)", boxShadow: "0 0 8px var(--success)" }} />
                                    <span className="badge-futuristic" style={{ color: "var(--success)", border: "none", padding: 0 }}>PROTECTED</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex-between" style={{ background: "rgba(255,255,255,0.02)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <Zap size={14} className="text-cyan" />
                                <span className="text-muted text-xs uppercase">Next Scan</span>
                            </div>
                            <span className="orbitron" style={{ fontSize: "0.8rem", color: "var(--cyan)" }}>00:24s</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

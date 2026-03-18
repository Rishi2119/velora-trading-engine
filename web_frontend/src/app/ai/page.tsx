"use client";
import { useEffect, useState, useRef } from "react";
import { ai, type AgentStatus } from "@/lib/api";
import {
    Brain, Play, Square, Activity, Cpu,
    Shield, Terminal, Zap, RefreshCw, Clock,
    Unlock, Lock
} from "lucide-react";

export default function AgentConfig() {
    const [status, setStatus] = useState<AgentStatus | null>(null);
    const [thoughtsHistory, setThoughtsHistory] = useState<{ time: string, thought: string, decision: string }[]>([]);
    const [loading, setLoading] = useState(false);
    const thoughtsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        async function pollStatus() {
            try {
                const res = await ai.status();
                setStatus(res);
                if (res.latest_thought) {
                    setThoughtsHistory(prev => {
                        if (prev.length > 0 && prev[prev.length - 1].thought === res.latest_thought) return prev;
                        return [...prev, {
                            time: new Date().toLocaleTimeString(),
                            thought: res.latest_thought,
                            decision: res.latest_decision
                        }].slice(-50);
                    });
                }
            } catch (e) {
                console.error(e);
            }
        }
        pollStatus();
        const interval = setInterval(pollStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        thoughtsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [thoughtsHistory]);

    const toggleAgent = async () => {
        setLoading(true);
        try {
            if (status?.is_running) {
                await ai.stop();
            } else {
                await ai.start();
            }
            const newStatus = await ai.status();
            setStatus(newStatus);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const toggleTrading = async () => {
        if (!status) return;
        setLoading(true);
        try {
            await ai.enableTrading(!status.demo_mode); // Assuming demo_mode is the inverse/relative of enabled trading for this context
            const newStatus = await ai.status();
            setStatus(newStatus);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fade-in">
            {/* Header */}
            <header className="flex-between mb-8">
                <div>
                    <h1 style={{ fontSize: "1.8rem" }}>Agent Processing Hub</h1>
                    <div className="text-muted text-xs uppercase mt-2">Core Neural Controller — Velora AI Engine v2.0</div>
                </div>
                <div style={{ display: "flex", gap: "1rem" }}>
                    {/* Live Trading Toggle */}
                    <button
                        className="btn-cyan"
                        style={{
                            background: "rgba(255,255,255,0.05)",
                            border: `1px solid ${status?.demo_mode ? "var(--warning)" : "var(--success)"}`,
                            color: status?.demo_mode ? "var(--warning)" : "var(--success)",
                            boxShadow: "none"
                        }}
                        onClick={toggleTrading}
                        disabled={loading || !status?.is_running}
                    >
                        {status?.demo_mode ? <><Lock size={14} className="mr-2" /> EXECUTION LOCKED</> : <><Unlock size={14} className="mr-2" /> EXECUTION UNLOCKED</>}
                    </button>

                    <button
                        className={`btn-cyan ${status?.is_running ? "bg-danger" : ""}`}
                        style={{
                            background: status?.is_running ? "var(--danger)" : "linear-gradient(135deg, var(--cyan), var(--violet))",
                             color: status?.is_running ? "white" : "var(--bg-deep)",
                            boxShadow: status?.is_running ? "0 0 20px rgba(255, 61, 107, 0.3)" : "0 0 20px var(--cyan-glow)",
                            animation: !status?.is_running ? "pulseGlow 2.5s infinite" : "none",
                            fontWeight: 700
                        }}
                        onClick={toggleAgent}
                        disabled={loading}
                    >
                        {loading ? <RefreshCw className="spin" size={16} /> : status?.is_running ? <><Square size={16} className="mr-2" /> TERMINATE PROCESS</> : <><Play size={16} className="mr-2" /> INITIALIZE AGENT</>}
                    </button>
                </div>
            </header>

            {/* Neural Stats */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1.5rem", marginBottom: "2.5rem" }}>
                <div className="glass-card" style={{ padding: "1.5rem" }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold">Model Integrity</span>
                        <Cpu size={14} className={status?.is_running ? "text-success" : "text-danger"} />
                    </div>
                    <div className="display" style={{ fontSize: "1.0rem", color: "white", marginTop: "4px" }}>
                        {status?.is_running ? "SYS_ACTIVE" : "Engine Standby"}
                    </div>
                    {!status?.is_running && <div style={{ fontSize: "10px", color: "var(--warning)", marginTop: "4px" }}>Ready to Initialize</div>}
                </div>

                <div className="glass-card" style={{ padding: "1.5rem" }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold">Reasoning Confidence</span>
                        <Zap size={14} className="text-violet" />
                    </div>
                    <div className="orbitron" style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--violet)" }}>
                        {((status?.confidence ?? 0) * 100).toFixed(1)}%
                    </div>
                </div>

                <div className="glass-card" style={{ padding: "1.5rem" }}>
                    <div className="flex-between mb-3">
                        <span className="text-muted text-xs uppercase font-bold">Process Uptime</span>
                        <Clock size={14} className="text-cyan" />
                    </div>
                    <div className="orbitron" style={{ fontSize: "1.4rem", fontWeight: 700, color: "white" }}>
                        {(status?.uptime_seconds ?? 0) > 0 ? `${Math.floor((status?.uptime_seconds ?? 0) / 60)}m ${String((status?.uptime_seconds ?? 0) % 60).padStart(2, '0')}s` : "00:00:00"}
                    </div>
                </div>
            </div>

            {/* Reasoning Feed */}
            <div className="glass-card" style={{ padding: 0 }}>
                <div style={{ padding: "1.5rem 2rem", borderBottom: "1px solid var(--glass-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div className="display" style={{ fontSize: "0.85rem" }}>Neural Reasoning Stream</div>
                    {status?.demo_mode && <span className="badge-futuristic text-warning">Simulation Active</span>}
                </div>

                <div style={{
                    height: "500px", overflowY: "auto", padding: "1.5rem 2rem",
                    fontFamily: "DM Mono", fontSize: "0.85rem", lineHeight: "1.6",
                    background: "rgba(0,0,0,0.2)"
                }}>
                    {thoughtsHistory.length === 0 ? (
                        <div className="flex-center h-full flex-col" style={{ opacity: 0.5 }}>
                            <Activity size={48} className="mb-4 text-cyan" style={{ animation: "pulse 2s infinite" }} />
                            <div className="display" style={{ fontSize: "0.8rem", color: "var(--cyan)" }}>Velora AI — Awaiting Activation...</div>
                            <div className="text-muted mt-2" style={{ fontSize: "11px" }}>Neural bridge standby. All systems nominal.</div>
                        </div>
                    ) : (
                        thoughtsHistory.map((t, i) => (
                            <div key={i} className="mb-6 fade-in" style={{ borderLeft: "2px solid var(--glass-border)", paddingLeft: "1.5rem" }}>
                                <div className="flex items-center gap-3 mb-2">
                                    <span className="text-muted" style={{ fontSize: "10px" }}>[{t.time}]</span>
                                    <span className="badge-futuristic" style={{
                                        color: t.decision?.includes("BUY") ? "var(--success)" :
                                            t.decision?.includes("SELL") ? "var(--danger)" : "var(--cyan)"
                                    }}>
                                        {t.decision}
                                    </span>
                                </div>
                                <div style={{ color: "rgba(255,255,255,0.8)" }}>{t.thought}</div>
                            </div>
                        ))
                    )}
                    <div ref={thoughtsEndRef} />
                </div>

                {/* Session Summary Footer */}
                <div style={{ padding: "1rem 2rem", borderTop: "1px solid var(--glass-border)", background: "rgba(0, 245, 255, 0.02)", display: "flex", gap: "3rem" }}>
                    <div>
                        <div className="text-muted text-xs uppercase font-bold mb-1">Signals Processed</div>
                        <div className="orbitron" style={{ color: "white" }}>{thoughtsHistory.length} EXEC</div>
                    </div>
                    <div>
                        <div className="text-muted text-xs uppercase font-bold mb-1">Last Action</div>
                        <div className="orbitron" style={{ color: "var(--cyan)" }}>{thoughtsHistory.length > 0 ? thoughtsHistory[thoughtsHistory.length - 1].decision : "NONE"}</div>
                    </div>
                    <div style={{ marginLeft: "auto", textAlign: "right" }}>
                        <div className="text-muted text-xs uppercase font-bold mb-1">Uptime</div>
                        <div className="orbitron" style={{ color: "white" }}>
                            {(status?.uptime_seconds ?? 0) > 0 ? `${Math.floor((status?.uptime_seconds ?? 0) / 60)}M ${String((status?.uptime_seconds ?? 0) % 60).padStart(2, '0')}S` : "00:00"}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

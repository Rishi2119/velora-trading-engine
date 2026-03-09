"use client";
import { useEffect, useState, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import { ai, type AgentStatus } from "@/lib/api";
import { Brain, Play, Square, Activity, Cpu } from "lucide-react";

export default function AIPage() {
    const [status, setStatus] = useState<AgentStatus | null>(null);
    const [thoughtsHistory, setThoughtsHistory] = useState<{ time: string, thought: string, decision: string }[]>([]);
    const [loading, setLoading] = useState(false);

    const thoughtsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        async function pollStatus() {
            try {
                const res = await ai.status();
                setStatus(res);
                setThoughtsHistory(prev => {
                    if (!res.latest_thought) return prev;
                    // Only add if it's new
                    if (prev.length > 0 && prev[prev.length - 1].thought === res.latest_thought) return prev;
                    const newHistory = [...prev, {
                        time: new Date().toLocaleTimeString(),
                        thought: res.latest_thought,
                        decision: res.latest_decision
                    }];
                    return newHistory.slice(-50); // Keep last 50
                });
            } catch (e) {
                console.error(e);
            }
        }
        pollStatus();
        const interval = setInterval(pollStatus, 3000); // Polling every 3s
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

    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    <div className="flex items-center gap-3 mb-6" style={{ justifyContent: "space-between" }}>
                        <div>
                            <h1 className="flex items-center gap-2"><Brain size={28} color="var(--brand-primary)" /> Autonomous AI Engine</h1>
                            <p className="text-muted text-sm mt-1">Control and monitor the NVIDIA NIM reasoning agent</p>
                        </div>
                        <div className="flex gap-3">
                            <button
                                className={`btn ${status?.is_running ? "btn-danger" : "btn-primary"} btn-lg`}
                                onClick={toggleAgent}
                                disabled={loading}
                            >
                                {loading ? <span className="spinner" /> : status?.is_running ? <><Square size={16} /> STOP AGENT</> : <><Play size={16} fill="currentColor" /> START AGENT</>}
                            </button>
                        </div>
                    </div>

                    <div className="grid-3 mb-6">
                        <div className="stat-card">
                            <div className="stat-label">Model Status</div>
                            <div className="flex items-center gap-2 mt-2">
                                {status?.is_running ? (
                                    <span className="badge badge-green"><Cpu size={12} style={{ marginRight: 4 }} /> RUNNING</span>
                                ) : (
                                    <span className="badge badge-yellow" style={{ opacity: 0.7 }}>OFFLINE</span>
                                )}
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Current Strategy Confidence</div>
                            <div className="flex items-baseline gap-2">
                                <div className="stat-value text-brand">{((status?.confidence ?? 0) * 100).toFixed(0)}%</div>
                            </div>
                            <div className="text-xs text-muted mt-1">NVIDIA Kimi K2.5 Output</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Uptime</div>
                            <div className="stat-value">{(status?.uptime_seconds ?? 0) > 0 ? `${Math.floor((status?.uptime_seconds ?? 0) / 60)}m ${(status?.uptime_seconds ?? 0) % 60}s` : "0m 0s"}</div>
                        </div>
                    </div>

                    <div className="card mb-6 flex flex-col" style={{ height: "400px" }}>
                        <h3 className="mb-4 flex items-center gap-2">
                            <Activity size={18} color="var(--brand-primary)" /> Agent Reasoning Log
                            {status?.demo_mode && <span className="badge badge-purple text-xs ml-auto">Demo Data</span>}
                        </h3>
                        <div className="flex-1 bg-[var(--bg-elevated)] border border-[var(--border)] rounded-md p-4 overflow-y-auto font-mono text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                            {thoughtsHistory.length === 0 ? (
                                <div className="h-full flex-center opacity-50">Waiting for agent thoughts...</div>
                            ) : (
                                thoughtsHistory.map((t, i) => (
                                    <div key={i} className="mb-4 pb-4 border-b border-[rgba(255,255,255,0.05)] last:border-0">
                                        <div className="flex gap-3 mb-1">
                                            <span className="text-muted text-xs">[{t.time}]</span>
                                            <span className={`badge text-xs px-2 py-0 h-[20px] ${t.decision.includes("BUY") || t.decision.includes("LONG") ? "badge-green" : t.decision.includes("SELL") || t.decision.includes("SHORT") ? "badge-red" : "badge-blue"}`}>
                                                {t.decision}
                                            </span>
                                        </div>
                                        <div className="text-[var(--text-primary)] whitespace-pre-wrap">{t.thought}</div>
                                    </div>
                                ))
                            )}
                            <div ref={thoughtsEndRef} />
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

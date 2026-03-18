"use client";
import { useEffect, useRef, useState } from "react";
import { Terminal, Cpu, Zap, AlertCircle, Info } from "lucide-react";

interface LogEntry {
    timestamp: string;
    type: "SIGNAL" | "BUY" | "SELL" | "HOLD" | "ERROR" | "INFO";
    message: string;
    id: string;
}

export default function VeloraAgentPanel({ status }: { status: any }) {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const bodyRef = useRef<HTMLDivElement>(null);

    // Update logs when status changes
    useEffect(() => {
        if (!status?.latest_thought) return;

        const newLog: LogEntry = {
            timestamp: new Date().toLocaleTimeString(),
            type: status.latest_decision === "BUY" ? "BUY" :
                status.latest_decision === "SELL" ? "SELL" :
                    status.latest_decision === "HOLD" ? "HOLD" : "SIGNAL",
            message: status.latest_thought,
            id: Math.random().toString(36).substring(7)
        };

        setLogs(prev => {
            // Avoid duplicate logs if status hasn't changed
            if (prev.length > 0 && prev[prev.length - 1].message === newLog.message) return prev;
            const updated = [...prev, newLog].slice(-100); // Keep last 100
            return updated;
        });
    }, [status?.latest_thought, status?.latest_decision]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (bodyRef.current) {
            bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
        }
    }, [logs]);

    const getTypeColor = (type: string) => {
        switch (type) {
            case "BUY": return "var(--success)";
            case "SELL": return "var(--danger)";
            case "ERROR": return "var(--danger)";
            case "HOLD": return "var(--warning)";
            default: return "var(--cyan)";
        }
    };

    const getTypeIcon = (type: string) => {
        switch (type) {
            case "BUY":
            case "SELL": return <Zap size={12} />;
            case "ERROR": return <AlertCircle size={12} />;
            case "HOLD": return <Cpu size={12} />;
            default: return <Info size={12} />;
        }
    };

    return (
        <div className="terminal-container glass-card" style={{ height: "400px", display: "flex", flexDirection: "column", padding: 0 }}>
            <div className="terminal-header">
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Terminal size={14} />
                    <span style={{ fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.1em" }}>Velora Reasoning Log</span>
                </div>
                <div style={{ color: "var(--text-muted)" }}>AGENT_ID: VLR-CORE-ENGINE</div>
            </div>

            <div className="terminal-body" ref={bodyRef}>
                {logs.length === 0 ? (
                    <div className="text-muted" style={{ height: "100%", display: "flex", alignItems: "center", justifyItems: "center", justifyContent: "center" }}>
                        <div style={{ textAlign: "center", display: "flex", alignItems: "center", gap: "8px" }}>
                            <div className="pulse-dot" style={{ background: "var(--cyan)" }} />
                            <span style={{ fontFamily: "DM Mono", color: "var(--cyan)", letterSpacing: "0.05em" }}>
                                Velora AI Engine — Monitoring market conditions<span style={{ animation: "pulse 1s infinite" }}>_</span>
                            </span>
                        </div>
                    </div>
                ) : (
                    logs.map((log) => (
                        <div key={log.id} className="log-entry" style={{
                            borderLeft: `3px solid ${getTypeColor(log.type)}`,
                            background: "rgba(0, 245, 255, 0.02)",
                            padding: "8px 12px",
                            marginBottom: "8px",
                            borderRadius: "0 4px 4px 0",
                            display: "flex",
                            alignItems: "flex-start",
                            gap: "12px"
                        }}>
                            <span style={{ color: "var(--text-muted)", fontSize: "11px", whiteSpace: "nowrap", paddingTop: "2px" }}>[{log.timestamp}]</span>
                            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                                <span style={{
                                    color: getTypeColor(log.type),
                                    fontWeight: 800,
                                    display: "inline-flex",
                                    alignItems: "center",
                                    gap: "6px",
                                    fontSize: "11px",
                                    letterSpacing: "0.1em"
                                }}>
                                    {getTypeIcon(log.type)}
                                    {log.type}
                                </span>
                                <span style={{ color: "var(--text-main)", fontSize: "13px", lineHeight: "1.4" }}>{log.message}</span>
                            </div>
                        </div>
                    ))
                )}
            </div>

            <div style={{ padding: "8px 1rem", borderTop: "1px solid var(--glass-border)", fontSize: "10px", color: "var(--text-muted)", display: "flex", justifyContent: "space-between" }}>
                <span>STATUS: {status?.is_running ? "STREAMING" : "IDLE"}</span>
                <span>BUFFER: {logs.length}/100</span>
            </div>
        </div>
    );
}

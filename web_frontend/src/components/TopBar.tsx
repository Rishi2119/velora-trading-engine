"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import {
    Bell, Clock, Layout, ChevronRight,
    Wifi, Globe, User, Terminal
} from "lucide-react";
import { useEngineWS } from "@/lib/useEngineWS";

export default function TopBar() {
    const pathname = usePathname();
    const { mt5Connected } = useEngineWS();
    const [time, setTime] = useState("");
    const [sessions, setSessions] = useState<{ name: string, active: boolean }[]>([]);

    useEffect(() => {
        const update = () => {
            const now = new Date();
            setTime(now.toLocaleTimeString("en-US", { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }));

            // Basic session indicator logic (UTC)
            const hour = now.getUTCHours();
            setSessions([
                { name: "LONDON", active: hour >= 8 && hour < 16 },
                { name: "NEW YORK", active: hour >= 13 && hour < 21 },
                { name: "TOKYO", active: (hour >= 0 && hour < 9) || hour >= 23 }
            ]);
        };
        update();
        const t = setInterval(update, 1000);
        return () => clearInterval(t);
    }, []);

    // Get breadcrumb
    const pageName = pathname.split("/").pop() || "Intelligence";
    const displayName = pageName.charAt(0).toUpperCase() + pageName.slice(1);

    return (
        <header style={{
            height: "64px", borderBottom: "1px solid var(--glass-border)",
            background: "rgba(2, 11, 24, 0.8)", backdropFilter: "blur(12px)",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "0 2rem", zIndex: 50, position: "sticky", top: 0
        }}>
            {/* Left: Breadcrumbs */}
            < div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Layout size={14} className="text-muted" />
                <span className="text-muted text-xs uppercase" style={{ letterSpacing: "0.1em" }}>VELORA</span>
                <ChevronRight size={12} className="text-muted" />
                <span style={{
                    fontFamily: "Syne, sans-serif", fontWeight: 800, fontSize: "0.9rem",
                    textTransform: "uppercase", color: "white", letterSpacing: "0.05em"
                }}>{displayName}</span>
            </div >

            {/* Center: Live Market Clock */}
            < div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <Clock size={14} className="text-cyan" />
                    <span className="orbitron" style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--cyan)", minWidth: "100px" }}>{time}</span>
                </div>

                <div style={{ display: "flex", gap: "12px" }}>
                    {sessions.map(s => (
                        <div key={s.name} style={{
                            display: "flex", alignItems: "center", gap: "6px",
                            opacity: s.active ? 1 : 0.3, transition: "opacity 0.3s"
                        }}>
                            <div style={{
                                width: 4, height: 4, borderRadius: "50%",
                                background: s.active ? "var(--success)" : "var(--text-muted)",
                                boxShadow: s.active ? "0 0 5px var(--success)" : "none"
                            }} />
                            <span style={{ fontSize: "9px", fontWeight: 800, color: s.active ? "white" : "var(--text-muted)", letterSpacing: "0.05em" }}>{s.name}</span>
                        </div>
                    ))}
                </div>
            </div >

            {/* Right: Status & Account */}
            < div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
                {/* MT5 Status Pill */}
                < div style={{
                    background: mt5Connected ? "rgba(0, 245, 255, 0.03)" : "rgba(255, 71, 87, 0.03)",
                    border: `1px solid ${mt5Connected ? "var(--glass-border)" : "rgba(255, 71, 87, 0.2)"}`,
                    borderRadius: "100px", padding: "4px 12px",
                    display: "flex", alignItems: "center", gap: "8px",
                    transition: "all 0.3s"
                }}>
                    <Wifi size={12} className={mt5Connected ? "text-cyan" : "text-danger"} />
                    <span style={{ 
                        fontSize: "10px", fontWeight: 800, 
                        color: mt5Connected ? "var(--cyan)" : "var(--danger)", 
                        letterSpacing: "0.05em" 
                    }}>
                        MT5 : {mt5Connected ? "LIVE" : "OFFLINE"}
                    </span>
                </div >

                <div style={{ display: "flex", alignItems: "center", gap: "1rem", borderLeft: "1px solid var(--glass-border)", paddingLeft: "1.5rem" }}>
                    <Bell size={18} className="text-muted" style={{ cursor: "pointer" }} />
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }}>
                        <div style={{ textAlign: "right", display: "none" }}>
                            <div style={{ fontSize: "11px", fontWeight: 700, color: "white" }}>ADMIN</div>
                            <div style={{ fontSize: "9px", color: "var(--text-muted)" }}>node_01</div>
                        </div>
                        <div style={{
                            width: 32, height: 32, borderRadius: "50%",
                            border: "1px solid var(--glass-border)",
                            background: "rgba(255,255,255,0.05)",
                            display: "flex", alignItems: "center", justifyContent: "center"
                        }}>
                            <User size={16} className="text-cyan" />
                        </div>
                    </div>
                </div>
            </div >
        </header >
    );
}

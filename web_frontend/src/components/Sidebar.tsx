"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { auth } from "@/lib/api";
import {
    LayoutDashboard, Terminal, Zap, Brain,
    BarChart3, FileText, Settings, LogOut,
    AlertTriangle, ShieldCheck
} from "lucide-react";
import { useEngineWS } from "@/lib/useEngineWS";

const NAV_ITEMS = [
    { href: "/dashboard", label: "Intelligence", icon: LayoutDashboard },
    { href: "/trading", label: "Live Trading", icon: Terminal },
    { href: "/strategies", label: "Strategy Config", icon: Zap },
    { href: "/ai", label: "AI Control", icon: Brain },
    { href: "/analytics", label: "Performance", icon: BarChart3 },
    { href: "/logs", label: "Trade Journal", icon: FileText },
    { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
    const path = usePathname();
    const { mt5Connected, killSwitchActive, lastError } = useEngineWS();
    const isConnected = mt5Connected;

    return (
        <aside className="sidebar">
            {/* Logo Section */}
            <div style={{ padding: "2rem 1.5rem 3rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    {/* Geometric V Logo */}
                    <div style={{
                        width: 38, height: 38, position: "relative",
                        background: "linear-gradient(135deg, var(--cyan), var(--violet))",
                        clipPath: "polygon(50% 100%, 0 0, 100% 0)",
                        boxShadow: "0 0 20px var(--cyan-glow)"
                    }}>
                        <div style={{
                            position: "absolute", inset: 2,
                            background: "var(--bg-deep)",
                            clipPath: "polygon(50% 100%, 0 0, 100% 0)",
                            display: "flex", alignItems: "center", justifyItems: "center", justifyContent: "center"
                        }}>
                            <div style={{ width: 12, height: 4, background: "var(--cyan)", borderRadius: 2 }} />
                        </div>
                    </div>
                    <div>
                        <div style={{
                            fontFamily: "Syne, sans-serif", fontWeight: 800,
                            fontSize: "1.4rem", letterSpacing: "-0.05em", color: "white",
                            lineHeight: 1
                        }}>VELORA</div>
                        <div style={{
                            fontSize: "0.6rem", fontWeight: 900, color: "var(--text-muted)",
                            textTransform: "uppercase", letterSpacing: "0.25em",
                            marginTop: "2px"
                        }}>AI ENGINE V2.0</div>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px" }}>
                {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
                    const isActive = path === href || path.startsWith(href + "/");
                    return (
                        <Link
                            key={href}
                            href={href}
                            className={`nav-item${isActive ? " active" : ""}`}
                            style={{
                                display: "flex", alignItems: "center", gap: "12px",
                                padding: "0.85rem 1.5rem", color: isActive ? "var(--cyan)" : "var(--text-main)",
                                textDecoration: "none", fontSize: "0.85rem", fontWeight: isActive ? 600 : 400,
                                position: "relative", transition: "all 0.3s",
                                borderLeft: "3px solid transparent",
                                background: isActive ? "linear-gradient(90deg, rgba(0, 245, 255, 0.08) 0%, transparent 100%)" : "transparent"
                            }}
                        >
                            {isActive && (
                                <div style={{
                                    position: "absolute", left: -3, top: 0, bottom: 0, width: 3,
                                    background: "var(--cyan)", boxShadow: "0 0 15px var(--cyan)"
                                }} />
                            )}
                            <Icon size={18} strokeWidth={isActive ? 2.5 : 1.5} />
                            <span style={{ fontFamily: isActive ? "Syne, sans-serif" : "inherit" }}>{label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Bottom Status & Actions */}
            <div style={{
                padding: "1.5rem", borderTop: "1px solid var(--glass-border)",
                background: "rgba(0,0,0,0.2)"
            }}>
                {/* Discipline Streak */}
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem", color: "var(--gold)", marginBottom: "1rem" }}>
                    <span>🔥</span> <span style={{ fontWeight: 600, fontFamily: "DM Sans" }}>3-day discipline streak</span>
                </div>

                {/* Active Error Warning */}
                {lastError && (
                    <div style={{
                        background: "rgba(255, 71, 87, 0.05)",
                        border: "1px solid rgba(255, 71, 87, 0.3)",
                        borderRadius: "4px", padding: "8px 12px",
                        display: "flex", alignItems: "center", gap: "10px",
                        marginBottom: "1rem"
                    }}>
                        <AlertTriangle size={14} className="text-danger" />
                        <span style={{ fontSize: "10px", fontWeight: 600, color: "var(--danger)", letterSpacing: "0.02em" }}>{lastError}</span>
                    </div>
                )}

                {/* Kill Switch Warning */}
                {killSwitchActive && (
                    <div style={{
                        background: "rgba(255, 71, 87, 0.1)",
                        border: "1px solid var(--danger)",
                        borderRadius: "4px", padding: "8px 12px",
                        display: "flex", alignItems: "center", gap: "10px",
                        marginBottom: "1rem",
                        animation: "pulseGlow 2s infinite"
                    }}>
                        <AlertTriangle size={14} className="text-danger" />
                        <span style={{ fontSize: "10px", fontWeight: 800, color: "var(--danger)", letterSpacing: "0.1em" }}>KILL SWITCH ACTIVE</span>
                    </div>
                )}

                {/* MT5 Status Pill */}
                <div style={{
                    background: isConnected ? "rgba(0, 230, 118, 0.03)" : "rgba(255, 71, 87, 0.03)",
                    border: `1px solid ${isConnected ? "rgba(0, 230, 118, 0.1)" : "rgba(255, 71, 87, 0.1)"}`,
                    borderRadius: "4px", padding: "8px 12px",
                    display: "flex", alignItems: "center", gap: "10px",
                    marginBottom: "1rem",
                    transition: "all 0.3s"
                }}>
                    <div style={{
                        width: 6, height: 6, borderRadius: "50%", 
                        background: isConnected ? "var(--success)" : "var(--danger)",
                        boxShadow: `0 0 8px ${isConnected ? "var(--success)" : "var(--danger)"}`
                    }} />
                    <span style={{ 
                        fontSize: "10px", fontWeight: 700, 
                        color: isConnected ? "var(--success)" : "var(--danger)", 
                        letterSpacing: "0.1em" 
                    }}>
                        {isConnected ? "TERMINAL CLOUD SYNCED" : "TERMINAL DISCONNECTED"}
                    </span>
                </div>

                {/* Calm Footer */}
                <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "DM Sans" }}>
                    <div style={{ 
                        width: 6, height: 6, borderRadius: "50%", 
                        background: isConnected ? "var(--success)" : "var(--danger)" 
                    }} />
                    <span>{isConnected ? "Connected" : "Offline"}</span> <span style={{ opacity: 0.5 }}>|</span> <span>Velora V2.0</span> <span style={{ opacity: 0.5 }}>|</span>
                    <button onClick={() => auth.logout()} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", textDecoration: "underline", padding: 0, fontSize: "inherit", fontFamily: "inherit" }}>
                        Disconnect
                    </button>
                </div>
            </div>

            <style jsx>{`
                .nav-item:hover {
                    color: white !important;
                    background: rgba(255, 255, 255, 0.02) !important;
                }
            `}</style>
        </aside>
    );
}

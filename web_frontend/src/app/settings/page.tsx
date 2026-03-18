"use client";
import { useState, useEffect } from "react";
import { trading, auth } from "@/lib/api";
import {
    Settings, Save, AlertTriangle, ShieldCheck,
    User, Mail, Database, Trash2, Github,
    Server, Activity, Terminal
} from "lucide-react";
import MT5ConnectModal from "@/components/MT5ConnectModal";

export default function SystemsSettings() {
    const [user, setUser] = useState<any>(null);
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState("");
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        setUser(auth.getUser());
        trading.mt5Status().then(setStatus).catch(console.error);
    }, []);

    const handleDisconnect = async () => {
        setLoading(true);
        try {
            await trading.disconnectMT5();
            setStatus({ connected: false });
        } finally {
            setLoading(false);
        }
    };

    const SectionHeader = ({ icon: Icon, title, sub }: any) => (
        <div className="flex items-center gap-4 mb-6">
            <div style={{ padding: "10px", background: "rgba(0, 245, 255, 0.05)", border: "1px solid var(--glass-border)", borderRadius: "8px" }}>
                <Icon size={20} className="text-cyan" />
            </div>
            <div>
                <h3 className="display" style={{ fontSize: "1rem", color: "white" }}>{title}</h3>
                <p className="text-muted" style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.05em" }}>{sub}</p>
            </div>
        </div>
    );

    return (
        <div className="fade-in" style={{ maxWidth: "800px", margin: "0 auto" }}>
            {/* Header */}
            <header className="mb-10">
                <h1 style={{ fontSize: "2rem" }}>Settings</h1>
                <div className="text-muted text-xs uppercase mt-1">Platform Integrity & Authentication Nexus</div>
            </header>

            <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>

                {/* MT5 Integration */}
                <div className="glass-card delay-1" style={{ padding: "2rem" }}>
                    <SectionHeader icon={Terminal} title="Broker Integration" sub="MetaTrader 5 Native Bridge" />

                    {status?.connected ? (
                        <div style={{
                            background: "rgba(0, 255, 136, 0.05)", border: "1px solid rgba(0, 255, 136, 0.1)",
                            borderRadius: "12px", padding: "1.5rem"
                        }}>
                            <div className="flex-between mb-4">
                                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                                    <div style={{
                                        width: 10, height: 10, borderRadius: "50%", background: "var(--success)",
                                        boxShadow: "0 0 10px var(--success)"
                                    }} />
                                    <span className="display" style={{ fontSize: "0.9rem", color: "white" }}>Terminal Bridge Active</span>
                                </div>
                                <button className="btn-outline-danger" onClick={handleDisconnect} disabled={loading} style={{ fontSize: "10px", borderColor: "var(--danger)", color: "var(--danger)" }}>Disconnect MT5</button>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                                <div style={{ padding: "12px", background: "rgba(0,0,0,0.2)", borderRadius: "8px" }}>
                                    <div className="text-muted text-[10px] uppercase mb-1">Broker Identity</div>
                                    <div className="orbitron text-xs text-white">MetaQuotes-Demo</div>
                                </div>
                                <div style={{ padding: "12px", background: "rgba(0,0,0,0.2)", borderRadius: "8px" }}>
                                    <div className="text-muted text-[10px] uppercase mb-1">Latency Layer</div>
                                    <div className="orbitron text-xs text-success">12.4ms Synchronized</div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div style={{ textAlign: "center", padding: "2rem", border: "1px dashed var(--glass-border)", borderRadius: "12px" }}>
                            <Server size={32} className="text-muted mb-3" style={{ opacity: 0.3 }} />
                            <div className="text-muted text-sm">No active terminal link detected.</div>
                            <button 
                                className="btn-cyan mt-4" 
                                style={{ padding: "8px 20px", fontSize: "10px" }}
                                onClick={() => setIsModalOpen(true)}
                            >
                                Establish New Link
                            </button>
                        </div>
                    )}
                </div>

                <MT5ConnectModal 
                    isOpen={isModalOpen} 
                    onClose={() => setIsModalOpen(false)} 
                    onSuccess={(newStatus) => setStatus(newStatus)}
                />

                {/* Account Profile */}
                <div className="glass-card delay-2" style={{ padding: "2rem" }}>
                    <SectionHeader icon={User} title="Authenticator Profile" sub="User Identity Data" />

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                        <div>
                            <label className="text-muted text-xs uppercase font-bold mb-2 block">Primary Identity</label>
                            <div style={{
                                padding: "10px 14px", background: "rgba(255,255,255,0.02)",
                                border: "1px solid var(--glass-border)", borderRadius: "4px",
                                color: "var(--text-main)", fontSize: "0.85rem",
                                display: "flex", justifyContent: "space-between", alignItems: "center"
                            }}>
                                <span>{user?.email || "anonymous_node"}</span>
                                <div style={{ color: "var(--text-muted)", cursor: "pointer" }}>Edit</div>
                            </div>
                        </div>
                        <div>
                            <label className="text-muted text-xs uppercase font-bold mb-2 block">Access Level</label>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                <span className="badge-futuristic text-cyan">CLUSTER_ADMIN</span>
                                <span className="text-muted" style={{ fontSize: "10px" }}>Institutional Grade</span>
                            </div>
                        </div>
                    </div>

                    <button className="btn-cyan mt-8" style={{ background: "rgba(255,255,255,0.05)", color: "white", width: "100%", boxShadow: "none", border: "1px solid var(--glass-border)" }}>
                        Update API Key
                    </button>
                </div>

                {/* System Health Overlay */}
                <div className="glass-card" style={{ padding: "2rem" }}>
                    <SectionHeader icon={Activity} title="System Health" sub="Real-time Module Integrity" />
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
                        {[
                            { label: "Database", status: "STABLE", icon: Database },
                            { label: "API Cluster", status: "NOMINAL", icon: Server },
                            { label: "MT5 Bridge", status: status?.connected ? "ACTIVE" : "OFFLINE", icon: Terminal }
                        ].map((s, i) => (
                            <div key={i} style={{ padding: "1rem", background: "rgba(255,255,255,0.02)", border: "1px solid var(--glass-border)", borderRadius: "12px", textAlign: "center" }}>
                                <s.icon size={16} className="text-muted mb-2 mx-auto" style={{ opacity: 0.5 }} />
                                <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 800, marginBottom: "4px" }}>{s.label}</div>
                                <div style={{ fontSize: "0.8rem", color: s.status === "OFFLINE" ? "var(--danger)" : "var(--success)", fontWeight: 800 }}>{s.status}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Danger Zone */}
                <div className="glass-card delay-3" style={{ padding: "2rem", border: "1px solid rgba(255, 61, 107, 0.2)" }}>
                    <div className="flex items-center gap-4 mb-6">
                        <div style={{ padding: "10px", background: "rgba(255, 61, 107, 0.05)", border: "1px solid rgba(255, 61, 107, 0.2)", borderRadius: "8px" }}>
                            <AlertTriangle size={20} className="text-danger" />
                        </div>
                        <div>
                            <h3 className="display" style={{ fontSize: "1rem", color: "var(--danger)" }}>Entropy Zone</h3>
                            <p className="text-muted" style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Destructive System Actions</p>
                        </div>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                        <div className="flex-between">
                            <div>
                                <div className="font-bold text-white text-sm">Purge Neural Records</div>
                                <div className="text-muted text-xs">Reset all history and balance data</div>
                            </div>
                            <button className="btn-outline-danger" style={{ fontSize: "10px" }}>INITIALIZE_PURGE</button>
                        </div>

                        <div style={{ borderTop: "1px solid rgba(255, 61, 107, 0.1)", paddingTop: "1.5rem" }}>
                            <div className="text-muted text-xs mb-4">Type <span className="text-danger font-bold">DELETE</span> to confirm account termination</div>
                             <div style={{ display: "flex", gap: "1rem" }}>
                                <input
                                    className="focus-cyan"
                                    placeholder="Type DELETE to confirm"
                                    value={deleteConfirm}
                                    onChange={e => setDeleteConfirm(e.target.value)}
                                    style={{
                                        flex: 1, background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255, 61, 107, 0.3)",
                                        borderRadius: "4px", padding: "10px 14px", color: "white", fontFamily: "inherit"
                                    }}
                                />
                                <button
                                    className="btn-cyan"
                                    style={{ background: "var(--danger)", color: "white", opacity: deleteConfirm === "DELETE" ? 1 : 0.3 }}
                                    disabled={deleteConfirm !== "DELETE"}
                                >
                                    Terminate Node
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer Build Status */}
            <div className="flex-center mt-12 gap-8 opacity-30">
                <Github size={16} />
                <div style={{ fontSize: "10px", fontWeight: 800 }}>VELORA_OS_BUILD : 0xc0ffee42</div>
                <div style={{ fontSize: "10px", fontWeight: 800 }}>CORE_KERNAL : v2.4.9-Stable</div>
            </div>
        </div>
    );
}

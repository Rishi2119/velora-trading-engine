"use client";
import React, { useState } from "react";
import { X, Shield, Server, Lock, User, RefreshCw, CheckCircle2 } from "lucide-react";
import { trading } from "@/lib/api";

interface MT5ConnectModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (status: any) => void;
}

export default function MT5ConnectModal({ isOpen, onClose, onSuccess }: MT5ConnectModalProps) {
    const [account, setAccount] = useState("");
    const [password, setPassword] = useState("");
    const [server, setServer] = useState("MetaQuotes-Demo");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        
        try {
            const res = await trading.connectMT5({ account, password, server });
            if (res.connected) {
                setSuccess(true);
                setTimeout(() => {
                    onSuccess(res);
                    onClose();
                    setSuccess(false);
                }, 2000);
            } else {
                setError(res.error || "Connection failed. Please check credentials.");
            }
        } catch (err: any) {
            setError(err.message || "An unexpected error occurred.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            position: "fixed", inset: 0, zIndex: 1000,
            display: "flex", alignItems: "center", justifyContent: "center",
            padding: "20px", background: "rgba(2, 11, 24, 0.8)", backdropFilter: "blur(8px)"
        }}>
            <div className="glass-card" style={{
                width: "100%", maxWidth: "450px", padding: "2rem",
                border: "1px solid var(--glass-border)", background: "var(--bg-deep)",
                animation: "slideUpFade 0.4s ease-out forwards"
            }}>
                <div className="flex-between mb-8">
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                        <div style={{ padding: "8px", background: "rgba(0, 245, 255, 0.05)", borderRadius: "8px" }}>
                            <Shield size={20} className="text-cyan" />
                        </div>
                        <h3 className="display" style={{ fontSize: "1.1rem", color: "white" }}>Establish Terminal Link</h3>
                    </div>
                    <button onClick={onClose} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
                        <X size={20} />
                    </button>
                </div>

                {success ? (
                    <div className="flex-center" style={{ flexDirection: "column", padding: "2rem 0", gap: "1rem" }}>
                        <CheckCircle2 size={48} className="text-success" style={{ animation: "pulse 2s infinite" }} />
                        <div className="display" style={{ color: "white", fontSize: "1rem" }}>Handshake Successful</div>
                        <p className="text-muted text-center text-xs">MT5 Terminal link established. Redirecting to core nexus...</p>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit}>
                        <div className="mb-4">
                            <label className="text-muted text-[10px] uppercase font-bold mb-2 block">Account Number</label>
                            <div style={{ position: "relative" }}>
                                <User size={14} className="text-muted" style={{ position: "absolute", left: "14px", top: "14px" }} />
                                <input
                                    type="text" value={account} onChange={e => setAccount(e.target.value)}
                                    placeholder="Enter MT5 ID" required
                                    style={{
                                        width: "100%", background: "rgba(0,0,0,0.2)", border: "1px solid var(--glass-border)",
                                        borderRadius: "4px", padding: "12px 14px 12px 40px", color: "white", fontSize: "0.85rem"
                                    }}
                                />
                            </div>
                        </div>

                        <div className="mb-4">
                            <label className="text-muted text-[10px] uppercase font-bold mb-2 block">Master Password</label>
                            <div style={{ position: "relative" }}>
                                <Lock size={14} className="text-muted" style={{ position: "absolute", left: "14px", top: "14px" }} />
                                <input
                                    type="password" value={password} onChange={e => setPassword(e.target.value)}
                                    placeholder="••••••••" required
                                    style={{
                                        width: "100%", background: "rgba(0,0,0,0.2)", border: "1px solid var(--glass-border)",
                                        borderRadius: "4px", padding: "12px 14px 12px 40px", color: "white", fontSize: "0.85rem"
                                    }}
                                />
                            </div>
                        </div>

                        <div className="mb-6">
                            <label className="text-muted text-[10px] uppercase font-bold mb-2 block">Access Server</label>
                            <div style={{ position: "relative" }}>
                                <Server size={14} className="text-muted" style={{ position: "absolute", left: "14px", top: "14px" }} />
                                <input
                                    type="text" value={server} onChange={e => setServer(e.target.value)}
                                    placeholder="e.g. MetaQuotes-Demo" required
                                    style={{
                                        width: "100%", background: "rgba(0,0,0,0.2)", border: "1px solid var(--glass-border)",
                                        borderRadius: "4px", padding: "12px 14px 12px 40px", color: "white", fontSize: "0.85rem"
                                    }}
                                />
                            </div>
                        </div>

                        {error && (
                            <div style={{
                                padding: "12px", background: "rgba(255, 61, 107, 0.1)", border: "1px solid rgba(255, 61, 107, 0.2)",
                                borderRadius: "4px", color: "var(--danger)", fontSize: "11px", marginBottom: "1.5rem"
                            }}>
                                [LINK_ERROR] : {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            className="btn-cyan"
                            style={{ width: "100%", padding: "14px", display: "flex", alignItems: "center", justifyContent: "center", gap: "10px" }}
                            disabled={loading}
                        >
                            {loading ? <RefreshCw className="spin" size={16} /> : "Initialize Link"}
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}

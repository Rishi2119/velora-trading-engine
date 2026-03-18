"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { Shield, TrendingUp, Brain, Zap, RefreshCw, Lock, Mail, User } from "lucide-react";
import GoogleLoginButton from "@/components/auth/GoogleLoginButton";


export default function LoginPage() {
    const router = useRouter();
    const [tab, setTab] = useState<"login" | "register">("login");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            if (tab === "login") {
                await auth.login(email, password);
            } else {
                await auth.register(email, password, fullName);
            }
            router.replace("/dashboard");
        } catch (err: any) {
            setError(err.message || "Authentication failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="flex-center" style={{ height: "100vh", position: "relative", overflow: "hidden" }}>
            {/* Ambient Background Elements */}
            <div style={{
                position: "absolute", width: "600px", height: "600px",
                background: "radial-gradient(circle, rgba(0, 245, 255, 0.05) 0%, transparent 70%)",
                top: "-10%", left: "-10%", zIndex: 0
            }} />
            <div style={{
                position: "absolute", width: "500px", height: "500px",
                background: "radial-gradient(circle, rgba(123, 97, 255, 0.05) 0%, transparent 70%)",
                bottom: "-10%", right: "-10%", zIndex: 0
            }} />

            <div className="glass-card fade-in" style={{ padding: 0, width: "900px", display: "flex", minHeight: "600px", zIndex: 1, border: "1px solid var(--glass-border)" }}>
                {/* Visual Side */}
                <div style={{ flex: 1, background: "rgba(0,0,0,0.3)", padding: "3rem", display: "flex", flexDirection: "column", borderRight: "1px solid var(--glass-border)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "3rem" }}>
                        <div style={{ width: 32, height: 32, background: "var(--cyan)", clipPath: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <div style={{ width: 14, height: 14, background: "var(--bg-deep)", borderRadius: "50%" }} />
                        </div>
                        <span className="display" style={{ fontSize: "1.5rem", color: "white", letterSpacing: "2px" }}>VELORA</span>
                    </div>

                    <h2 className="display" style={{ fontSize: "2.2rem", lineHeight: "1.1", marginBottom: "1.5rem", color: "white" }}>
                        NEURAL <br />TRADING <br />PROTOCOL
                    </h2>

                    <p className="text-muted" style={{ fontSize: "0.9rem", maxWidth: "300px", lineHeight: "1.6", marginBottom: "3rem" }}>
                        Access the next generation of autonomous capital management. Institutional-grade reasoning with 24/7 execution parity.
                    </p>

                    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", marginTop: "auto" }}>
                        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                            <div style={{ padding: "8px", background: "rgba(0, 245, 255, 0.05)", borderRadius: "6px" }}><Zap size={14} className="text-cyan" /></div>
                            <span className="text-muted text-[10px] uppercase font-bold tracking-widest">Low Latency Signal Data</span>
                        </div>
                        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                            <div style={{ padding: "8px", background: "rgba(123, 97, 255, 0.05)", borderRadius: "6px" }}><Brain size={14} className="text-violet" /></div>
                            <span className="text-muted text-[10px] uppercase font-bold tracking-widest">Self-Correcting Reasoning</span>
                        </div>
                    </div>
                </div>

                {/* Form Side */}
                <div style={{ width: "420px", padding: "4rem", display: "flex", flexDirection: "column", justifyContent: "center" }}>

                    {/* Tab Select */}
                    <div style={{ display: "flex", background: "rgba(255,255,255,0.03)", padding: "4px", borderRadius: "8px", marginBottom: "2rem", border: "1px solid var(--glass-border)" }}>
                        <button
                            onClick={() => { setTab("login"); setError(""); }}
                            style={{
                                flex: 1, padding: "10px", borderRadius: "6px", border: "none",
                                background: tab === "login" ? "rgba(0, 245, 255, 0.1)" : "transparent",
                                color: tab === "login" ? "var(--cyan)" : "var(--text-muted)",
                                fontSize: "11px", fontWeight: 800, cursor: "pointer", transition: "all 0.3s"
                            }}
                        >SIGN_IN</button>
                        <button
                            onClick={() => { setTab("register"); setError(""); }}
                            style={{
                                flex: 1, padding: "10px", borderRadius: "6px", border: "none",
                                background: tab === "register" ? "rgba(0, 245, 255, 0.1)" : "transparent",
                                color: tab === "register" ? "var(--cyan)" : "var(--text-muted)",
                                fontSize: "11px", fontWeight: 800, cursor: "pointer", transition: "all 0.3s"
                            }}
                        >SIGN_UP</button>
                    </div>

                    <form onSubmit={handleSubmit}>
                        {tab === "register" && (
                            <div className="mb-4">
                                <label className="text-muted text-[10px] uppercase font-bold mb-2 block">Operator Name</label>
                                <div style={{ position: "relative" }}>
                                    <User size={12} className="text-muted" style={{ position: "absolute", left: "14px", top: "14px" }} />
                                    <input
                                        type="text" value={fullName} onChange={e => setFullName(e.target.value)}
                                        className="focus-cyan"
                                        placeholder="Full Name"
                                        style={{
                                            width: "100%", background: "rgba(0,0,0,0.2)", border: "1px solid var(--glass-border)",
                                            borderRadius: "4px", padding: "10px 14px 10px 40px", color: "white", fontSize: "0.85rem"
                                        }}
                                    />
                                </div>
                            </div>
                        )}

                        <div className="mb-4">
                            <label className="text-muted text-[10px] uppercase font-bold mb-2 block">Network Identity</label>
                            <div style={{ position: "relative" }}>
                                <Mail size={12} className="text-muted" style={{ position: "absolute", left: "14px", top: "14px" }} />
                                <input
                                    type="email" value={email} onChange={e => setEmail(e.target.value)}
                                    className="focus-cyan"
                                    placeholder="Enter your email"
                                    required
                                    style={{
                                        width: "100%", background: "rgba(0,0,0,0.2)", border: "1px solid var(--glass-border)",
                                        borderRadius: "4px", padding: "10px 14px 10px 40px", color: "white", fontSize: "0.85rem"
                                    }}
                                />
                            </div>
                        </div>

                        <div className="mb-6">
                            <label className="text-muted text-[10px] uppercase font-bold mb-2 block">Security Token</label>
                            <div style={{ position: "relative" }}>
                                <Lock size={12} className="text-muted" style={{ position: "absolute", left: "14px", top: "14px" }} />
                                <input
                                    type="password" value={password} onChange={e => setPassword(e.target.value)}
                                    className="focus-cyan"
                                    placeholder="••••••••"
                                    required
                                    style={{
                                        width: "100%", background: "rgba(0,0,0,0.2)", border: "1px solid var(--glass-border)",
                                        borderRadius: "4px", padding: "10px 14px 10px 40px", color: "white", fontSize: "0.85rem"
                                    }}
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="fade-in" style={{
                                padding: "10px", background: "rgba(255, 61, 107, 0.1)", border: "1px solid rgba(255, 61, 107, 0.3)",
                                borderRadius: "4px", color: "var(--danger)", fontSize: "10px", marginBottom: "1.5rem"
                            }}>
                                [AUTH_ERROR] : {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            className="btn-cyan"
                            style={{ width: "100%", padding: "14px" }}
                            disabled={loading}
                        >
                            {loading ? <RefreshCw className="spin" size={16} /> : tab === "login" ? "SIGN_IN" : "CREATE_ACCOUNT"}
                        </button>
                    </form>

                    <div style={{ marginTop: "1rem", textAlign: "center" }}>
                        <button 
                            onClick={() => setTab(tab === "login" ? "register" : "login")}
                            style={{ background: "none", border: "none", color: "var(--cyan)", fontSize: "11px", cursor: "pointer", opacity: 0.8 }}
                        >
                            {tab === "login" ? "New here? Create account" : "Already have an account? Sign in"}
                        </button>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "10px", margin: "1.5rem 0" }}>
                        <div style={{ flex: 1, height: "1px", background: "var(--glass-border)" }} />
                        <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>OR</span>
                        <div style={{ flex: 1, height: "1px", background: "var(--glass-border)" }} />
                    </div>

                    <GoogleLoginButton />

                    <div style={{ marginTop: "2rem", textAlign: "center", fontSize: "10px", color: "var(--text-muted)", letterSpacing: "1px" }}>
                        ENCRYPTED P2P HANDSHAKE ACTIVE
                    </div>
                </div>
            </div>



            <style jsx>{`
                .focus-cyan:focus {
                    outline: none;
                    border-color: var(--cyan) !important;
                    box-shadow: 0 0 10px var(--cyan-glow);
                }
            `}</style>
        </div>
    );
}

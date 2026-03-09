"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { Shield, TrendingUp, Brain, Zap } from "lucide-react";

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
        <div style={{ display: "flex", height: "100vh", background: "var(--bg-base)" }}>
            {/* Left panel — branding */}
            <div style={{
                flex: 1, display: "flex", flexDirection: "column", justifyContent: "center",
                padding: "60px", background: "var(--bg-surface)", borderRight: "1px solid var(--border)"
            }}>
                <div style={{ marginBottom: 40 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                        <Shield size={32} color="#6366f1" />
                        <span style={{ fontSize: "2rem", fontWeight: 800, background: "var(--gradient-brand)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Velora</span>
                    </div>
                    <p style={{ color: "var(--text-secondary)", fontSize: "1rem" }}>AI-Powered Trading Platform</p>
                </div>

                <h1 style={{ marginBottom: 12 }}>Institutional-grade<br />trading, simplified.</h1>
                <p style={{ color: "var(--text-secondary)", maxWidth: 420, marginBottom: 40, lineHeight: 1.8 }}>
                    Connect your MT5 account, deploy AI strategies, and monitor real-time performance — all from one unified dashboard.
                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                    {[
                        { icon: Brain, title: "Autonomous AI Agent", desc: "NVIDIA-powered reasoning engine making 24/7 trading decisions" },
                        { icon: TrendingUp, title: "MT5 Integration", desc: "Direct connection to MetaTrader 5 for live trade execution" },
                        { icon: Zap, title: "Strategy Engine", desc: "Volatility breakout, London session, mean reversion & more" },
                    ].map(({ icon: Icon, title, desc }) => (
                        <div key={title} style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                            <div style={{ padding: 8, background: "rgba(99,102,241,0.12)", borderRadius: 8, flexShrink: 0 }}>
                                <Icon size={18} color="#6366f1" />
                            </div>
                            <div>
                                <div style={{ fontWeight: 600, marginBottom: 2 }}>{title}</div>
                                <div style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>{desc}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right panel — form */}
            <div style={{ width: 480, display: "flex", alignItems: "center", justifyContent: "center", padding: 40 }}>
                <div style={{ width: "100%", maxWidth: 380 }}>
                    {/* Tabs */}
                    <div style={{ display: "flex", gap: 2, background: "var(--bg-card)", borderRadius: 10, padding: 4, marginBottom: 28, border: "1px solid var(--border)" }}>
                        {(["login", "register"] as const).map(t => (
                            <button
                                key={t}
                                onClick={() => setTab(t)}
                                className="btn"
                                style={{
                                    flex: 1, padding: "8px 0", fontSize: "0.85rem",
                                    background: tab === t ? "var(--gradient-brand)" : "transparent",
                                    color: tab === t ? "#fff" : "var(--text-secondary)",
                                    boxShadow: "none", borderRadius: 7,
                                }}
                            >
                                {t === "login" ? "Sign In" : "Create Account"}
                            </button>
                        ))}
                    </div>

                    <h2 style={{ marginBottom: 6 }}>{tab === "login" ? "Welcome back" : "Get started"}</h2>
                    <p className="text-muted text-sm mb-4">{tab === "login" ? "Sign in to your Velora account" : "Create your free trading account"}</p>

                    <form onSubmit={handleSubmit}>
                        {tab === "register" && (
                            <div className="form-group">
                                <label className="form-label">Full Name</label>
                                <input className="form-input" type="text" placeholder="John Doe" value={fullName} onChange={e => setFullName(e.target.value)} />
                            </div>
                        )}
                        <div className="form-group">
                            <label className="form-label">Email</label>
                            <input className="form-input" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Password</label>
                            <input className="form-input" type="password" placeholder={tab === "register" ? "At least 6 characters" : "Your password"} value={password} onChange={e => setPassword(e.target.value)} required />
                        </div>

                        {error && (
                            <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: "10px 14px", color: "var(--red)", fontSize: "0.85rem", marginBottom: 16 }}>
                                {error}
                            </div>
                        )}

                        <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
                            {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : null}
                            {tab === "login" ? "Sign In" : "Create Account"}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}

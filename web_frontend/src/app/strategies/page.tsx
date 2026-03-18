"use client";
import { useEffect, useState, useCallback } from "react";
import {
    Settings, Save, RotateCcw, Shield,
    Filter, Zap, Target, RefreshCw
} from "lucide-react";
import { trading, ai } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StrategySettings() {
    const [config, setConfig] = useState<any>(null);
    const [filters, setFilters] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [optimizing, setOptimizing] = useState(false);
    const [form, setForm] = useState<any>({});

    const token = () => typeof window !== "undefined" ? localStorage.getItem("velora_token") || "" : "";

    const fetchData = useCallback(async () => {
        try {
            const [cfgRes, fltRes] = await Promise.allSettled([
                fetch(`${API}/api/v1/strategy/config`, { headers: { Authorization: `Bearer ${token()}` } }).then(r => r.json()),
                trading.mt5Status(),
            ]);

            if (cfgRes.status === "fulfilled") {
                const c = cfgRes.value.config || cfgRes.value || {};
                setConfig(c);
                setForm(c);
            }
            if (fltRes.status === "fulfilled") setFilters(fltRes.value);
        } catch (err) {
            console.error("Strategy fetch error:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const t = setInterval(fetchData, 5000);
        return () => clearInterval(t);
    }, [fetchData]);

    const handleSave = async () => {
        setSaving(true);
        try {
            await fetch(`${API}/api/v1/strategy/config`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token()}` },
                body: JSON.stringify(form),
            });
            await fetchData();
            alert("Configuration saved successfully!");
        } catch (err) {
            console.error("Save config error:", err);
            alert("Failed to save configuration.");
        } finally {
            setSaving(false);
        }
    };

    const handleOptimize = async () => {
        setOptimizing(true);
        try {
            await fetch(`${API}/api/v1/ai/optimize`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token()}` },
                body: JSON.stringify({ strategy: "Velora_Trend_v2" })
            });
            alert("AI Optimization cycle started in background.");
        } catch (err) {
            console.error("Optimize error:", err);
            alert("Failed to start AI optimization.");
        } finally {
            setOptimizing(false);
        }
    };

    const InputField = ({ label, value, onChange, type = "number", sub }: any) => (
        <div className="mb-5">
            <label className="text-muted text-xs uppercase font-bold mb-2 block" style={{ letterSpacing: "0.1em" }}>{label}</label>
            <input
                type={type}
                value={value ?? ""}
                placeholder={`e.g. ${type === "number" ? "1.0" : "EURUSD"}`}
                onChange={e => onChange(type === "number" ? parseFloat(e.target.value) : e.target.value)}
                style={{
                    width: "100%", background: "rgba(0,0,0,0.3)", border: "1px solid var(--glass-border)",
                    borderBottomWidth: "2px",
                    borderRadius: "4px", padding: "12px 14px", color: "white", fontFamily: "inherit",
                    transition: "all 0.2s"
                }}
                className="focus-cyan"
            />
            {sub && <div className="text-muted" style={{ fontSize: "10px", marginTop: "4px" }}>{sub}</div>}
        </div>
    );

    const PillToggle = ({ label, active, onToggle }: any) => (
        <div className="flex-between p-3" style={{ background: "rgba(255,255,255,0.02)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.05)" }}>
            <span className="text-xs uppercase font-bold text-main">{label}</span>
            <button
                onClick={onToggle}
                style={{
                    width: "48px", height: "24px", borderRadius: "100px",
                    background: active ? "var(--cyan)" : "rgba(255,255,255,0.1)",
                    border: "none", cursor: "pointer", position: "relative",
                    transition: "all 0.3s", boxShadow: active ? "0 0 10px var(--cyan)" : "none"
                }}
            >
                <div style={{
                    position: "absolute", top: "4px", left: active ? "28px" : "4px",
                    width: "16px", height: "16px", borderRadius: "50%", background: active ? "var(--bg-deep)" : "white",
                    transition: "all 0.3s"
                }} />
            </button>
        </div>
    );

    if (loading && !config) {
        return (
            <div className="flex-center" style={{ height: "60vh" }}>
                <RefreshCw size={32} className="text-cyan pulse" />
            </div>
        );
    }

    return (
        <div className="fade-in">
            {/* Header Section */}
            <header className="flex-between mb-8">
                <div>
                    <h1 style={{ fontSize: "1.8rem" }}>Strategy Configuration</h1>
                    <div className="flex items-center gap-2 mt-2">
                        <span className="badge-futuristic text-success">Hot-Reload Active</span>
                        <span className="text-muted text-xs uppercase">Engine Syncing v2.4.0</span>
                    </div>
                </div>
                <div style={{ display: "flex", gap: "1rem" }}>
                    <button className="btn-cyan" style={{ background: "var(--violet)", boxShadow: "0 0 15px var(--violet-glow)" }} onClick={handleOptimize} disabled={optimizing}>
                        <Zap size={14} className="mr-2" /> {optimizing ? "OPTIMIZING..." : "AI OPTIMIZE"}
                    </button>
                    <button className="btn-cyan" onClick={handleSave} disabled={saving}>
                        <Save size={14} className="mr-2" /> {saving ? "SAVING..." : "SAVE CONFIG"}
                    </button>
                </div>
            </header>

            {/* Strategy Health Score */}
            <div className="glass-card mb-8" style={{ padding: "1.5rem", background: "linear-gradient(90deg, rgba(0, 245, 255, 0.05) 0%, transparent 100%)", borderLeft: "4px solid var(--success)" }}>
                <div className="flex-between">
                    <div>
                        <div className="display" style={{ fontSize: "0.85rem", color: "var(--success)" }}>Strategy Health Score</div>
                        <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "white", marginTop: "4px" }}>87/100 — <span className="text-success">Configuration Optimized</span></div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                        <div className="text-muted text-xs uppercase mb-1">Risk Profile</div>
                        <div className="badge-futuristic text-cyan">INSTITUTIONAL</div>
                    </div>
                </div>
            </div>

            {/* Config Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1.5rem", marginBottom: "2rem" }}>

                {/* Risk Management */}
                <div className="glass-card delay-1" style={{ padding: "1.5rem" }}>
                    <div className="display mb-6" style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "10px" }}>
                        <Shield size={16} className="text-cyan" />
                        Risk Parameters
                    </div>
                    <InputField label="Risk per Trade (%)" value={form.risk_per_trade_pct} onChange={(v: any) => setForm({ ...form, risk_per_trade_pct: v })} sub="Percentage of equity risked per order" />
                    <InputField label="Min Risk:Reward" value={form.min_rr} onChange={(v: any) => setForm({ ...form, min_rr: v })} sub="Minimum allowed R:R ratio for signals" />
                    <InputField label="Circuit Breaker" value={form.circuit_breaker_pct} onChange={(v: any) => setForm({ ...form, circuit_breaker_pct: v })} sub="Auto-halt trading at % daily drawdown" />
                </div>

                {/* Indicators */}
                <div className="glass-card delay-2" style={{ padding: "1.5rem" }}>
                    <div className="display mb-6" style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "10px" }}>
                        <Settings size={16} className="text-violet" />
                        Neural Indicators
                    </div>
                    <InputField label="EMA Fast / Slow" value={form.ema_fast} onChange={(v: any) => setForm({ ...form, ema_fast: v })} sub="Smoothing periods for trend bias" />
                    <InputField label="RSI Threshold" value={form.rsi_period} onChange={(v: any) => setForm({ ...form, rsi_period: v })} sub="Momentum period for oscillator logic" />
                    <InputField label="Max Spread (pips)" value={form.max_spread_pips} onChange={(v: any) => setForm({ ...form, max_spread_pips: v })} sub="Reject trades above this spread" />
                </div>

                {/* Filters */}
                <div className="glass-card delay-3" style={{ padding: "1.5rem" }}>
                    <div className="display mb-6" style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "10px" }}>
                        <Filter size={16} className="text-warning" />
                        Execution Filters
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
                        <PillToggle label="Session Filter" active={form.enable_session_filter} onToggle={() => setForm({ ...form, enable_session_filter: !form.enable_session_filter })} />
                        <PillToggle label="News Filter" active={form.enable_news_filter} onToggle={() => setForm({ ...form, enable_news_filter: !form.enable_news_filter })} />
                        <PillToggle label="Spread Check" active={form.enable_spread_filter} onToggle={() => setForm({ ...form, enable_spread_filter: !form.enable_spread_filter })} />
                    </div>
                    <InputField label="Trading Pairs" type="text" value={form.pairs} onChange={(v: any) => setForm({ ...form, pairs: v })} sub="Comma separated (e.g. EURUSD,XAUUSD)" />
                </div>
            </div>

            {/* Live Filter Status Panel */}
            <div className="glass-card delay-4" style={{ padding: "1.5rem" }}>
                <div className="display mb-6" style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "10px" }}>
                    <Target size={16} className="text-cyan" />
                    Live Filter Environment
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
                    {[
                        { 
                            label: "Market Session", 
                            status: filters?.session?.is_open ? "success" : "warning", 
                            text: filters?.session?.is_open ? "ACTIVE" : "CLOSED", 
                            meta: filters?.session?.is_open ? `Current: ${filters?.session?.session}` : "Next: London Open in 4h 23m" 
                        },
                        { label: "Macro Event Shield", status: "success", text: filters?.news?.blocked ? "SHIELD ACTIVE" : "CLEAR", meta: "Low Impact State" },
                        { label: "Circuit Integrity", status: "success", text: filters?.kill_switch?.active ? "HALTED" : "STABLE", meta: "Manual Override OK" }
                    ].map((s, i) => (
                        <div key={i} style={{ padding: "1.25rem", background: "rgba(255,255,255,0.02)", border: "1px solid var(--glass-border)", borderRadius: "8px" }}>
                            <div className="flex-between mb-2">
                                <span className="text-muted text-xs uppercase font-bold">{s.label}</span>
                                <div style={{
                                    width: 8, height: 8, borderRadius: "50%",
                                    background: `var(--${s.status})`,
                                    boxShadow: `0 0 10px var(--${s.status})`
                                }} />
                            </div>

                            <div className="display" style={{ fontSize: "1rem", color: "white" }}>{s.text}</div>
                            <div className="text-muted" style={{ fontSize: "10px", marginTop: "4px" }}>{s.meta}</div>
                        </div>
                    ))}
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

"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { trading } from "@/lib/api";
import { Zap, Play, Square, Settings2, ShieldCheck, Activity } from "lucide-react";

export default function StrategiesPage() {
    const [strats, setStrats] = useState<Record<string, boolean>>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        async function load() {
            try {
                const res = await trading.strategies();
                setStrats(res);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    const toggle = (name: string) => {
        setStrats(prev => ({ ...prev, [name]: !prev[name] }));
    };

    const save = async () => {
        setSaving(true);
        try {
            await trading.updateStrategies(strats);
        } catch (e) {
            console.error(e);
        } finally {
            setSaving(false);
        }
    };

    const strategyConfig = [
        { id: "volatility_breakout", name: "Volatility Breakout", desc: "Capitalizes on sudden spikes in market volatility using ATR channels.", icon: Activity },
        { id: "london_session", name: "London Session Momentum", desc: "Executes trades based on the opening volume of the London market session.", icon: Zap },
        { id: "mean_reversion", name: "Mean Reversion", desc: "Fades extreme price movements anticipating a return to the moving average.", icon: ShieldCheck },
        { id: "ai_prediction", name: "NVIDIA NIM Predictive", desc: "Uses the deep learning AI agent to predict next-candle directional bias.", icon: Zap },
    ];

    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    <div className="flex items-center gap-3 mb-6" style={{ justifyContent: "space-between" }}>
                        <div>
                            <h1 className="flex items-center gap-2"><Settings2 size={28} color="var(--brand-primary)" /> Strategy Configuration</h1>
                            <p className="text-muted text-sm mt-1">Enable or disable specific algorithmic trading strategies.</p>
                        </div>
                        <button className="btn btn-primary" onClick={save} disabled={loading || saving}>
                            {saving ? <span className="spinner" style={{ width: 14, height: 14 }} /> : "Save Changes"}
                        </button>
                    </div>

                    <div className="grid-2">
                        {loading ? (
                            <div className="col-span-2 flex-center py-12"><div className="spinner"></div></div>
                        ) : (
                            strategyConfig.map(s => {
                                const isActive = strats[s.id] ?? false;
                                return (
                                    <div key={s.id} className="card flex items-start gap-4">
                                        <div style={{ padding: 12, background: isActive ? "rgba(99,102,241,0.15)" : "var(--bg-elevated)", borderRadius: 12 }}>
                                            <s.icon size={24} color={isActive ? "var(--brand-primary)" : "var(--text-secondary)"} />
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center justify-between mb-2">
                                                <h3 className="font-semibold">{s.name}</h3>
                                                <label className="toggle">
                                                    <input type="checkbox" checked={isActive} onChange={() => toggle(s.id)} />
                                                    <span className="toggle-slider"></span>
                                                </label>
                                            </div>
                                            <p className="text-muted text-sm leading-relaxed">{s.desc}</p>
                                            <div className="mt-4 flex gap-2">
                                                {isActive ? (
                                                    <span className="badge badge-green"><Play size={10} style={{ marginRight: 4 }} /> ACTIVE</span>
                                                ) : (
                                                    <span className="badge badge-yellow"><Square size={10} style={{ marginRight: 4 }} /> INACTIVE</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

"use client";
import Sidebar from "@/components/Sidebar";
import { Copy, Link2, GitMerge } from "lucide-react";

export default function CopyTradingPage() {
    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    <div className="flex items-center gap-3 mb-6" style={{ justifyContent: "space-between" }}>
                        <div>
                            <h1>Copy Trading Engine</h1>
                            <p className="text-muted text-sm">Pub-Sub signal broadcasting across linked vaults</p>
                        </div>
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <div className="flex items-center gap-2 mb-4">
                                <Link2 size={16} color="var(--brand-primary)" />
                                <h3>Active Followers</h3>
                            </div>
                            <p className="text-muted text-sm mb-4">
                                The engine is running with the <b>CopyBroadcaster</b> pushing signals to the
                                memory bus. Registered followers sync within a 30s staleness window.
                            </p>
                            <div style={{ background: "var(--bg-elevated)", padding: 12, borderRadius: 8, border: "1px solid var(--border)" }}>
                                <div className="stat-label mb-2">Internal Pub-Sub Bus</div>
                                <div className="flex items-center gap-2">
                                    <span className="badge badge-green">LIVE</span>
                                    <span className="text-xs font-mono text-muted">CopyFollower Active</span>
                                </div>
                            </div>
                        </div>

                        <div className="card">
                            <div className="flex items-center gap-2 mb-4">
                                <GitMerge size={16} color="var(--brand-primary)" />
                                <h3>Follower Rules</h3>
                            </div>
                            <div className="flex flex-col gap-3">
                                <div className="form-group mb-0">
                                    <label className="form-label">Max Staleness (seconds)</label>
                                    <input type="number" className="form-input" defaultValue={30} disabled />
                                </div>
                                <div className="form-group mb-0">
                                    <label className="form-label">Confidence Override</label>
                                    <input type="number" className="form-input" defaultValue={100} disabled />
                                    <p className="text-xs text-muted mt-1">Copied signals force 100% confidence to bypass AI thresholds.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

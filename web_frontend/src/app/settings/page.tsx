"use client";
import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { trading, auth } from "@/lib/api";
import { Settings, Save, AlertTriangle } from "lucide-react";

export default function SettingsPage() {
    const [user, setUser] = useState<any>(null);
    const [mt5Acc, setMt5Acc] = useState("");
    const [mt5Pass, setMt5Pass] = useState("");
    const [mt5Server, setMt5Server] = useState("");
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [status, setStatus] = useState<any>(null);

    useEffect(() => {
        setUser(auth.getUser());
        trading.mt5Status().then(res => setStatus(res)).catch(console.error);
    }, []);

    const handleConnect = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setSuccess(false);
        try {
            await trading.connectMT5({ account: mt5Acc, password: mt5Pass, server: mt5Server });
            setSuccess(true);
            setStatus({ connected: true });
        } catch (e) {
            console.error(e);
            alert("Failed to connect to MT5. Check credentials.");
        } finally {
            setLoading(false);
        }
    };

    const handleDisconnect = async () => {
        setLoading(true);
        try {
            await trading.disconnectMT5();
            setStatus({ connected: false });
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    <div className="mb-6">
                        <h1 className="flex items-center gap-2"><Settings size={28} color="var(--brand-primary)" /> Settings</h1>
                        <p className="text-muted text-sm mt-1">Configure your account and broker connections.</p>
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <h3 className="mb-4">MetaTrader 5 Integration</h3>
                            {status?.connected ? (
                                <div className="mb-4 p-4 rounded-md" style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)" }}>
                                    <div className="font-bold text-green mb-1">MT5 Terminal Connected</div>
                                    <p className="text-sm text-green opacity-80 mb-4">You are currently connected to the broker terminal and ready to execute live trades.</p>
                                    <button className="btn btn-danger" onClick={handleDisconnect} disabled={loading}>Disconnect MT5</button>
                                </div>
                            ) : (
                                <form onSubmit={handleConnect}>
                                    <div className="form-group">
                                        <label className="form-label">Account Number (Login)</label>
                                        <input className="form-input" type="text" value={mt5Acc} onChange={e => setMt5Acc(e.target.value)} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Password</label>
                                        <input className="form-input" type="password" value={mt5Pass} onChange={e => setMt5Pass(e.target.value)} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Broker Server Name</label>
                                        <input className="form-input" type="text" placeholder="e.g. MetaQuotes-Demo" value={mt5Server} onChange={e => setMt5Server(e.target.value)} required />
                                    </div>
                                    <button className="btn btn-primary" type="submit" disabled={loading}>
                                        {loading ? <span className="spinner" style={{ width: 14, height: 14 }} /> : <><Save size={14} /> Connect Terminal</>}
                                    </button>
                                    {success && <div className="text-green text-sm mt-3">Connection successful!</div>}
                                </form>
                            )}
                        </div>

                        <div className="card">
                            <h3 className="mb-4">Account Profile</h3>
                            <div className="form-group">
                                <label className="form-label">Email Address</label>
                                <input className="form-input" type="email" value={user?.email || ""} readOnly disabled />
                            </div>
                            <div className="form-group">
                                <label className="form-label">ID</label>
                                <input className="form-input" type="text" value={user?.id || ""} readOnly disabled />
                            </div>

                            <div className="mt-8 pt-6 border-t border-[var(--border)]">
                                <h4 className="text-red mb-2 flex items-center gap-2"><AlertTriangle size={16} /> Danger Zone</h4>
                                <p className="text-muted text-sm mb-4">Permanently delete your account and all associated trading data.</p>
                                <button className="btn btn-danger">Delete Account</button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

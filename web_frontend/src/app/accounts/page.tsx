"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { Users, Plus, Trash2, Key } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AccountsPage() {
    const [accounts, setAccounts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ login: "", password: "", server: "", broker: "MetaQuotes" });

    const fetchAccounts = async () => {
        try {
            const res = await fetch(`${API}/api/v1/accounts`);
            const data = await res.json();
            setAccounts(data.accounts || []);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchAccounts(); }, []);

    const handleAdd = async (e: any) => {
        e.preventDefault();
        await fetch(`${API}/api/v1/accounts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                login: Number(form.login),
                password: form.password,
                server: form.server,
                broker: form.broker
            })
        });
        setForm({ login: "", password: "", server: "", broker: "MetaQuotes" });
        fetchAccounts();
    };

    const handleDelete = async (id: number) => {
        await fetch(`${API}/api/v1/accounts/${id}`, { method: "DELETE" });
        fetchAccounts();
    };

    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    <div className="flex items-center gap-3 mb-6" style={{ justifyContent: "space-between" }}>
                        <div>
                            <h1>Multi-Account Manager</h1>
                            <p className="text-muted text-sm">Secure MT5 credential storage with AES-256 Fernet encryption</p>
                        </div>
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <h3 className="mb-4">Add Account</h3>
                            <form onSubmit={handleAdd} className="flex flex-col gap-4">
                                <input required placeholder="MT5 Login ID (e.g. 1029384)" type="number" className="form-input" value={form.login} onChange={e => setForm({ ...form, login: e.target.value })} />
                                <input required placeholder="Password" type="password" className="form-input" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
                                <input required placeholder="Server (e.g. MetaQuotes-Demo)" className="form-input" value={form.server} onChange={e => setForm({ ...form, server: e.target.value })} />
                                <input required placeholder="Broker Name" className="form-input" value={form.broker} onChange={e => setForm({ ...form, broker: e.target.value })} />
                                <button type="submit" className="btn btn-primary" style={{ justifyContent: "center" }}>
                                    <Plus size={16} /> Add MT5 Vault
                                </button>
                            </form>
                        </div>

                        <div className="card">
                            <div className="flex items-center gap-2 mb-4" style={{ justifyContent: "space-between" }}>
                                <h3>Secured Vaults</h3>
                                <span className="badge badge-purple"><Key size={10} style={{ marginRight: 4 }} />Encrypted</span>
                            </div>
                            {loading ? <p className="text-muted">Loading...</p> : (
                                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                                    {accounts.length === 0 && <p className="text-sm text-muted">No accounts added yet.</p>}
                                    {accounts.map(acc => (
                                        <div key={acc.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--bg-elevated)", padding: 12, borderRadius: 8, border: "1px solid var(--border)" }}>
                                            <div>
                                                <div className="font-bold">{acc.broker} - {acc.login}</div>
                                                <div className="text-xs text-muted">Server: {acc.server}</div>
                                            </div>
                                            <button className="btn btn-danger btn-sm" onClick={() => handleDelete(acc.id)}>
                                                <Trash2 size={12} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

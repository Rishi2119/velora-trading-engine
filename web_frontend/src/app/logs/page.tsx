"use client";
import Sidebar from "@/components/Sidebar";
import { FileText, Download } from "lucide-react";

export default function LogsPage() {
    return (
        <div className="layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-content">
                    <div className="flex items-center gap-3 mb-6" style={{ justifyContent: "space-between" }}>
                        <div>
                            <h1 className="flex items-center gap-2"><FileText size={28} color="var(--brand-primary)" /> System Logs</h1>
                            <p className="text-muted text-sm mt-1">View streaming application logs from the backend.</p>
                        </div>
                        <button className="btn btn-secondary"><Download size={14} /> Export Logs</button>
                    </div>

                    <div className="card h-[70vh] flex flex-col items-center justify-center text-center">
                        <FileText size={48} color="var(--text-secondary)" className="mb-4 opacity-50" />
                        <h3 className="mb-2">Log Viewer (Coming Soon)</h3>
                        <p className="text-muted max-w-md">
                            Direct WebSocket streaming of `backend.log` and `flask.log` will be available in the next iteration.
                            Currently, logs can be viewed on the server console or in the `logs/` directory.
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}

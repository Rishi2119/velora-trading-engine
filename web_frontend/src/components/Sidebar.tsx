"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { auth } from "@/lib/api";
import {
    LayoutDashboard, TrendingUp, BarChart3, Brain,
    Settings, FileText, LogOut, Zap, Shield
} from "lucide-react";

const NAV_ITEMS = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/trading", label: "Trading", icon: TrendingUp },
    { href: "/analytics", label: "Analytics", icon: BarChart3 },
    { href: "/strategies", label: "Strategies", icon: Zap },
    { href: "/ai", label: "AI Agent", icon: Brain },
    { href: "/logs", label: "Logs", icon: FileText },
    { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
    const path = usePathname();

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="nav-logo">
                <Shield size={22} color="#6366f1" />
                <span className="nav-logo-text">Velora</span>
            </div>

            {/* Main nav */}
            <div className="nav-section">Navigation</div>
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
                <Link
                    key={href}
                    href={href}
                    className={`nav-item${path === href || path.startsWith(href + "/") ? " active" : ""}`}
                >
                    <Icon size={16} />
                    {label}
                </Link>
            ))}

            {/* Spacer */}
            <div style={{ flex: 1 }} />

            {/* Logout */}
            <div style={{ padding: "0 12px 12px" }}>
                <button
                    className="nav-item"
                    onClick={() => auth.logout()}
                    style={{ width: "100%", borderRadius: 8, color: "var(--red)" }}
                >
                    <LogOut size={16} />
                    Logout
                </button>
            </div>
        </aside>
    );
}

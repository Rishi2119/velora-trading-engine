/**
 * Velora Trading Platform — API Client
 * Typed wrappers around all backend endpoints with automatic JWT injection.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const MOBILE_API_BASE = process.env.NEXT_PUBLIC_MOBILE_API_URL || "http://localhost:5050";

// ── Auth helpers ──────────────────────────────────────────────────────────────

function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("velora_token");
}

function setToken(token: string) {
    localStorage.setItem("velora_token", token);
}

function clearToken() {
    localStorage.removeItem("velora_token");
    localStorage.removeItem("velora_user");
}

function authHeaders(): Record<string, string> {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Generic fetch ─────────────────────────────────────────────────────────────

async function request<T>(
    url: string,
    options: RequestInit = {}
): Promise<T> {
    const res = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...authHeaders(),
            ...(options.headers as Record<string, string>),
        },
        ...options,
    });

    if (res.status === 401) {
        clearToken();
        if (typeof window !== "undefined") window.location.href = "/login";
        throw new Error("Unauthorized");
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(data?.detail || data?.error || `HTTP ${res.status}`);
    }
    return data as T;
}

// ── Auth API ──────────────────────────────────────────────────────────────────

export const auth = {
    async login(email: string, password: string) {
        const data = await request<{ access_token: string; user_id: number; email: string }>(
            `${API_BASE}/auth/login`,
            { method: "POST", body: JSON.stringify({ email, password }) }
        );
        setToken(data.access_token);
        localStorage.setItem("velora_user", JSON.stringify({ id: data.user_id, email: data.email }));
        return data;
    },

    async register(email: string, password: string, fullName: string) {
        const data = await request<{ access_token: string; user_id: number; email: string }>(
            `${API_BASE}/auth/register`,
            { method: "POST", body: JSON.stringify({ email, password, full_name: fullName }) }
        );
        setToken(data.access_token);
        localStorage.setItem("velora_user", JSON.stringify({ id: data.user_id, email: data.email }));
        return data;
    },

    async me() {
        return request<{ id: number; email: string; full_name: string; is_admin: boolean }>(
            `${API_BASE}/auth/me`
        );
    },

    logout() {
        clearToken();
        window.location.href = "/login";
    },

    isLoggedIn() {
        return !!getToken();
    },

    getUser() {
        if (typeof window === "undefined") return null;
        const u = localStorage.getItem("velora_user");
        return u ? JSON.parse(u) : null;
    },
};

// ── Trading API ───────────────────────────────────────────────────────────────

export interface TradeStats {
    account_balance: number;
    equity: number;
    open_pnl: number;
    currency: string;
    total_pnl: number;
    win_rate: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    open_trades_count: number;
    avg_rr: number;
    max_drawdown: number;
    profit_factor: number;
    kill_switch_active: boolean;
    mt5_connected: boolean;
    server_time: string;
    demo_mode?: boolean;
}

export interface Trade {
    trade_id: string;
    timestamp: string;
    symbol: string;
    strategy: string;
    direction: string;
    entry: number;
    stop_loss: number;
    take_profit: number;
    lots: number;
    pnl: number;
    status: string;
    rr_ratio: number;
}

export const trading = {
    stats: () => request<TradeStats>(`${API_BASE}/trading/stats`),
    openPositions: () => request<{ trades: Trade[]; count: number; live: boolean }>(`${API_BASE}/trading/open-positions`),
    history: (days = 30) => request<{ trades: Trade[]; count: number }>(`${API_BASE}/trading/history?days=${days}`),
    performance: (days = 30) => request<any>(`${API_BASE}/trading/performance?days=${days}`),
    strategies: () => request<Record<string, boolean>>(`${API_BASE}/trading/strategies`),
    updateStrategies: (body: Record<string, boolean>) =>
        request(`${API_BASE}/trading/strategies`, { method: "PUT", body: JSON.stringify(body) }),
    mt5Status: () => request<any>(`${API_BASE}/trading/mt5/status`),
    connectMT5: (body: { account: string; password: string; server: string }) =>
        request<{ connected: boolean; error?: string }>(`${API_BASE}/trading/mt5/connect`, { method: "POST", body: JSON.stringify(body) }),
    disconnectMT5: () => request(`${API_BASE}/trading/mt5/disconnect`, { method: "POST" }),
    killSwitch: () => request<{ active: boolean }>(`${API_BASE}/trading/kill-switch`),
    activateKillSwitch: () => request(`${API_BASE}/trading/kill-switch/activate`, { method: "POST" }),
    deactivateKillSwitch: () => request(`${API_BASE}/trading/kill-switch`, { method: "DELETE" }),
};

// ── Analytics API ─────────────────────────────────────────────────────────────

export const analytics = {
    performance: (days = 30) => request<any>(`${API_BASE}/analytics/performance?days=${days}`),
    equityCurve: (days = 30) => request<{ curve: any[] }>(`${API_BASE}/analytics/equity-curve?days=${days}`),
};

// ── AI Agent API ──────────────────────────────────────────────────────────────

export interface AgentStatus {
    is_running: boolean;
    latest_thought: string;
    latest_decision: string;
    confidence: number;
    uptime_seconds: number;
    crash_count: number;
    demo_mode?: boolean;
}

export const ai = {
    status: () => request<AgentStatus>(`${API_BASE}/ai/status`),
    thoughts: () => request<AgentStatus>(`${API_BASE}/ai/thoughts`),
    start: () => request(`${API_BASE}/ai/start`, { method: "POST" }),
    stop: () => request(`${API_BASE}/ai/stop`, { method: "POST" }),
    enableTrading: (enabled: boolean) =>
        request(`${API_BASE}/ai/enable-trading`, { method: "POST", body: JSON.stringify({ enabled }) }),
};

// ── Market API ────────────────────────────────────────────────────────────────

export interface PriceTick {
    symbol: string;
    bid: number;
    ask: number;
    spread: number;
    timestamp: string;
}

export const market = {
    prices: () => request<{ prices: PriceTick[]; timestamp: string }>(`${API_BASE}/market/prices`),
    wsUrl: () => {
        const urlStr = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
        const wsBase = urlStr.replace("http://", "ws://").replace("https://", "wss://");
        
        // If url already contains /api/v1, don't append it again
        if (wsBase.endsWith("/api/v1")) {
            return `${wsBase}/market/stream`;
        }
        return `${wsBase}/api/v1/market/stream`;
    },
};

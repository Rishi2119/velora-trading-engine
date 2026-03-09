// API client for the Trading Engine Flask API
//
// For physical device testing, change PC_IP to your computer's local IP address.
// Find it with: ipconfig (Windows). Look for IPv4 Address.
// Example: const PC_IP = "192.168.1.100";
// For browser / web testing, 127.0.0.1 works fine.
//
const PC_IP = "127.0.0.1";
const API_BASE = `http://${PC_IP}:5050/api`;
const API_TOKEN = "b6687ce673eacd9c940f94cc5f7102e907f187acf7d8b29bec0b9cab28df20fb";

async function request(endpoint, options = {}) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${API_TOKEN}`
            },
            ...options,
        });
        if (!res.ok) {
            const errorBody = await res.json().catch(() => ({}));
            console.warn(`API error [${endpoint}]: HTTP ${res.status}`, errorBody);
            return null;
        }
        return await res.json();
    } catch (err) {
        console.warn(`API error [${endpoint}]:`, err.message);
        return null;
    }
}

export const api = {
    // ── Account & Stats ────────────────────────────────────────────
    getStats: () => request("/stats"),
    getAccount: () => request("/account"),

    // ── Trades & Positions ─────────────────────────────────────────
    getTrades: (status) => request(`/trades${status ? `?status=${status}` : ""}`),
    getOpenTrades: () => request("/open-trades"),
    getPositions: () => request("/positions"),
    getHistory: (days = 30) => request(`/history?days=${days}`),
    getPerformance: (days = 30) => request(`/performance?days=${days}`),

    // ── Config ─────────────────────────────────────────────────────
    getConfig: () => request("/config"),
    updateConfig: (data) => request("/config", { method: "PUT", body: JSON.stringify(data) }),
    getStrategies: () => request("/strategies"),
    updateStrategies: (data) => request("/strategies", { method: "PUT", body: JSON.stringify(data) }),

    // ── Kill Switch ────────────────────────────────────────────────
    getKillSwitch: () => request("/kill-switch"),
    activateKillSwitch: () => request("/kill-switch", { method: "POST" }),
    deactivateKillSwitch: () => request("/kill-switch", { method: "DELETE" }),

    // ── MT5 Connection ─────────────────────────────────────────────
    getMT5Config: () => request("/mt5/config"),
    saveMT5Config: (data) => request("/mt5/config", { method: "PUT", body: JSON.stringify(data) }),
    testMT5Connection: (data) => request("/mt5/connect", { method: "POST", body: JSON.stringify(data) }),
    getMT5Status: () => request("/mt5/status"),
    disconnectMT5: () => request("/mt5/disconnect", { method: "POST" }),
    reconnectMT5: () => request("/mt5/reconnect", { method: "POST" }),

    // ── AI Agent Control ───────────────────────────────────────────
    getAgentStatus: () => request("/agent/status"),
    getAgentThoughts: () => request("/agent/thoughts"),
    startAgent: () => request("/agent/start", { method: "POST" }),
    stopAgent: () => request("/agent/stop", { method: "POST" }),
    enableAgentTrading: (enabled) => request("/agent/enable-trading", {
        method: "POST",
        body: JSON.stringify({ enabled })
    }),

    // ── Health ─────────────────────────────────────────────────────
    health: () => request("/health"),
};

export default api;

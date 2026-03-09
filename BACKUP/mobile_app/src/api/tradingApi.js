// API client for the Trading Engine Flask API
// ⚠️  PC's local WiFi IP — must be on same network as phone
const PC_IP = "192.168.1.5";
const API_BASE = `http://${PC_IP}:5050/api`;

async function request(endpoint, options = {}) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.warn(`API error [${endpoint}]:`, err.message);
        return null;
    }
}

export const api = {
    getStats: () => request("/stats"),
    getTrades: (status) => request(`/trades${status ? `?status=${status}` : ""}`),
    getOpenTrades: () => request("/open-trades"),
    getPerformance: (days = 30) => request(`/performance?days=${days}`),
    getConfig: () => request("/config"),
    updateConfig: (data) => request("/config", { method: "PUT", body: JSON.stringify(data) }),
    getStrategies: () => request("/strategies"),
    updateStrategies: (data) => request("/strategies", { method: "PUT", body: JSON.stringify(data) }),
    getKillSwitch: () => request("/kill-switch"),
    activateKillSwitch: () => request("/kill-switch", { method: "POST" }),
    deactivateKillSwitch: () => request("/kill-switch", { method: "DELETE" }),
    // MT5 Connection
    getMT5Config: () => request("/mt5/config"),
    saveMT5Config: (data) => request("/mt5/config", { method: "PUT", body: JSON.stringify(data) }),
    testMT5Connection: (data) => request("/mt5/connect", { method: "POST", body: JSON.stringify(data) }),
    getMT5Status: () => request("/mt5/status"),
    disconnectMT5: () => request("/mt5/disconnect", { method: "POST" }),
    // AI Agent Control
    getAgentStatus: () => request("/agent/status"),
    startAgent: () => request("/agent/start", { method: "POST" }),
    stopAgent: () => request("/agent/stop", { method: "POST" }),
};

export default api;

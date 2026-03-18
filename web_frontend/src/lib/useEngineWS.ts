/**
 * useEngineWS — subscribes to /ws/feed and delivers typed engine events.
 * Auto-reconnects on disconnect. Updates engineStatus and killSwitchActive state.
 */
"use client";
import { useEffect, useRef, useCallback, useState } from "react";

export interface WSEvent {
    type: string;
    timestamp: string;
    severity: "info" | "warning" | "error";
    data: Record<string, any>;
}

export interface EngineStatus {
    mt5Connected: boolean;
    killSwitchActive: boolean;
    killSwitchReason: string;
    dailyTrades: number;
    currentPositions: number;
    dailyPnl: number;
    balance: number;
    equity: number;
    session: string;
    wsConnected: boolean;
    lastError: string | null;
}

const DEFAULT_STATUS: EngineStatus = {
    mt5Connected: false,
    killSwitchActive: false,
    killSwitchReason: "",
    dailyTrades: 0,
    currentPositions: 0,
    dailyPnl: 0,
    balance: 0,
    equity: 0,
    session: "unknown",
    wsConnected: false,
    lastError: null,
};

const WS_URL =
    typeof window !== "undefined"
        ? (process.env.NEXT_PUBLIC_WS_URL ||
            `${window.location.protocol === "https:" ? "wss" : "ws"}://${process.env.NEXT_PUBLIC_API_HOST || "localhost:8000"
            }/ws/feed`)
        : "ws://localhost:8000/ws/feed";

export function useEngineWS(
    onEvent?: (e: WSEvent) => void
): EngineStatus {
    const [status, setStatus] = useState<EngineStatus>(DEFAULT_STATUS);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
    const mounted = useRef(true);

    const connect = useCallback(() => {
        if (!mounted.current) return;
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
            setStatus((s) => ({ ...s, wsConnected: true }));
        };

        ws.onclose = () => {
            setStatus((s) => ({ ...s, wsConnected: false }));
            if (mounted.current) {
                reconnectTimer.current = setTimeout(connect, 3000);
            }
        };

        ws.onerror = () => {
            ws.close();
        };

        ws.onmessage = (ev) => {
            try {
                const event: WSEvent = JSON.parse(ev.data);
                onEvent?.(event);

                if (event.type === "heartbeat") {
                    const { mt5, error } = event.data || {};
                    setStatus((s) => ({
                        ...s,
                        mt5Connected: mt5?.connected ?? s.mt5Connected,
                        lastError: error || null,
                    }));
                } else if (event.type === "engine_status") {
                    const d = event.data || {};
                    setStatus((s) => ({
                        ...s,
                        mt5Connected: d.mt5?.connected ?? s.mt5Connected,
                        balance: d.balance ?? s.balance,
                        equity: d.equity ?? s.equity,
                        lastError: d.error || null,
                    }));
                } else if (event.type === "error") {
                    setStatus((s) => ({
                        ...s,
                        lastError: event.data?.message || "Unknown error",
                    }));
                } else if (event.type === "kill_switch") {
                    setStatus((s) => ({
                        ...s,
                        killSwitchActive: event.data?.active ?? s.killSwitchActive,
                        killSwitchReason: event.data?.reason ?? s.killSwitchReason,
                    }));
                } else if (event.type === "position_update") {
                    setStatus((s) => ({
                        ...s,
                        currentPositions: event.data?.count ?? s.currentPositions,
                    }));
                }
            } catch (_) { }
        };
    }, [onEvent]);

    useEffect(() => {
        mounted.current = true;
        connect();
        return () => {
            mounted.current = false;
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
            wsRef.current?.close();
        };
    }, [connect]);

    return status;
}

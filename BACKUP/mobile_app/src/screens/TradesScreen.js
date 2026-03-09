import React, { useState, useEffect, useCallback } from "react";
import {
    View, Text, SectionList, TouchableOpacity,
    StyleSheet, RefreshControl, StatusBar,
} from "react-native";
import { colors, shadow, radius } from "../theme/colors";
import api from "../api/tradingApi";

const FILTERS = ["ALL", "OPEN", "CLOSED"];

function FilterPill({ label, active, onPress }) {
    return (
        <TouchableOpacity
            onPress={onPress}
            style={[styles.pill, active && styles.pillActive]}
        >
            <Text style={[styles.pillText, active && styles.pillTextActive]}>{label}</Text>
        </TouchableOpacity>
    );
}

function SummaryBar({ trades }) {
    const pnl = trades.reduce((s, t) => s + parseFloat(t.pnl || 0), 0);
    const wins = trades.filter(t => parseFloat(t.pnl) > 0).length;
    const loss = trades.filter(t => parseFloat(t.pnl) < 0).length;
    const winPct = trades.length ? Math.round((wins / trades.length) * 100) : 0;

    return (
        <View style={[styles.summaryBar, shadow.sm]}>
            <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>P&L</Text>
                <Text style={[styles.summaryValue, { color: pnl >= 0 ? colors.profit : colors.loss }]}>
                    {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
                </Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>Wins</Text>
                <Text style={[styles.summaryValue, { color: colors.profit }]}>{wins}</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>Losses</Text>
                <Text style={[styles.summaryValue, { color: colors.loss }]}>{loss}</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>Win %</Text>
                <Text style={[styles.summaryValue, { color: colors.accent }]}>{winPct}%</Text>
            </View>
        </View>
    );
}

function TradeRow({ trade }) {
    const pnl = parseFloat(trade.pnl || 0);
    const isProfit = pnl >= 0;
    const isOpen = trade.status === "OPEN";
    const stratColor = {
        VOLATILITY_BREAKOUT: colors.strategy?.volatility || "#FF6B35",
        LONDON_BREAKOUT: colors.strategy?.london || "#007AFF",
        AGGRESSIVE_TREND: colors.strategy?.trend || "#5856D6",
        MEAN_REVERSION: colors.strategy?.reversion || "#34C759",
        LIVE: colors.accent,
    }[trade.strategy] || colors.textMuted;

    return (
        <View style={styles.tradeRow}>
            <View style={[styles.tradeAccent, { backgroundColor: isProfit ? colors.profit : colors.loss }]} />
            <View style={[styles.tradeIcon, { backgroundColor: isProfit ? colors.profitLight : colors.lossLight }]}>
                <Text style={{ fontSize: 16 }}>{isProfit ? "📈" : "📉"}</Text>
            </View>
            <View style={styles.tradeBody}>
                <View style={styles.tradeTopRow}>
                    <Text style={styles.tradeSymbol}>{trade.symbol}</Text>
                    <View style={[styles.dirBadge, { backgroundColor: trade.direction === "LONG" ? colors.profitLight : colors.lossLight }]}>
                        <Text style={[styles.dirText, { color: trade.direction === "LONG" ? colors.profit : colors.loss }]}>
                            {trade.direction === "LONG" ? "▲" : "▼"} {trade.direction}
                        </Text>
                    </View>
                </View>
                <View style={styles.tradeMeta}>
                    <View style={[styles.stratBadge, { backgroundColor: stratColor + "15" }]}>
                        <Text style={[styles.stratText, { color: stratColor }]}>
                            {trade.strategy?.replace(/_/g, " ").slice(0, 14)}
                        </Text>
                    </View>
                    <Text style={styles.tradeSub}>
                        {trade.lots} lots · {trade.timestamp?.slice(5, 16)}
                    </Text>
                </View>
                {trade.entry ? <Text style={styles.tradeEntry}>Entry @ {trade.entry}</Text> : null}
            </View>
            <View style={styles.tradeRight}>
                <Text style={[styles.tradePnl, { color: isProfit ? colors.profit : colors.loss }]}>
                    {isProfit ? "+" : ""}${pnl.toFixed(2)}
                </Text>
                <View style={[styles.statusChip, { backgroundColor: isOpen ? colors.accentLight : colors.surfaceAlt }]}>
                    <Text style={[styles.statusText, { color: isOpen ? colors.accent : colors.textMuted }]}>
                        {isOpen ? "● OPEN" : "CLOSED"}
                    </Text>
                </View>
            </View>
        </View>
    );
}

export default function TradesScreen() {
    const [trades, setTrades] = useState([]);
    const [filter, setFilter] = useState("ALL");
    const [refreshing, setRefreshing] = useState(false);
    const [isLive, setIsLive] = useState(false);

    const load = useCallback(async () => {
        const res = await api.getTrades();
        if (res?.trades) {
            setTrades(res.trades);
            setIsLive(!!res.live);
        }
        setRefreshing(false);
    }, []);

    useEffect(() => { load(); }, []);

    const filtered = filter === "ALL"
        ? trades
        : trades.filter(t => t.status === filter);

    return (
        <View style={styles.container}>
            <StatusBar barStyle="dark-content" backgroundColor={colors.bg} />

            {/* Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.title}>Trade Journal</Text>
                    <Text style={styles.subtitle}>{filtered.length} trades{isLive ? " · Live MT5" : ""}</Text>
                </View>
                {isLive && (
                    <View style={styles.liveChip}>
                        <View style={styles.liveDot} />
                        <Text style={styles.liveText}>LIVE</Text>
                    </View>
                )}
            </View>

            {/* Filter Pills */}
            <View style={styles.filters}>
                {FILTERS.map(f => (
                    <FilterPill key={f} label={f} active={filter === f} onPress={() => setFilter(f)} />
                ))}
            </View>

            {/* Summary */}
            <SummaryBar trades={filtered} />

            {/* Trade List */}
            <SectionList
                sections={[{ data: filtered }]}
                keyExtractor={(t, i) => t.trade_id || String(i)}
                renderItem={({ item }) => <TradeRow trade={item} />}
                ItemSeparatorComponent={() => <View style={styles.sep} />}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.accent} />}
                ListEmptyComponent={
                    <View style={styles.empty}>
                        <Text style={styles.emptyIcon}>📭</Text>
                        <Text style={styles.emptyText}>No {filter.toLowerCase()} trades</Text>
                    </View>
                }
                contentContainerStyle={{ paddingBottom: 100 }}
                style={styles.list}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.bg },
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end", paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16 },
    title: { fontSize: 28, fontWeight: "800", color: colors.textPrimary },
    subtitle: { fontSize: 13, color: colors.textSecondary, marginTop: 2 },
    liveChip: { flexDirection: "row", alignItems: "center", backgroundColor: colors.profitLight, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999 },
    liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.profit, marginRight: 5 },
    liveText: { fontSize: 11, fontWeight: "800", color: colors.profit, letterSpacing: 1 },
    filters: { flexDirection: "row", paddingHorizontal: 20, gap: 8, marginBottom: 12 },
    pill: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    pillActive: { backgroundColor: colors.accent, borderColor: colors.accent },
    pillText: { fontSize: 13, fontWeight: "600", color: colors.textSecondary },
    pillTextActive: { color: "#FFFFFF" },
    summaryBar: { flexDirection: "row", marginHorizontal: 20, marginBottom: 16, backgroundColor: colors.surface, borderRadius: radius.lg, padding: 14, borderWidth: 1, borderColor: colors.border },
    summaryItem: { flex: 1, alignItems: "center" },
    summaryDivider: { width: 1, backgroundColor: colors.border },
    summaryLabel: { fontSize: 11, color: colors.textMuted, fontWeight: "500", marginBottom: 4 },
    summaryValue: { fontSize: 16, fontWeight: "800" },
    list: { flex: 1 },
    tradeRow: { flexDirection: "row", alignItems: "center", backgroundColor: colors.surface, paddingVertical: 14, paddingRight: 16, paddingLeft: 4 },
    tradeAccent: { width: 3, height: 44, borderRadius: 2, marginRight: 12 },
    tradeIcon: { width: 40, height: 40, borderRadius: 12, alignItems: "center", justifyContent: "center", marginRight: 12 },
    tradeBody: { flex: 1 },
    tradeTopRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4 },
    tradeSymbol: { fontSize: 16, fontWeight: "800", color: colors.textPrimary },
    dirBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 },
    dirText: { fontSize: 11, fontWeight: "700" },
    tradeMeta: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 2 },
    stratBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
    stratText: { fontSize: 10, fontWeight: "700" },
    tradeSub: { fontSize: 11, color: colors.textMuted },
    tradeEntry: { fontSize: 11, color: colors.textMuted },
    tradeRight: { alignItems: "flex-end", gap: 6 },
    tradePnl: { fontSize: 16, fontWeight: "800" },
    statusChip: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999 },
    statusText: { fontSize: 10, fontWeight: "700" },
    sep: { height: 1, backgroundColor: colors.border, marginLeft: 72 },
    empty: { padding: 48, alignItems: "center" },
    emptyIcon: { fontSize: 40, marginBottom: 12 },
    emptyText: { fontSize: 15, color: colors.textMuted },
});

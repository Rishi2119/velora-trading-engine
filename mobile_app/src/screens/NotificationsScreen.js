import React, { useState, useEffect } from "react";
import {
    View, Text, FlatList, TouchableOpacity,
    StyleSheet, RefreshControl, StatusBar,
} from "react-native";
import { colors, shadow, radius } from "../theme/colors";

const DEMO_NOTIFS = [
    { id: "1", type: "TRADE", icon: "📈", title: "Trade Opened", sub: "EURUSD Long · Vol. Breakout", time: "2m ago", amount: null },
    { id: "2", type: "TRADE", icon: "📉", title: "Trade Closed", sub: "USDCAD Short −$22.10", time: "2h ago", amount: -22.10 },
    { id: "3", type: "TRADE", icon: "✅", title: "Trade Closed +$88.40", sub: "AUDUSD Long · Aggressive Trend", time: "3h ago", amount: 88.40 },
    { id: "4", type: "ALERT", icon: "⚠️", title: "Max Concurrent Trades", sub: "Limit of 2 positions reached", time: "4h ago", amount: null },
    { id: "5", type: "SESSION", icon: "🇬🇧", title: "London Session Open", sub: "09:00 GMT — Trading window active", time: "5h ago", amount: null },
    { id: "6", type: "TRADE", icon: "🔒", title: "Breakeven Set", sub: "NZDUSD · SL moved to entry", time: "6h ago", amount: null },
    { id: "7", type: "ALERT", icon: "📰", title: "High-Impact News", sub: "NFP report — Trades paused", time: "7h ago", amount: null },
    { id: "8", type: "SESSION", icon: "🇺🇸", title: "New York Session Open", sub: "14:00 GMT — Overlap active", time: "8h ago", amount: null },
    { id: "9", type: "TRADE", icon: "📈", title: "Trade Opened", sub: "GBPUSD Long · London Breakout", time: "8h ago", amount: null },
    { id: "10", type: "TRADE", icon: "💰", title: "Take Profit Hit", sub: "EURUSD +$45.50 · 3.5R", time: "9h ago", amount: 45.50 },
];

const FILTER_CFG = {
    ALL: { label: "All", icon: "📋" },
    TRADE: { label: "Trades", icon: "📊" },
    ALERT: { label: "Alerts", icon: "⚠️" },
    SESSION: { label: "Sessions", icon: "🌍" },
};

const TYPE_COLORS = {
    TRADE: colors.accent,
    ALERT: colors.warning,
    SESSION: colors.info,
};

function NotifCard({ item }) {
    const typeColor = TYPE_COLORS[item.type] || colors.textMuted;
    const hasAmount = item.amount != null;
    const isProfit = hasAmount && item.amount > 0;

    return (
        <View style={styles.notifRow}>
            <View style={[styles.notifIcon, { backgroundColor: typeColor + "12" }]}>
                <Text style={{ fontSize: 18 }}>{item.icon}</Text>
            </View>
            <View style={styles.notifBody}>
                <Text style={styles.notifTitle}>{item.title}</Text>
                <Text style={styles.notifSub}>{item.sub}</Text>
            </View>
            <View style={styles.notifRight}>
                {hasAmount && (
                    <Text style={[styles.notifAmount, { color: isProfit ? colors.profit : colors.loss }]}>
                        {isProfit ? "+" : ""}${Math.abs(item.amount).toFixed(2)}
                    </Text>
                )}
                <Text style={styles.notifTime}>{item.time}</Text>
            </View>
        </View>
    );
}

export default function NotificationsScreen() {
    const [filter, setFilter] = useState("ALL");
    const [refreshing, setRefreshing] = useState(false);
    const [notifs, setNotifs] = useState(DEMO_NOTIFS);

    const filtered = filter === "ALL" ? notifs : notifs.filter(n => n.type === filter);

    // Summary counts
    const trades = notifs.filter(n => n.type === "TRADE").length;
    const alerts = notifs.filter(n => n.type === "ALERT").length;
    const wins = notifs.filter(n => n.amount > 0).length;
    const losses = notifs.filter(n => n.amount < 0).length;

    return (
        <View style={styles.container}>
            <StatusBar barStyle="dark-content" />

            {/* Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.title}>Activity</Text>
                    <Text style={styles.subtitle}>Trade events & alerts</Text>
                </View>
                <TouchableOpacity
                    onPress={() => { setRefreshing(true); setTimeout(() => setRefreshing(false), 800); }}
                    style={styles.refreshBtn}
                >
                    <Text style={{ fontSize: 16 }}>↻</Text>
                </TouchableOpacity>
            </View>

            {/* Summary Chips */}
            <View style={styles.chips}>
                {[
                    { label: `${trades} Trades`, color: colors.accent },
                    { label: `${wins} Wins`, color: colors.profit },
                    { label: `${losses} Losses`, color: colors.loss },
                    { label: `${alerts} Alerts`, color: colors.warning },
                ].map(c => (
                    <View key={c.label} style={[styles.chip, { backgroundColor: c.color + "12" }]}>
                        <Text style={[styles.chipText, { color: c.color }]}>{c.label}</Text>
                    </View>
                ))}
            </View>

            {/* Filter Pills */}
            <View style={styles.filters}>
                {Object.entries(FILTER_CFG).map(([key, cfg]) => (
                    <TouchableOpacity
                        key={key}
                        onPress={() => setFilter(key)}
                        style={[styles.pill, filter === key && styles.pillActive]}
                    >
                        <Text style={{ fontSize: 12, marginRight: 4 }}>{cfg.icon}</Text>
                        <Text style={[styles.pillText, filter === key && styles.pillTextActive]}>{cfg.label}</Text>
                    </TouchableOpacity>
                ))}
            </View>

            {/* Feed */}
            <FlatList
                data={filtered}
                keyExtractor={i => i.id}
                renderItem={({ item }) => <NotifCard item={item} />}
                ItemSeparatorComponent={() => <View style={styles.sep} />}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); setTimeout(() => setRefreshing(false), 600); }} tintColor={colors.accent} />}
                ListEmptyComponent={
                    <View style={styles.empty}>
                        <Text style={styles.emptyIcon}>📭</Text>
                        <Text style={styles.emptyText}>No {filter.toLowerCase()} events</Text>
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
    subtitle: { fontSize: 13, color: colors.textSecondary },
    refreshBtn: { width: 38, height: 38, borderRadius: 19, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, alignItems: "center", justifyContent: "center" },
    chips: { flexDirection: "row", flexWrap: "wrap", paddingHorizontal: 20, gap: 8, marginBottom: 12 },
    chip: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 999 },
    chipText: { fontSize: 12, fontWeight: "700" },
    filters: { flexDirection: "row", paddingHorizontal: 20, gap: 8, marginBottom: 16 },
    pill: { flexDirection: "row", alignItems: "center", paddingHorizontal: 12, paddingVertical: 7, borderRadius: 999, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    pillActive: { backgroundColor: colors.accent, borderColor: colors.accent },
    pillText: { fontSize: 12, fontWeight: "600", color: colors.textSecondary },
    pillTextActive: { color: "#FFFFFF" },
    list: { flex: 1 },
    notifRow: { flexDirection: "row", alignItems: "center", paddingHorizontal: 20, paddingVertical: 14, backgroundColor: colors.surface, gap: 12 },
    notifIcon: { width: 44, height: 44, borderRadius: 14, alignItems: "center", justifyContent: "center" },
    notifBody: { flex: 1 },
    notifTitle: { fontSize: 15, fontWeight: "700", color: colors.textPrimary },
    notifSub: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    notifRight: { alignItems: "flex-end" },
    notifAmount: { fontSize: 15, fontWeight: "700" },
    notifTime: { fontSize: 11, color: colors.textMuted, marginTop: 2 },
    sep: { height: 1, backgroundColor: colors.border, marginLeft: 76 },
    empty: { padding: 48, alignItems: "center" },
    emptyIcon: { fontSize: 40, marginBottom: 12 },
    emptyText: { fontSize: 15, color: colors.textMuted },
});

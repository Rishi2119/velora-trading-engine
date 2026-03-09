import React, { useState, useEffect, useRef } from "react";
import {
    View, Text, ScrollView, TouchableOpacity, StyleSheet,
    Animated, RefreshControl, StatusBar, Dimensions, Image,
} from "react-native";
import { colors, shadow, radius } from "../theme/colors";
import api from "../api/tradingApi";

const VELORA_LOGO = null; // require("../../assets/velora_logo.png");
const { width } = Dimensions.get("window");

// ─── Reusable Components ─────────────────────────────────────────

function ActionButton({ icon, label, onPress, color }) {
    const scale = useRef(new Animated.Value(1)).current;
    const press = () => {
        Animated.sequence([
            Animated.timing(scale, { toValue: 0.92, duration: 80, useNativeDriver: true }),
            Animated.timing(scale, { toValue: 1, duration: 120, useNativeDriver: true }),
        ]).start();
        onPress?.();
    };
    return (
        <TouchableOpacity onPress={press} activeOpacity={0.8} style={styles.actionItem}>
            <Animated.View style={[styles.actionIconWrap, { backgroundColor: color || colors.accentLight, transform: [{ scale }] }]}>
                <Text style={styles.actionIcon}>{icon}</Text>
            </Animated.View>
            <Text style={styles.actionLabel}>{label}</Text>
        </TouchableOpacity>
    );
}

function StatCard({ icon, label, value, valueColor }) {
    return (
        <View style={[styles.statCard, shadow.sm]}>
            <Text style={styles.statIcon}>{icon}</Text>
            <Text style={styles.statLabel}>{label}</Text>
            <Text style={[styles.statValue, valueColor && { color: valueColor }]}>{value}</Text>
        </View>
    );
}

function ActivityRow({ trade }) {
    const isProfit = parseFloat(trade.pnl) >= 0;
    const isOpen = trade.status === "OPEN";
    return (
        <View style={styles.activityRow}>
            <View style={[styles.activityIcon, { backgroundColor: isProfit ? colors.profitLight : colors.lossLight }]}>
                <Text style={{ fontSize: 16 }}>{isProfit ? "📈" : "📉"}</Text>
            </View>
            <View style={styles.activityBody}>
                <Text style={styles.activityTitle}>{trade.symbol}</Text>
                <Text style={styles.activitySub}>
                    {trade.direction} · {trade.strategy?.replace(/_/g, " ").slice(0, 12)}{isOpen ? " · LIVE" : ""}
                </Text>
            </View>
            <View style={styles.activityRight}>
                <Text style={[styles.activityAmount, { color: isProfit ? colors.profit : colors.loss }]}>
                    {isProfit ? "+" : ""}${parseFloat(trade.pnl || 0).toFixed(2)}
                </Text>
                <Text style={styles.activityDate}>{trade.timestamp?.slice(5, 16)}</Text>
            </View>
        </View>
    );
}

// ─── Main Screen ─────────────────────────────────────────────────

export default function DashboardScreen() {
    const [stats, setStats] = useState(null);
    const [trades, setTrades] = useState([]);
    const [agentStats, setAgentStats] = useState(null);
    const [killSwitch, setKillSwitch] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const fadeAnim = useRef(new Animated.Value(0)).current;

    const isLive = stats?.mt5_connected || false;

    const fetchData = async () => {
        const [s, t, a] = await Promise.all([api.getStats(), api.getTrades(), api.getAgentStatus()]);
        if (s) { setStats(s); setKillSwitch(s.kill_switch_active); }
        if (t?.trades) setTrades(t.trades.slice(0, 5));
        if (a && !a.error) setAgentStats(a);
        setRefreshing(false);
        Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }).start();
    };

    useEffect(() => {
        fetchData();
        const id = setInterval(fetchData, isLive ? 5000 : 15000);
        return () => clearInterval(id);
    }, [isLive]);

    const toggleKill = async () => {
        killSwitch ? await api.deactivateKillSwitch() : await api.activateKillSwitch();
        setKillSwitch(!killSwitch);
    };

    const toggleAgent = async () => {
        if (!agentStats) return;
        const isRunning = agentStats.is_running;
        const res = isRunning ? await api.stopAgent() : await api.startAgent();
        if (res?.success) {
            setAgentStats(res.status);
        }
        fetchData();
    };

    const s = stats || {
        account_balance: 500, equity: 500, open_pnl: 0,
        total_pnl: 224, win_rate: 62.1, total_trades: 87,
        open_trades_count: 0, avg_rr: 3.2, max_drawdown: -145,
        profit_factor: 2.1, mt5_connected: false, currency: "USD",
    };

    const isPnlPos = s.total_pnl >= 0;

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchData(); }} tintColor={colors.accent} />}
        >
            <StatusBar barStyle="dark-content" backgroundColor={colors.bg} />
            <Animated.View style={{ opacity: fadeAnim }}>

                {/* ── Header — Velora Logo ───────────────────────────── */}
                <View style={styles.header}>
                    <View style={styles.brandRow}>
                        <Image source={VELORA_LOGO} style={styles.logo} resizeMode="contain" />
                        <View>
                            <Text style={styles.brandName}>Velora</Text>
                            <Text style={styles.brandSub}>AI Trading</Text>
                        </View>
                    </View>
                    <View style={styles.headerRight}>
                        {isLive && (
                            <View style={styles.liveChip}>
                                <View style={styles.liveDot} />
                                <Text style={styles.liveChipText}>LIVE</Text>
                            </View>
                        )}
                        <TouchableOpacity onPress={toggleKill} style={[styles.killBtn, killSwitch && styles.killBtnActive]}>
                            <Text style={[styles.killBtnText, killSwitch && { color: colors.loss }]}>
                                {killSwitch ? "⏹ KILL" : "⏸ Pause"}
                            </Text>
                        </TouchableOpacity>
                    </View>
                </View>

                {/* ── Kill alert ─────────────────────────────────────── */}
                {killSwitch && (
                    <View style={styles.killAlert}>
                        <Text style={styles.killAlertText}>🛑 Kill Switch Active — All trading paused</Text>
                        <TouchableOpacity onPress={toggleKill}>
                            <Text style={styles.killAlertAction}>Resume</Text>
                        </TouchableOpacity>
                    </View>
                )}

                {/* ── Balance Card ───────────────────────────────────── */}
                <View style={[styles.balanceCard, shadow.md]}>
                    {/* Watermark logo inside card */}
                    <Image
                        source={VELORA_LOGO}
                        style={styles.cardWatermark}
                        resizeMode="contain"
                    />
                    <Text style={styles.balanceLabel}>Available Balance</Text>
                    <Text style={styles.balanceAmount}>
                        {s.currency} {Number(s.account_balance).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </Text>

                    {isLive && (
                        <View style={styles.equityRow}>
                            <View style={styles.equityItem}>
                                <Text style={styles.equityLabel}>Equity</Text>
                                <Text style={styles.equityValue}>${Number(s.equity).toFixed(2)}</Text>
                            </View>
                            <View style={styles.equityDivider} />
                            <View style={styles.equityItem}>
                                <Text style={styles.equityLabel}>Open P&L</Text>
                                <Text style={[styles.equityValue, { color: (s.open_pnl || 0) >= 0 ? "#90EE90" : "#FFB3B3" }]}>
                                    {(s.open_pnl || 0) >= 0 ? "+" : ""}${Number(s.open_pnl || 0).toFixed(2)}
                                </Text>
                            </View>
                            <View style={styles.equityDivider} />
                            <View style={styles.equityItem}>
                                <Text style={styles.equityLabel}>Positions</Text>
                                <Text style={styles.equityValue}>{s.open_trades_count}</Text>
                            </View>
                        </View>
                    )}

                    <View style={[styles.pnlBadge, { backgroundColor: isPnlPos ? "rgba(144,238,144,0.25)" : "rgba(255,179,179,0.25)" }]}>
                        <Text style={[styles.pnlBadgeText, { color: isPnlPos ? "#90EE90" : "#FFB3B3" }]}>
                            {isPnlPos ? "+" : ""}${Number(s.total_pnl).toFixed(2)} total P&L   {isPnlPos ? "▲" : "▼"}
                        </Text>
                    </View>
                </View>

                {/* ── AI Auto-Trader Card ────────────────────────────── */}
                <View style={[styles.aiCard, shadow.md]}>
                    <View style={styles.aiHeader}>
                        <View style={styles.aiHeaderLeft}>
                            <View style={[styles.aiIconBadge, agentStats?.is_running && { backgroundColor: colors.accent }]}>
                                <Text style={styles.aiIconText}>🧠</Text>
                            </View>
                            <View>
                                <Text style={styles.aiTitle}>AI Auto-Trader</Text>
                                <Text style={styles.aiSub}>Powered by Kimi K2.5</Text>
                            </View>
                        </View>
                        <TouchableOpacity
                            style={[styles.aiToggleBtn, agentStats?.is_running && styles.aiToggleActive]}
                            onPress={toggleAgent}
                        >
                            <Text style={[styles.aiToggleText, agentStats?.is_running && { color: "#FFFFFF" }]}>
                                {agentStats?.is_running ? "Running" : "Start"}
                            </Text>
                        </TouchableOpacity>
                    </View>

                    <View style={styles.aiBrainBox}>
                        <Text style={styles.aiBrainLabel}>LIVE THOUGHT PROCESS</Text>
                        <Text style={styles.aiBrainText} numberOfLines={3}>
                            {agentStats ? agentStats.latest_thought : "Initializing AI engine..."}
                        </Text>
                        <View style={styles.aiDecisionRow}>
                            <Text style={styles.aiDecisionLabel}>Latest Decision:</Text>
                            <Text style={[
                                styles.aiDecisionValue,
                                agentStats?.latest_decision === "TRADE" ? { color: colors.profit } : { color: colors.textSecondary }
                            ]}>
                                {agentStats?.latest_decision || "NONE"}
                            </Text>
                            {agentStats?.confidence > 0 && (
                                <Text style={styles.aiConfidence}>
                                    ({Math.round(agentStats.confidence * 100)}% conf)
                                </Text>
                            )}
                        </View>
                        {agentStats?.sentiment && (
                            <View style={[styles.aiDecisionRow, { marginTop: 8, borderTopWidth: 0, paddingTop: 0 }]}>
                                <Text style={styles.aiDecisionLabel}>Market Sentiment:</Text>
                                <Text style={[
                                    styles.aiDecisionValue,
                                    { color: agentStats.sentiment.score > 0 ? colors.profit : agentStats.sentiment.score < 0 ? colors.loss : colors.textPrimary }
                                ]}>
                                    {agentStats.sentiment.label?.replace(/_/g, " ")}
                                </Text>
                                <Text style={styles.aiConfidence}>
                                    ({agentStats.sentiment.score > 0 ? "+" : ""}{agentStats.sentiment.score})
                                </Text>
                            </View>
                        )}
                    </View>
                </View>

                {/* ── Quick Actions ──────────────────────────────────── */}
                <View style={styles.actionsRow}>
                    <ActionButton icon="📊" label="Trades" color={colors.accentLight} />
                    <ActionButton icon="⚙️" label="Config" color="#F3F0FF" />
                    <ActionButton icon="📈" label="Charts" color={colors.profitLight} />
                    <ActionButton icon="🔔" label="Alerts" color={colors.warningLight} />
                </View>

                {/* ── Stats Grid ─────────────────────────────────────── */}
                <Text style={styles.sectionTitle}>Performance</Text>
                <View style={styles.statsRow}>
                    <StatCard icon="🎯" label="Win Rate" value={`${Number(s.win_rate).toFixed(1)}%`} valueColor={colors.profit} />
                    <StatCard icon="⚖️" label="Avg R:R" value={`${Number(s.avg_rr).toFixed(1)}:1`} valueColor={colors.accent} />
                    <StatCard icon="📉" label="Max Drawdown" value={`$${Math.abs(s.max_drawdown).toFixed(0)}`} valueColor={colors.loss} />
                    <StatCard icon="💹" label="Profit Factor" value={`${Number(s.profit_factor).toFixed(2)}`} valueColor={colors.info} />
                </View>

                {/* ── Recent Activity ────────────────────────────────── */}
                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Recent Activity</Text>
                    <Text style={styles.sectionCount}>{s.total_trades} total</Text>
                </View>

                <View style={[styles.activityCard, shadow.sm]}>
                    {trades.length === 0 ? (
                        <View style={styles.emptyState}>
                            <Text style={styles.emptyIcon}>📭</Text>
                            <Text style={styles.emptyText}>No recent trades</Text>
                        </View>
                    ) : (
                        trades.map((t, i) => (
                            <View key={t.trade_id || i}>
                                <ActivityRow trade={t} />
                                {i < trades.length - 1 && <View style={styles.divider} />}
                            </View>
                        ))
                    )}
                </View>

                {/* ── Powered by Footer ──────────────────────────────── */}
                <View style={styles.footer}>
                    <Image source={VELORA_LOGO} style={styles.footerLogo} resizeMode="contain" />
                    <Text style={styles.footerText}>Velora AI Trading Engine</Text>
                </View>

                <View style={{ height: 100 }} />
            </Animated.View>
        </ScrollView>
    );
}

function getTimeOfDay() {
    const h = new Date().getHours();
    if (h < 12) return "Morning";
    if (h < 17) return "Afternoon";
    return "Evening";
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.bg },

    // Header (Velora brand)
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingHorizontal: 20, paddingTop: 56, paddingBottom: 16 },
    brandRow: { flexDirection: "row", alignItems: "center", gap: 10 },
    logo: { width: 44, height: 44 },
    brandName: { fontSize: 20, fontWeight: "900", color: colors.textPrimary, letterSpacing: 0.5 },
    brandSub: { fontSize: 11, color: colors.textSecondary, fontWeight: "500", letterSpacing: 0.5 },
    headerRight: { flexDirection: "row", alignItems: "center", gap: 8 },
    liveChip: { flexDirection: "row", alignItems: "center", backgroundColor: colors.profitLight, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999 },
    liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.profit, marginRight: 5 },
    liveChipText: { fontSize: 11, fontWeight: "800", color: colors.profit, letterSpacing: 1 },
    killBtn: { backgroundColor: colors.surfaceAlt, paddingHorizontal: 12, paddingVertical: 7, borderRadius: 999, borderWidth: 1, borderColor: colors.border },
    killBtnActive: { backgroundColor: colors.lossLight, borderColor: colors.loss + "60" },
    killBtnText: { fontSize: 12, fontWeight: "700", color: colors.textSecondary },
    killAlert: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginHorizontal: 20, marginBottom: 12, padding: 14, backgroundColor: colors.lossLight, borderRadius: radius.md, borderWidth: 1, borderColor: colors.loss + "30" },
    killAlertText: { fontSize: 13, fontWeight: "600", color: colors.loss },
    killAlertAction: { fontSize: 13, fontWeight: "700", color: colors.accent },

    // Balance Card (blue with watermark logo)
    balanceCard: { marginHorizontal: 20, marginBottom: 24, padding: 24, backgroundColor: colors.accent, borderRadius: radius.xl, overflow: "hidden" },
    cardWatermark: { position: "absolute", right: -10, top: -10, width: 120, height: 120, opacity: 0.12 },
    balanceLabel: { fontSize: 13, color: "rgba(255,255,255,0.75)", fontWeight: "500", marginBottom: 6 },
    balanceAmount: { fontSize: 38, fontWeight: "800", color: "#FFFFFF", letterSpacing: -1, marginBottom: 16 },
    equityRow: { flexDirection: "row", backgroundColor: "rgba(255,255,255,0.15)", borderRadius: radius.md, padding: 12, marginBottom: 16 },
    equityItem: { flex: 1, alignItems: "center" },
    equityDivider: { width: 1, backgroundColor: "rgba(255,255,255,0.2)" },
    equityLabel: { fontSize: 10, color: "rgba(255,255,255,0.7)", marginBottom: 2, fontWeight: "500" },
    equityValue: { fontSize: 15, fontWeight: "700", color: "#FFFFFF" },
    pnlBadge: { alignSelf: "flex-start", paddingHorizontal: 12, paddingVertical: 6, borderRadius: radius.full },
    pnlBadgeText: { fontSize: 13, fontWeight: "700" },

    // AI Card
    aiCard: { marginHorizontal: 20, marginBottom: 24, padding: 16, backgroundColor: colors.surface, borderRadius: radius.xl, borderWidth: 1, borderColor: colors.border },
    aiHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
    aiHeaderLeft: { flexDirection: "row", alignItems: "center", gap: 12 },
    aiIconBadge: { width: 44, height: 44, borderRadius: 16, backgroundColor: colors.surfaceAlt, alignItems: "center", justifyContent: "center" },
    aiIconText: { fontSize: 24 },
    aiTitle: { fontSize: 16, fontWeight: "800", color: colors.textPrimary },
    aiSub: { fontSize: 11, color: colors.textSecondary, fontWeight: "600" },
    aiToggleBtn: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.surfaceAlt },
    aiToggleActive: { backgroundColor: colors.accent },
    aiToggleText: { fontSize: 13, fontWeight: "700", color: colors.textPrimary },
    aiBrainBox: { backgroundColor: "#F9FAFC", borderRadius: radius.md, padding: 14, borderWidth: 1, borderColor: colors.border },
    aiBrainLabel: { fontSize: 10, fontWeight: "800", color: colors.textMuted, letterSpacing: 0.5, marginBottom: 6 },
    aiBrainText: { fontSize: 13, color: colors.textPrimary, fontStyle: "italic", lineHeight: 20, marginBottom: 12 },
    aiDecisionRow: { flexDirection: "row", alignItems: "center", gap: 6, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 10 },
    aiDecisionLabel: { fontSize: 11, color: colors.textSecondary, fontWeight: "600" },
    aiDecisionValue: { fontSize: 12, fontWeight: "800" },
    aiConfidence: { fontSize: 11, color: colors.textMuted },

    // Actions
    actionsRow: { flexDirection: "row", justifyContent: "space-between", paddingHorizontal: 20, marginBottom: 28 },
    actionItem: { alignItems: "center", gap: 8 },
    actionIconWrap: { width: 56, height: 56, borderRadius: 18, alignItems: "center", justifyContent: "center" },
    actionIcon: { fontSize: 22 },
    actionLabel: { fontSize: 11, fontWeight: "600", color: colors.textSecondary },

    // Stats
    sectionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingHorizontal: 20, marginBottom: 12 },
    sectionTitle: { fontSize: 18, fontWeight: "700", color: colors.textPrimary, paddingHorizontal: 20, marginBottom: 12 },
    sectionCount: { fontSize: 13, color: colors.textMuted },
    statsRow: { flexDirection: "row", flexWrap: "wrap", paddingHorizontal: 12, marginBottom: 28, gap: 8 },
    statCard: { width: (width - 24 - 8 * 3) / 2, backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16, borderWidth: 1, borderColor: colors.border },
    statIcon: { fontSize: 20, marginBottom: 8 },
    statLabel: { fontSize: 11, color: colors.textMuted, fontWeight: "600", marginBottom: 4 },
    statValue: { fontSize: 22, fontWeight: "800", color: colors.textPrimary },

    // Activity
    activityCard: { marginHorizontal: 20, marginBottom: 16, backgroundColor: colors.surface, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border, overflow: "hidden" },
    activityRow: { flexDirection: "row", alignItems: "center", padding: 16, gap: 12 },
    activityIcon: { width: 42, height: 42, borderRadius: 13, alignItems: "center", justifyContent: "center" },
    activityBody: { flex: 1 },
    activityTitle: { fontSize: 15, fontWeight: "700", color: colors.textPrimary },
    activitySub: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    activityRight: { alignItems: "flex-end" },
    activityAmount: { fontSize: 15, fontWeight: "700" },
    activityDate: { fontSize: 11, color: colors.textMuted, marginTop: 2 },
    divider: { height: 1, backgroundColor: colors.border, marginHorizontal: 16 },
    emptyState: { padding: 32, alignItems: "center" },
    emptyIcon: { fontSize: 32, marginBottom: 8 },
    emptyText: { fontSize: 14, color: colors.textMuted },

    // Footer
    footer: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, paddingVertical: 8, opacity: 0.4 },
    footerLogo: { width: 20, height: 20 },
    footerText: { fontSize: 11, color: colors.textSecondary, fontWeight: "600" },
});

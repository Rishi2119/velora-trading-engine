import React, { useState, useEffect } from "react";
import {
    View, Text, ScrollView, TouchableOpacity,
    StyleSheet, Dimensions, RefreshControl, StatusBar,
} from "react-native";
import { LineChart } from "react-native-chart-kit";
import { colors, shadow, radius } from "../theme/colors";
import api from "../api/tradingApi";

const { width } = Dimensions.get("window");
const RANGES = [7, 14, 30];
const CHART_W = width - 40;

function KpiCard({ icon, label, value, valueColor }) {
    return (
        <View style={[styles.kpiCard, shadow.sm]}>
            <Text style={styles.kpiIcon}>{icon}</Text>
            <Text style={styles.kpiValue} numberOfLines={1} style={[styles.kpiValue, valueColor && { color: valueColor }]}>{value}</Text>
            <Text style={styles.kpiLabel}>{label}</Text>
        </View>
    );
}

function WinLossBar({ winRate }) {
    const win = winRate || 0;
    const los = 100 - win;
    return (
        <View style={styles.wlContainer}>
            <Text style={styles.wlTitle}>Win / Loss Split</Text>
            <View style={styles.wlBar}>
                <View style={[styles.wlWin, { flex: win }]} />
                <View style={[styles.wlLoss, { flex: los }]} />
            </View>
            <View style={styles.wlLegend}>
                <View style={styles.wlLegendItem}>
                    <View style={[styles.wlDot, { backgroundColor: colors.profit }]} />
                    <Text style={styles.wlLegendText}>Wins {win.toFixed(1)}%</Text>
                </View>
                <View style={styles.wlLegendItem}>
                    <View style={[styles.wlDot, { backgroundColor: colors.loss }]} />
                    <Text style={styles.wlLegendText}>Losses {los.toFixed(1)}%</Text>
                </View>
            </View>
        </View>
    );
}

export default function PerformanceScreen() {
    const [perf, setPerf] = useState(null);
    const [range, setRange] = useState(30);
    const [refreshing, setRefreshing] = useState(false);

    const load = async () => {
        const res = await api.getPerformance(range);
        if (res) setPerf(res);
        setRefreshing(false);
    };

    useEffect(() => { load(); }, [range]);

    const daily = perf?.daily || [];
    const summary = perf?.summary || {};
    const isLive = perf?.live || false;

    // Chart data — only show days that have data
    const chartDays = daily.slice(-range);
    const labels = chartDays.filter((_, i) => i % Math.ceil(chartDays.length / 5) === 0).map(d => d.date?.slice(5));
    const pnlData = chartDays.map(d => d.pnl || 0);
    const balData = chartDays.map(d => d.balance || 0);

    const chartConfig = {
        backgroundGradientFrom: "#FFFFFF",
        backgroundGradientTo: "#FFFFFF",
        color: (opacity = 1) => `rgba(0,122,255,${opacity})`,
        strokeWidth: 2,
        decimalPlaces: 0,
        propsForDots: { r: "3", strokeWidth: "2", stroke: colors.accent },
        propsForBackgroundLines: { stroke: colors.border },
        labelColor: () => colors.textMuted,
    };

    // Sum daily P&L for all days
    const totalPnl = pnlData.reduce((a, b) => a + b, 0);
    const positivedays = pnlData.filter(v => v > 0).length;

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.accent} />}
        >
            <StatusBar barStyle="dark-content" />

            {/* Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.title}>Performance</Text>
                    <Text style={styles.subtitle}>{isLive ? "Live MT5 data" : "Demo data"}</Text>
                </View>
                <View style={styles.rangeRow}>
                    {RANGES.map(r => (
                        <TouchableOpacity key={r} onPress={() => setRange(r)} style={[styles.rangeBtn, range === r && styles.rangeBtnActive]}>
                            <Text style={[styles.rangeBtnText, range === r && styles.rangeBtnTextActive]}>{r}D</Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </View>

            {/* KPI Grid */}
            <View style={styles.kpiGrid}>
                <KpiCard icon="💰" label="Total P&L" value={`$${Number(summary.total_pnl || 0).toFixed(2)}`} valueColor={summary.total_pnl >= 0 ? colors.profit : colors.loss} />
                <KpiCard icon="🎯" label="Win Rate" value={`${Number(summary.win_rate || 0).toFixed(1)}%`} valueColor={colors.profit} />
                <KpiCard icon="💹" label="Profit Factor" value={`${Number(summary.profit_factor || 0).toFixed(2)}`} valueColor={colors.accent} />
                <KpiCard icon="⚖️" label="Avg R:R" value={`${Number(summary.avg_rr || 0).toFixed(1)}:1`} valueColor={colors.info} />
                <KpiCard icon="📉" label="Max Drawdown" value={`$${Math.abs(summary.max_drawdown || 0).toFixed(0)}`} valueColor={colors.loss} />
                {isLive && <KpiCard icon="💳" label="Balance" value={`$${Number(summary.balance || 0).toFixed(2)}`} valueColor={colors.accent} />}
            </View>

            {/* Win/Loss Bar */}
            <View style={[styles.card, shadow.sm]}>
                <WinLossBar winRate={summary.win_rate || 0} />
                <View style={styles.cardDivider} />
                <View style={styles.inlineStat}>
                    <Text style={styles.inlineLabel}>Positive Days</Text>
                    <Text style={[styles.inlineValue, { color: colors.profit }]}>{positivedays} / {chartDays.length}</Text>
                </View>
                <View style={styles.inlineStat}>
                    <Text style={styles.inlineLabel}>Period P&L</Text>
                    <Text style={[styles.inlineValue, { color: totalPnl >= 0 ? colors.profit : colors.loss }]}>
                        {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}
                    </Text>
                </View>
            </View>

            {/* Daily P&L Chart */}
            {pnlData.length > 1 && (
                <View style={[styles.chartCard, shadow.sm]}>
                    <Text style={styles.chartTitle}>Daily P&L</Text>
                    <LineChart
                        data={{ labels, datasets: [{ data: pnlData.length > 0 ? pnlData : [0] }] }}
                        width={CHART_W}
                        height={180}
                        chartConfig={chartConfig}
                        bezier
                        withInnerLines={false}
                        style={{ borderRadius: radius.md, marginLeft: -8 }}
                    />
                </View>
            )}

            {/* Equity Curve */}
            {balData.length > 1 && (
                <View style={[styles.chartCard, shadow.sm]}>
                    <Text style={styles.chartTitle}>Equity Curve</Text>
                    <LineChart
                        data={{ labels, datasets: [{ data: balData, color: () => colors.profit }] }}
                        width={CHART_W}
                        height={160}
                        chartConfig={{ ...chartConfig, color: (o) => `rgba(52,199,89,${o})` }}
                        bezier
                        withInnerLines={false}
                        style={{ borderRadius: radius.md, marginLeft: -8 }}
                    />
                </View>
            )}

            {/* Recent Days */}
            {daily.length > 0 && (
                <>
                    <Text style={styles.sectionTitle}>Day-by-Day</Text>
                    <View style={[styles.card, shadow.sm]}>
                        {[...daily].reverse().slice(0, 7).map((d, i) => (
                            <View key={d.date}>
                                <View style={styles.dayRow}>
                                    <Text style={styles.dayDate}>{d.date}</Text>
                                    <Text style={[styles.dayPnl, { color: d.pnl >= 0 ? colors.profit : colors.loss }]}>
                                        {d.pnl >= 0 ? "+" : ""}${d.pnl?.toFixed(2)}
                                    </Text>
                                    <Text style={styles.dayBalance}>${d.balance?.toFixed(2)}</Text>
                                </View>
                                {i < 6 && <View style={styles.cardDivider} />}
                            </View>
                        ))}
                    </View>
                </>
            )}

            <View style={{ height: 100 }} />
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.bg },
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end", paddingHorizontal: 20, paddingTop: 60, paddingBottom: 20 },
    title: { fontSize: 28, fontWeight: "800", color: colors.textPrimary },
    subtitle: { fontSize: 13, color: colors.textSecondary },
    rangeRow: { flexDirection: "row", gap: 6 },
    rangeBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 999, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
    rangeBtnActive: { backgroundColor: colors.accent, borderColor: colors.accent },
    rangeBtnText: { fontSize: 12, fontWeight: "700", color: colors.textSecondary },
    rangeBtnTextActive: { color: "#FFFFFF" },
    kpiGrid: { flexDirection: "row", flexWrap: "wrap", padding: 12, gap: 8, marginBottom: 8 },
    kpiCard: { width: (width - 40 - 8) / 2, backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16, borderWidth: 1, borderColor: colors.border },
    kpiIcon: { fontSize: 20, marginBottom: 6 },
    kpiValue: { fontSize: 22, fontWeight: "800", color: colors.textPrimary, marginBottom: 4 },
    kpiLabel: { fontSize: 11, color: colors.textMuted, fontWeight: "500" },
    card: { marginHorizontal: 20, marginBottom: 16, backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16, borderWidth: 1, borderColor: colors.border },
    cardDivider: { height: 1, backgroundColor: colors.border, marginVertical: 12 },
    inlineStat: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 2 },
    inlineLabel: { fontSize: 14, color: colors.textSecondary },
    inlineValue: { fontSize: 15, fontWeight: "700" },
    wlContainer: {},
    wlTitle: { fontSize: 13, fontWeight: "700", color: colors.textSecondary, marginBottom: 10 },
    wlBar: { flexDirection: "row", height: 8, borderRadius: 4, overflow: "hidden", marginBottom: 10 },
    wlWin: { backgroundColor: colors.profit },
    wlLoss: { backgroundColor: colors.loss },
    wlLegend: { flexDirection: "row", gap: 16 },
    wlLegendItem: { flexDirection: "row", alignItems: "center", gap: 6 },
    wlDot: { width: 8, height: 8, borderRadius: 4 },
    wlLegendText: { fontSize: 12, color: colors.textSecondary, fontWeight: "500" },
    chartCard: { marginHorizontal: 20, marginBottom: 16, backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16, borderWidth: 1, borderColor: colors.border },
    chartTitle: { fontSize: 15, fontWeight: "700", color: colors.textPrimary, marginBottom: 12 },
    sectionTitle: { fontSize: 18, fontWeight: "700", color: colors.textPrimary, paddingHorizontal: 20, marginBottom: 10 },
    dayRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 2 },
    dayDate: { fontSize: 13, color: colors.textSecondary, flex: 1 },
    dayPnl: { fontSize: 14, fontWeight: "700", width: 80, textAlign: "right" },
    dayBalance: { fontSize: 13, color: colors.textMuted, width: 80, textAlign: "right" },
});

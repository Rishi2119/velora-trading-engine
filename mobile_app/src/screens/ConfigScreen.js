import React, { useState, useEffect } from "react";
import {
    View, Text, ScrollView, TouchableOpacity, Switch,
    StyleSheet, Alert, RefreshControl, StatusBar,
} from "react-native";
import { colors, shadow, radius } from "../theme/colors";
import api from "../api/tradingApi";

function SectionCard({ title, children }) {
    return (
        <View style={styles.section}>
            <Text style={styles.sectionTitle}>{title}</Text>
            <View style={[styles.card, shadow.sm]}>{children}</View>
        </View>
    );
}

function Row({ label, sub, right, borderTop }) {
    return (
        <View style={[styles.row, borderTop && styles.rowBorder]}>
            <View style={{ flex: 1 }}>
                <Text style={styles.rowLabel}>{label}</Text>
                {sub ? <Text style={styles.rowSub}>{sub}</Text> : null}
            </View>
            {right}
        </View>
    );
}

function StepperRow({ label, sub, value, onDec, onInc, format, borderTop }) {
    return (
        <Row
            label={label}
            sub={sub}
            borderTop={borderTop}
            right={
                <View style={styles.stepper}>
                    <TouchableOpacity onPress={onDec} style={styles.stepBtn}>
                        <Text style={styles.stepBtnText}>−</Text>
                    </TouchableOpacity>
                    <Text style={styles.stepValue}>{format ? format(value) : value}</Text>
                    <TouchableOpacity onPress={onInc} style={styles.stepBtn}>
                        <Text style={styles.stepBtnText}>+</Text>
                    </TouchableOpacity>
                </View>
            }
        />
    );
}

function ToggleRow({ label, sub, value, onChange, borderTop }) {
    return (
        <Row
            label={label}
            sub={sub}
            borderTop={borderTop}
            right={
                <Switch
                    value={value}
                    onValueChange={onChange}
                    thumbColor={value ? colors.accent : colors.textMuted}
                    trackColor={{ false: colors.border, true: colors.accent + "60" }}
                />
            }
        />
    );
}

export default function ConfigScreen() {
    const [config, setConfig] = useState({});
    const [strats, setStrats] = useState({});
    const [dirty, setDirty] = useState(false);
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        const [c, s] = await Promise.all([api.getConfig(), api.getStrategies()]);
        if (c) setConfig(c);
        if (s) setStrats(s);
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const set = (key, val) => { setConfig(p => ({ ...p, [key]: val })); setDirty(true); };
    const setSt = (key, val) => { setStrats(p => ({ ...p, [key]: val })); setDirty(true); };

    const save = async () => {
        setSaving(true);
        await Promise.all([api.updateConfig(config), api.updateStrategies(strats)]);
        setSaving(false);
        setDirty(false);
        Alert.alert("✅ Saved", "Configuration updated.");
    };

    const c = config;
    const bal = c.account_balance || 500;
    const riskAmt = ((c.risk_per_trade || 0.01) * bal).toFixed(2);

    return (
        <View style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <ScrollView
                contentContainerStyle={{ paddingBottom: 120 }}
                refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor={colors.accent} />}
            >
                {/* Header */}
                <View style={styles.header}>
                    <View>
                        <Text style={styles.title}>Configuration</Text>
                        <Text style={styles.subtitle}>Risk management & strategy settings</Text>
                    </View>
                    {dirty && (
                        <TouchableOpacity onPress={save} style={[styles.saveBtn, saving && { opacity: 0.6 }]} disabled={saving}>
                            <Text style={styles.saveBtnText}>{saving ? "Saving…" : "Save"}</Text>
                        </TouchableOpacity>
                    )}
                </View>

                {/* Risk alert */}
                <View style={styles.riskAlert}>
                    <Text style={styles.riskIcon}>⚠️</Text>
                    <Text style={styles.riskText}>
                        Current risk: {((c.risk_per_trade || 0.01) * 100).toFixed(1)}% per trade = ${riskAmt} on ${bal} account
                    </Text>
                </View>

                {/* Risk Management */}
                <SectionCard title="Risk Management">
                    <StepperRow
                        label="Risk Per Trade"
                        sub={`$${riskAmt} per position`}
                        value={c.risk_per_trade || 0.01}
                        onDec={() => set("risk_per_trade", Math.max(0.005, (c.risk_per_trade || 0.01) - 0.005))}
                        onInc={() => set("risk_per_trade", Math.min(0.05, (c.risk_per_trade || 0.01) + 0.005))}
                        format={v => `${(v * 100).toFixed(1)}%`}
                    />
                    <StepperRow borderTop
                        label="Min Risk:Reward"
                        value={c.min_risk_reward || 3.0}
                        onDec={() => set("min_risk_reward", Math.max(1.5, (c.min_risk_reward || 3.0) - 0.5))}
                        onInc={() => set("min_risk_reward", Math.min(5.0, (c.min_risk_reward || 3.0) + 0.5))}
                        format={v => `${v.toFixed(1)}:1`}
                    />
                    <StepperRow borderTop
                        label="Max Daily Loss"
                        value={c.max_daily_loss || 20}
                        onDec={() => set("max_daily_loss", Math.max(10, (c.max_daily_loss || 20) - 5))}
                        onInc={() => set("max_daily_loss", Math.min(150, (c.max_daily_loss || 20) + 5))}
                        format={v => `$${v}`}
                    />
                    <StepperRow borderTop
                        label="Max Daily Trades"
                        value={c.max_daily_trades || 5}
                        onDec={() => set("max_daily_trades", Math.max(1, (c.max_daily_trades || 5) - 1))}
                        onInc={() => set("max_daily_trades", Math.min(20, (c.max_daily_trades || 5) + 1))}
                    />
                    <StepperRow borderTop
                        label="Max Concurrent"
                        value={c.max_concurrent_trades || 2}
                        onDec={() => set("max_concurrent_trades", Math.max(1, (c.max_concurrent_trades || 2) - 1))}
                        onInc={() => set("max_concurrent_trades", Math.min(5, (c.max_concurrent_trades || 2) + 1))}
                        format={v => `${v} trades`}
                    />
                </SectionCard>

                {/* Strategies */}
                <SectionCard title="Strategies">
                    <ToggleRow label="Volatility Breakout" sub="High priority — aggressive entries" value={strats.volatility_breakout ?? true} onChange={v => setSt("volatility_breakout", v)} />
                    <ToggleRow borderTop label="London Breakout" sub="Session-timed entries" value={strats.london_breakout ?? true} onChange={v => setSt("london_breakout", v)} />
                    <ToggleRow borderTop label="Aggressive Trend" sub="Momentum-following" value={strats.aggressive_trend ?? true} onChange={v => setSt("aggressive_trend", v)} />
                    <ToggleRow borderTop label="Mean Reversion" sub="Counter-trend plays" value={strats.mean_reversion ?? false} onChange={v => setSt("mean_reversion", v)} />
                </SectionCard>

                {/* Filters */}
                <SectionCard title="Filters">
                    <ToggleRow label="Session Filter" sub="Trade London & New York only" value={c.enable_session_filter ?? true} onChange={v => set("enable_session_filter", v)} />
                    <ToggleRow borderTop label="News Filter" sub="Avoid high-impact news events" value={c.enable_news_filter ?? true} onChange={v => set("enable_news_filter", v)} />
                </SectionCard>

                {/* Trade Management */}
                <SectionCard title="Trade Management">
                    <StepperRow
                        label="Breakeven Trigger"
                        sub="Pips in profit to move SL to entry"
                        value={c.breakeven_trigger_pips || 15}
                        onDec={() => set("breakeven_trigger_pips", Math.max(5, (c.breakeven_trigger_pips || 15) - 5))}
                        onInc={() => set("breakeven_trigger_pips", Math.min(50, (c.breakeven_trigger_pips || 15) + 5))}
                        format={v => `${v} pips`}
                    />
                    <StepperRow borderTop
                        label="Trailing Stop Start"
                        value={c.trailing_start_pips || 20}
                        onDec={() => set("trailing_start_pips", Math.max(10, (c.trailing_start_pips || 20) - 5))}
                        onInc={() => set("trailing_start_pips", Math.min(80, (c.trailing_start_pips || 20) + 5))}
                        format={v => `${v} pips`}
                    />
                    <StepperRow borderTop
                        label="Trailing Distance"
                        value={c.trailing_distance_pips || 10}
                        onDec={() => set("trailing_distance_pips", Math.max(5, (c.trailing_distance_pips || 10) - 5))}
                        onInc={() => set("trailing_distance_pips", Math.min(40, (c.trailing_distance_pips || 10) + 5))}
                        format={v => `${v} pips`}
                    />
                </SectionCard>
            </ScrollView>

            {/* Floating Save */}
            {dirty && (
                <View style={styles.floatSave}>
                    <TouchableOpacity style={styles.floatBtn} onPress={save} disabled={saving}>
                        <Text style={styles.floatBtnText}>{saving ? "Saving…" : "💾  Save Changes"}</Text>
                    </TouchableOpacity>
                </View>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.bg },
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end", paddingHorizontal: 20, paddingTop: 60, paddingBottom: 20 },
    title: { fontSize: 28, fontWeight: "800", color: colors.textPrimary },
    subtitle: { fontSize: 13, color: colors.textSecondary, marginTop: 2 },
    saveBtn: { backgroundColor: colors.accent, paddingHorizontal: 18, paddingVertical: 9, borderRadius: 999 },
    saveBtnText: { color: "#FFFFFF", fontWeight: "700", fontSize: 14 },
    riskAlert: { flexDirection: "row", alignItems: "center", marginHorizontal: 20, marginBottom: 16, padding: 12, backgroundColor: colors.warningLight, borderRadius: radius.md, gap: 8 },
    riskIcon: { fontSize: 16 },
    riskText: { flex: 1, fontSize: 13, color: colors.warning, fontWeight: "500" },
    section: { paddingHorizontal: 20, marginBottom: 16 },
    sectionTitle: { fontSize: 13, fontWeight: "700", color: colors.textSecondary, letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 8 },
    card: { backgroundColor: colors.surface, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border, overflow: "hidden" },
    row: { flexDirection: "row", alignItems: "center", paddingHorizontal: 16, paddingVertical: 14 },
    rowBorder: { borderTopWidth: 1, borderTopColor: colors.border },
    rowLabel: { fontSize: 15, fontWeight: "600", color: colors.textPrimary },
    rowSub: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    stepper: { flexDirection: "row", alignItems: "center", gap: 12 },
    stepBtn: { width: 32, height: 32, borderRadius: 16, backgroundColor: colors.surfaceAlt, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: colors.border },
    stepBtnText: { fontSize: 18, fontWeight: "300", color: colors.textSecondary },
    stepValue: { fontSize: 15, fontWeight: "700", color: colors.accent, minWidth: 52, textAlign: "center" },
    floatSave: { position: "absolute", bottom: 30, left: 24, right: 24 },
    floatBtn: { backgroundColor: colors.accent, paddingVertical: 18, borderRadius: radius.xl, alignItems: "center", shadowColor: colors.accent, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.4, shadowRadius: 16, elevation: 8 },
    floatBtnText: { color: "#FFFFFF", fontSize: 16, fontWeight: "800" },
});

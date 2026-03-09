import React, { useState, useEffect } from "react";
import {
    View, Text, ScrollView, TextInput, TouchableOpacity,
    StyleSheet, Alert, Switch, ActivityIndicator, StatusBar,
} from "react-native";
import { colors, shadow, radius } from "../theme/colors";
import api from "../api/tradingApi";

const SERVERS = [
    "MetaQuotes-Demo",
    "ICMarketsSC-Demo",
    "ICMarketsSC-Live",
    "Pepperstone-Demo",
    "Pepperstone-Live",
    "XM.COM-Demo 3",
    "XM.COM-Real 3",
    "Exness-Trial",
    "Exness-Real4",
    "FusionMarkets-Demo",
    "FusionMarkets-Live",
    "Admirals-Demo",
    "Admirals-Live",
    "OctaFX-Real",
    "OctaFX-Demo",
];

const STATUS_CONFIG = {
    connected: { color: colors.profit, icon: "●", label: "CONNECTED" },
    disconnected: { color: colors.loss, icon: "●", label: "DISCONNECTED" },
    connecting: { color: colors.warning, icon: "◐", label: "CONNECTING…" },
    unknown: { color: colors.textMuted, icon: "○", label: "NOT TESTED" },
};

// ─── Sub-components ─────────────────────────────────────────────────

function InputField({ label, value, onChangeText, secureTextEntry, placeholder, keyboardType }) {
    const [focused, setFocused] = useState(false);
    const [showPass, setShowPass] = useState(false);
    return (
        <View style={styles.inputWrapper}>
            <Text style={styles.inputLabel}>{label}</Text>
            <View style={[styles.inputRow, focused && styles.inputFocused]}>
                <TextInput
                    style={styles.input}
                    value={value}
                    onChangeText={onChangeText}
                    placeholder={placeholder}
                    placeholderTextColor={colors.textMuted}
                    secureTextEntry={secureTextEntry && !showPass}
                    keyboardType={keyboardType || "default"}
                    autoCapitalize="none"
                    autoCorrect={false}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                />
                {secureTextEntry && (
                    <TouchableOpacity onPress={() => setShowPass(!showPass)} style={styles.eyeBtn}>
                        <Text style={styles.eyeIcon}>{showPass ? "👁" : "🙈"}</Text>
                    </TouchableOpacity>
                )}
            </View>
        </View>
    );
}

function ServerPicker({ selected, onSelect }) {
    const [open, setOpen] = useState(false);
    return (
        <View style={styles.inputWrapper}>
            <Text style={styles.inputLabel}>Broker Server</Text>
            <TouchableOpacity
                style={[styles.inputRow, open && styles.inputFocused]}
                onPress={() => setOpen(!open)}
            >
                <Text style={[styles.input, { color: selected ? colors.textPrimary : colors.textMuted }]}>
                    {selected || "Select your broker server…"}
                </Text>
                <Text style={styles.eyeIcon}>▾</Text>
            </TouchableOpacity>
            {open && (
                <View style={styles.dropdown}>
                    <ScrollView style={{ maxHeight: 200 }} nestedScrollEnabled>
                        {SERVERS.map(s => (
                            <TouchableOpacity
                                key={s}
                                style={[styles.dropdownItem, s === selected && styles.dropdownItemActive]}
                                onPress={() => { onSelect(s); setOpen(false); }}
                            >
                                <Text style={[styles.dropdownText, s === selected && { color: colors.accent }]}>{s}</Text>
                                {s === selected && <Text style={{ color: colors.accent }}>✓</Text>}
                            </TouchableOpacity>
                        ))}
                    </ScrollView>
                </View>
            )}
        </View>
    );
}

function StatusBadge({ status }) {
    const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.unknown;
    return (
        <View style={[styles.statusBadge, { backgroundColor: cfg.color + "12", borderColor: cfg.color + "40" }]}>
            <Text style={{ color: cfg.color, fontSize: 10 }}>{cfg.icon} </Text>
            <Text style={[styles.statusText, { color: cfg.color }]}>{cfg.label}</Text>
        </View>
    );
}

// ─── Main Screen ────────────────────────────────────────────────────

export default function MT5Screen() {
    const [account, setAccount] = useState("");
    const [password, setPassword] = useState("");
    const [server, setServer] = useState("");
    const [enableLive, setEnableLive] = useState(false);
    const [status, setStatus] = useState("unknown");
    const [testing, setTesting] = useState(false);
    const [saving, setSaving] = useState(false);
    const [lastTested, setLastTested] = useState(null);
    const [brokerInfo, setBrokerInfo] = useState(null);

    useEffect(() => {
        loadSavedSettings();
        checkLiveStatus();
        const interval = setInterval(checkLiveStatus, 10000);
        return () => clearInterval(interval);
    }, []);

    const checkLiveStatus = async () => {
        try {
            // Use centralized API instead of hardcoded URL
            const res = await api.getMT5Status();
            if (res?.connected) {
                setStatus("connected");
                setBrokerInfo(res.account);
                setLastTested(new Date().toLocaleTimeString());
            } else {
                if (status === "connected") setStatus("disconnected");
            }
        } catch (_) { }
    };

    const loadSavedSettings = async () => {
        const res = await api.getMT5Config();
        if (res) {
            setAccount(res.account?.toString() === "0" ? "" : (res.account?.toString() || ""));
            setPassword(res.password ? "••••••••" : "");
            setServer(res.server || "");
            setEnableLive(res.enable_execution || false);
            if (res.connected) {
                setStatus("connected");
            } else if (res.last_status) {
                setStatus(res.last_status);
            }
        }
    };

    const saveSettings = async () => {
        if (!account || !server) {
            Alert.alert("Missing Fields", "Please fill in Account Number and Server.");
            return;
        }
        setSaving(true);
        const payload = { account, server, enable_execution: enableLive };
        if (password && password !== "••••••••") payload.password = password;
        const res = await api.saveMT5Config(payload);
        setSaving(false);
        Alert.alert(res?.success ? "✅ Saved" : "⚠️ Failed", res?.success ? "Settings saved." : "Could not save. Check API.");
    };

    const testConnection = async () => {
        if (!account || !server) {
            Alert.alert("Missing Fields", "Please fill in Account Number and Server first.");
            return;
        }
        if (!password || password === "••••••••") {
            Alert.alert("Password Required", "Please enter your full MT5 password to test a new connection.");
            return;
        }
        setTesting(true);
        setStatus("connecting");
        setBrokerInfo(null);
        const res = await api.testMT5Connection({ account, password, server });
        setTesting(false);
        if (res?.connected) {
            setStatus("connected");
            setBrokerInfo(res.info || null);
            setLastTested(new Date().toLocaleTimeString());
            await api.saveMT5Config({ account, password, server, enable_execution: enableLive });
        } else {
            setStatus("disconnected");
            Alert.alert(
                "❌ Connection Failed",
                res?.error || "Could not connect to MT5.\n\nMake sure:\n1. MetaTrader 5 is open\n2. pip install MetaTrader5\n3. Credentials are correct"
            );
        }
    };

    const disconnectMT5 = () => {
        Alert.alert(
            "Disconnect MT5?",
            "The app will switch to demo mode.",
            [
                { text: "Cancel", style: "cancel" },
                {
                    text: "Disconnect", style: "destructive", onPress: async () => {
                        // Use centralized API
                        await api.disconnectMT5();
                        setStatus("disconnected");
                        setBrokerInfo(null);
                    }
                },
            ]
        );
    };

    return (
        <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
            <StatusBar barStyle="dark-content" backgroundColor={colors.bg} />

            {/* Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.title}>MT5 Connection</Text>
                    <Text style={styles.subtitle}>Connect your broker account</Text>
                </View>
                <StatusBadge status={status} />
            </View>

            {/* ── CONNECTED INFO CARD ─────────────────────────── */}
            {status === "connected" && brokerInfo && (
                <View style={styles.connectedCard}>
                    <Text style={styles.connectedTitle}>✅ Live MT5 Connection Active</Text>
                    <View style={styles.infoGrid}>
                        {Object.entries(brokerInfo).map(([k, v]) => {
                            const isBalance = k === "balance" || k === "equity";
                            const isProfit = k === "profit";
                            const profitNum = isProfit ? parseFloat(v) : null;
                            return (
                                <View key={k} style={styles.infoItem}>
                                    <Text style={styles.infoKey}>{k.replace(/_/g, " ").toUpperCase()}</Text>
                                    <Text style={[
                                        styles.infoVal,
                                        isBalance && { color: colors.profit },
                                        isProfit && { color: profitNum >= 0 ? colors.profit : colors.loss },
                                    ]}>{String(v)}</Text>
                                </View>
                            );
                        })}
                    </View>
                    {lastTested && <Text style={styles.lastTested}>Updated: {lastTested}</Text>}
                    <TouchableOpacity style={styles.disconnectBtn} onPress={disconnectMT5}>
                        <Text style={styles.disconnectText}>⏏ Disconnect</Text>
                    </TouchableOpacity>
                </View>
            )}

            {/* ── SECURITY WARNING ────────────────────────────── */}
            <View style={styles.warningBox}>
                <Text style={styles.warningTitle}>⚠️ Security Notice</Text>
                <Text style={styles.warningText}>
                    Credentials are stored locally in the Flask API config. Use an investor (read-only) password when possible. Never share your trading password.
                </Text>
            </View>

            {/* ── CREDENTIALS FORM ────────────────────────────── */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>🔑 Broker Credentials</Text>
                <View style={[styles.card, shadow.sm]}>
                    <InputField label="Account Number" value={account} onChangeText={setAccount} placeholder="e.g. 5046125612" keyboardType="numeric" />
                    <View style={styles.divider} />
                    <InputField label="Password" value={password} onChangeText={setPassword} placeholder="Your MT5 password" secureTextEntry />
                    <View style={styles.divider} />
                    <ServerPicker selected={server} onSelect={setServer} />
                    <View style={styles.divider} />
                    <InputField label="Custom Server (if not in list above)" value={SERVERS.includes(server) ? "" : server} onChangeText={setServer} placeholder="e.g. YourBroker-Server01" />
                </View>
            </View>

            {/* ── TRADING MODE ────────────────────────────────── */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>⚡ Trading Mode</Text>
                <View style={[styles.card, shadow.sm]}>
                    <View style={styles.toggleRow}>
                        <View style={{ flex: 1 }}>
                            <Text style={styles.toggleLabel}>Enable Live Trading</Text>
                            <Text style={styles.toggleSub}>
                                {enableLive ? "⚠️ LIVE MODE — Real money at risk!" : "✅ PAPER MODE — No real orders"}
                            </Text>
                        </View>
                        <Switch
                            value={enableLive}
                            onValueChange={(v) => {
                                if (v) {
                                    Alert.alert(
                                        "⚠️ Enable Live Trading?",
                                        "This will execute REAL trades with REAL money on your broker account.",
                                        [
                                            { text: "Cancel", style: "cancel" },
                                            { text: "Enable Live", style: "destructive", onPress: () => setEnableLive(true) },
                                        ]
                                    );
                                } else {
                                    setEnableLive(false);
                                }
                            }}
                            thumbColor={enableLive ? colors.loss : colors.profit}
                            trackColor={{ false: colors.profit + "40", true: colors.loss + "40" }}
                        />
                    </View>
                    {enableLive && (
                        <View style={styles.liveWarning}>
                            <Text style={styles.liveWarningText}>🔴 LIVE TRADING ON — Real orders will be placed</Text>
                        </View>
                    )}
                </View>
            </View>

            {/* ── SETUP GUIDE ──────────────────────────────────── */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>ℹ️ Setup Guide</Text>
                <View style={[styles.card, shadow.sm]}>
                    {[
                        ["1", "Install MetaTrader 5 on your PC"],
                        ["2", "pip install MetaTrader5 (in terminal)"],
                        ["3", "Open MT5 terminal and log in to your broker"],
                        ["4", "Enter the same account #, password & server above"],
                        ["5", "Run: python mobile_api/app.py"],
                        ["6", "Tap 'Connect to MT5' — live data flows instantly"],
                    ].map(([num, step]) => (
                        <View key={num} style={styles.step}>
                            <View style={styles.stepNum}><Text style={styles.stepNumText}>{num}</Text></View>
                            <Text style={styles.stepText}>{step}</Text>
                        </View>
                    ))}
                </View>
            </View>

            {/* ── ACTION BUTTONS ──────────────────────────────── */}
            <View style={styles.btnRow}>
                <TouchableOpacity
                    style={[styles.testBtn, testing && { opacity: 0.7 }]}
                    onPress={testConnection}
                    disabled={testing}
                >
                    {testing
                        ? <ActivityIndicator color="#FFFFFF" size="small" />
                        : <Text style={styles.testBtnText}>🔌 Connect to MT5</Text>
                    }
                </TouchableOpacity>
                <TouchableOpacity
                    style={[styles.saveBtn, saving && { opacity: 0.7 }]}
                    onPress={saveSettings}
                    disabled={saving}
                >
                    <Text style={styles.saveBtnText}>{saving ? "Saving…" : "💾 Save"}</Text>
                </TouchableOpacity>
            </View>

            <View style={{ height: 120 }} />
        </ScrollView>
    );
}

// ─── Styles (Airwallex light theme) ─────────────────────────────────

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.bg },
    header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16 },
    title: { fontSize: 26, fontWeight: "900", color: colors.textPrimary },
    subtitle: { fontSize: 12, color: colors.textSecondary, marginTop: 2 },
    statusBadge: { flexDirection: "row", alignItems: "center", paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1 },
    statusText: { fontSize: 11, fontWeight: "800", letterSpacing: 1 },
    connectedCard: { marginHorizontal: 20, marginBottom: 12, padding: 16, backgroundColor: colors.profitLight, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.profit + "30" },
    connectedTitle: { fontSize: 14, fontWeight: "700", color: colors.profit, marginBottom: 12 },
    infoGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
    infoItem: { minWidth: "45%" },
    infoKey: { fontSize: 9, color: colors.textMuted, letterSpacing: 0.5, marginBottom: 2 },
    infoVal: { fontSize: 14, color: colors.textPrimary, fontWeight: "700" },
    lastTested: { fontSize: 10, color: colors.textMuted, marginTop: 10 },
    disconnectBtn: { marginTop: 12, paddingVertical: 10, borderRadius: radius.md, backgroundColor: colors.lossLight, borderWidth: 1, borderColor: colors.loss + "30", alignItems: "center" },
    disconnectText: { color: colors.loss, fontWeight: "700", fontSize: 13 },
    warningBox: { marginHorizontal: 20, marginBottom: 12, padding: 14, backgroundColor: colors.warningLight, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.warning + "30" },
    warningTitle: { fontSize: 13, fontWeight: "700", color: colors.warning, marginBottom: 6 },
    warningText: { fontSize: 11, color: colors.textSecondary, lineHeight: 17 },
    section: { paddingHorizontal: 20, marginBottom: 16 },
    sectionTitle: { fontSize: 13, fontWeight: "700", color: colors.textSecondary, letterSpacing: 0.5, marginBottom: 10, textTransform: "uppercase" },
    card: { backgroundColor: colors.surface, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border, overflow: "visible" },
    divider: { height: 1, backgroundColor: colors.border },
    inputWrapper: { padding: 14 },
    inputLabel: { fontSize: 11, color: colors.textSecondary, fontWeight: "700", letterSpacing: 0.5, marginBottom: 8 },
    inputRow: { flexDirection: "row", alignItems: "center", backgroundColor: colors.surfaceAlt, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, paddingHorizontal: 14 },
    inputFocused: { borderColor: colors.accent },
    input: { flex: 1, color: colors.textPrimary, fontSize: 15, paddingVertical: 12, fontWeight: "500" },
    eyeBtn: { padding: 4 },
    eyeIcon: { fontSize: 16, color: colors.textMuted },
    dropdown: { backgroundColor: colors.surface, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, marginTop: 4 },
    dropdownItem: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingHorizontal: 16, paddingVertical: 12 },
    dropdownItemActive: { backgroundColor: colors.accentLight },
    dropdownText: { fontSize: 13, color: colors.textSecondary, fontWeight: "500" },
    toggleRow: { flexDirection: "row", alignItems: "center", padding: 16 },
    toggleLabel: { fontSize: 15, fontWeight: "700", color: colors.textPrimary, marginBottom: 4 },
    toggleSub: { fontSize: 11, color: colors.textSecondary },
    liveWarning: { marginHorizontal: 14, marginBottom: 14, padding: 12, backgroundColor: colors.lossLight, borderRadius: radius.md, borderWidth: 1, borderColor: colors.loss + "30" },
    liveWarningText: { color: colors.loss, fontSize: 12, fontWeight: "700", textAlign: "center" },
    step: { flexDirection: "row", alignItems: "flex-start", padding: 14 },
    stepNum: { width: 26, height: 26, borderRadius: 13, backgroundColor: colors.accentLight, borderWidth: 1, borderColor: colors.accent + "40", alignItems: "center", justifyContent: "center", marginRight: 12 },
    stepNumText: { color: colors.accent, fontWeight: "800", fontSize: 12 },
    stepText: { flex: 1, fontSize: 13, color: colors.textSecondary, lineHeight: 22 },
    btnRow: { flexDirection: "row", paddingHorizontal: 20, gap: 10, marginTop: 4 },
    testBtn: { flex: 2, paddingVertical: 17, backgroundColor: colors.accent, borderRadius: radius.lg, alignItems: "center", justifyContent: "center", shadowColor: colors.accent, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 12, elevation: 6 },
    testBtnText: { color: "#FFFFFF", fontWeight: "900", fontSize: 15 },
    saveBtn: { flex: 1, paddingVertical: 17, backgroundColor: colors.surface, borderRadius: radius.lg, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: colors.border },
    saveBtnText: { color: colors.textPrimary, fontWeight: "700", fontSize: 14 },
});

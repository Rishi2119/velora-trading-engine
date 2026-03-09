/**
 * Airwallex-style Design System
 * Clean, minimal, light-mode financial UI
 */

export const colors = {
    // ── Backgrounds ──────────────────────────
    bg: "#F7F8FA",   // page background
    surface: "#FFFFFF",   // card surface
    surfaceAlt: "#F0F2F6",   // secondary surface
    border: "#E8ECF0",   // card borders / dividers
    overlay: "rgba(0,0,0,0.03)",

    // ── Brand / Accent ───────────────────────
    accent: "#007AFF",   // primary blue
    accentLight: "#EBF3FF",   // light blue bg
    accentDark: "#0055CC",   // dark blue hover

    // ── Status ───────────────────────────────
    profit: "#34C759",   // iOS green
    profitLight: "#EDFBF1",
    loss: "#FF3B30",   // iOS red
    lossLight: "#FFF0EF",
    warning: "#FF9500",   // iOS orange
    warningLight: "#FFF6EC",
    info: "#5856D6",   // purple-blue

    // ── Text ─────────────────────────────────
    textPrimary: "#0D0D0D",
    textSecondary: "#6B7280",
    textMuted: "#9CA3AF",
    textInverse: "#FFFFFF",

    // ── Strategy Colors ──────────────────────
    strategy: {
        volatility: "#FF6B35",
        london: "#007AFF",
        trend: "#5856D6",
        reversion: "#34C759",
    },

    // ── Shadow ───────────────────────────────
    shadowColor: "#000000",
};

export const shadow = {
    xs: {
        shadowColor: colors.shadowColor,
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.04,
        shadowRadius: 3,
        elevation: 1,
    },
    sm: {
        shadowColor: colors.shadowColor,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.06,
        shadowRadius: 8,
        elevation: 2,
    },
    md: {
        shadowColor: colors.shadowColor,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 16,
        elevation: 4,
    },
};

export const radius = {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    full: 999,
};

export const spacing = {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
};

export const typography = {
    hero: { fontSize: 40, fontWeight: "800", letterSpacing: -1, color: colors.textPrimary },
    h1: { fontSize: 28, fontWeight: "700", letterSpacing: -0.5, color: colors.textPrimary },
    h2: { fontSize: 20, fontWeight: "700", color: colors.textPrimary },
    h3: { fontSize: 17, fontWeight: "600", color: colors.textPrimary },
    body: { fontSize: 15, fontWeight: "400", color: colors.textSecondary },
    caption: { fontSize: 12, fontWeight: "500", color: colors.textMuted },
    label: { fontSize: 11, fontWeight: "600", letterSpacing: 0.5, color: colors.textMuted, textTransform: "uppercase" },
};

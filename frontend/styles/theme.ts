// styles/theme.ts

// Temas por grupo (usado por ThemeContext)
export const temasPorGrupo = {
  A: {
    background: "#ffffff",
    textPrimary: "#b91c1c",
    textSecondary: "#991b1b",
    primary: "#dc2626",
    badge: "#b91c1c",
    badgeText: "#ffffff",
    card: "#fef2f2",
  },
  B: {
    background: "#f9fafb",
    textPrimary: "#1e3a8a",
    textSecondary: "#4338ca",
    primary: "#facc15",
    badge: "#1e3a8a",
    badgeText: "#facc15",
    card: "#e0e7ff",
  },
};

// Paleta base
export const colors = {
  light: {
    background: "#ffffff",
    textPrimary: "#1f2937",
    textSecondary: "#4b5563",
    primary: "#6366f1",
    badge: "#1e1e1e",
    badgeText: "#d1fae5",
    card: "#ffffff",
    // nuevos tokens
    surface: "#ffffff",
    inputBg: "#f0f0f0",
    textMuted: "#888888",
    divider: "#cccccc",
  },
  dark: {
    background: "#1f1f1f",
    textPrimary: "#f3f4f6",
    textSecondary: "#9ca3af",
    primary: "#8b5cf6",
    badge: "#2c2c2c",
    badgeText: "#a7f3d0",
    card: "#2a2a2a",
    // nuevos tokens
    surface: "#2a2a2a",
    inputBg: "#2b2b2b",
    textMuted: "#A1A1AA",
    divider: "#3f3f46",
  },
};

// Layout base
export const layout = {
  container: {
    flex: 1,
    padding: 20,
    justifyContent: "center",
    alignItems: "center",
  },
};

// Tipografía base
export const typography = {
  heading: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    marginBottom: 8,
  },
};

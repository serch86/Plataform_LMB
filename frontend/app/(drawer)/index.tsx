import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { layout, typography, colors } from "@/styles/theme";
import { useColorScheme } from "@/hooks/useColorScheme";

export default function HomeScreen() {
  const scheme = useColorScheme();
  const themeColors = colors[scheme ?? "light"];

  return (
    <View
      style={[layout.container, { backgroundColor: themeColors.background }]}
    >
      <View style={[styles.badge, { backgroundColor: themeColors.badge }]}>
        <Text style={[styles.badgeText, { color: themeColors.badgeText }]}>
          Reportes de Béisbol Automatizados
        </Text>
      </View>

      <Text style={[styles.title, { color: themeColors.primary }]}>
        Bienvenido al Panel del Equipo
      </Text>

      <Text style={[styles.subtitle, { color: themeColors.textSecondary }]}>
        Visualiza estadísticas, reportes y gestiona tu alineación fácilmente.
      </Text>

      <View style={styles.buttonRow}>
        <TouchableOpacity
          style={[
            styles.primaryButton,
            { backgroundColor: themeColors.primary },
          ]}
        >
          <Text style={[styles.primaryButtonText, { color: "white" }]}>
            Ver Reportes
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.secondaryButton,
            { borderColor: themeColors.textSecondary },
          ]}
        >
          <Text
            style={[
              styles.secondaryButtonText,
              { color: themeColors.textPrimary },
            ]}
          >
            Subir Roster
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsGrid}>
        {[
          { num: "8", label: "Equipos", caption: "Con acceso activo" },
          {
            num: "120",
            label: "Reportes generados",
            caption: "Últimos 30 días",
          },
          { num: "48h", label: "Tiempo de entrega", caption: "Promedio" },
          { num: "95%", label: "Precisión OCR", caption: "En documentos" },
        ].map((item, i) => (
          <View
            key={i}
            style={[styles.statCard, { backgroundColor: themeColors.card }]}
          >
            <Text style={[styles.statNumber, { color: themeColors.primary }]}>
              {item.num}
            </Text>
            <Text
              style={[styles.statLabel, { color: themeColors.textPrimary }]}
            >
              {item.label}
            </Text>
            <Text
              style={[styles.statCaption, { color: themeColors.textSecondary }]}
            >
              {item.caption}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "center",
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginBottom: 20,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: "600",
  },
  title: {
    fontSize: 32,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    textAlign: "center",
    marginBottom: 32,
    paddingHorizontal: 12,
  },
  buttonRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 12,
  },
  primaryButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  primaryButtonText: {
    fontWeight: "600",
  },
  secondaryButton: {
    borderWidth: 1,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  secondaryButtonText: {
    fontWeight: "600",
  },
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    marginTop: 32,
    gap: 16,
  },
  statCard: {
    width: 160,
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 3,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: "bold",
  },
  statLabel: {
    fontSize: 16,
    fontWeight: "600",
    marginTop: 8,
  },
  statCaption: {
    fontSize: 12,
    textAlign: "center",
    marginTop: 4,
  },
});

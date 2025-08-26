import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { layout } from "@/styles/theme";
import { useRouter } from "expo-router";
import { useTheme } from "@/ThemeContext";

const logosPorGrupo: Record<string, any> = {
  A: require("../../assets/images/diablos.png"),
  B: require("../../assets/images/sultanes.png"),
};

export default function HomeScreen() {
  const router = useRouter();
  const { grupo, theme: themeColors } = useTheme();

  console.log("Grupo actual:", grupo);

  return (
    <View
      style={[layout.container, { backgroundColor: themeColors.background }]}
    >
      {grupo && logosPorGrupo[grupo] && (
        <Image
          source={logosPorGrupo[grupo]}
          style={styles.logo}
          resizeMode="contain"
        />
      )}

      <View style={[styles.badge, { backgroundColor: themeColors.badge }]}>
        <Text style={[styles.badgeText, { color: themeColors.badgeText }]}>
          Reportes de Béisbol Automatizados
        </Text>
      </View>

      <Text style={[styles.title, { color: themeColors.primary }]}>
        {grupo === "B"
          ? "Bienvenido al Panel – Sultanes de Monterrey"
          : "Bienvenido al Panel del Equipo"}
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
          onPress={() => router.push("/(drawer)/reportes")}
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
          onPress={() => router.push("/(drawer)/roster")}
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
  logo: {
    width: 100,
    height: 100,
    alignSelf: "center",
    marginBottom: 16,
  },
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

import { View, Text, StyleSheet, TouchableOpacity, Switch } from "react-native";
import { layout, typography } from "@/styles/theme";
import { useUserStore } from "@/store/useUserStore";
import { useTheme } from "@/ThemeContext";

export default function SuscripcionScreen() {
  const { theme: themeColors } = useTheme();
  const { subscriptionStatus, setSubscriptionStatus } = useUserStore();

  const toggleSwitch = () => {
    const nuevoEstado = subscriptionStatus === "activo" ? "inactivo" : "activo";
    setSubscriptionStatus(nuevoEstado);
  };

  const iniciarPago = () => {
    alert("Redirigiendo a Stripe...");
  };

  return (
    <View
      style={[
        layout.container,
        { backgroundColor: themeColors.background, padding: 20 },
      ]}
    >
      <Text
        style={[
          typography.heading,
          styles.title,
          { color: themeColors.primary },
        ]}
      >
        Suscripción del Equipo
      </Text>

      <View style={styles.estadoRow}>
        <Text style={{ color: themeColors.textPrimary, fontSize: 16 }}>
          Estado actual:
        </Text>
        <Text
          style={{
            fontWeight: "bold",
            color: subscriptionStatus === "activo" ? "green" : "red",
            marginLeft: 8,
          }}
        >
          {subscriptionStatus === "activo" ? "Activa" : "Inactiva"}
        </Text>
      </View>

      <View style={styles.switchRow}>
        <Text style={{ color: themeColors.textSecondary }}>Simular estado</Text>
        <Switch
          value={subscriptionStatus === "activo"}
          onValueChange={toggleSwitch}
          thumbColor={
            subscriptionStatus === "activo" ? themeColors.primary : "#ccc"
          }
        />
      </View>

      {subscriptionStatus === "inactivo" && (
        <TouchableOpacity
          style={[styles.button, { backgroundColor: themeColors.primary }]}
          onPress={iniciarPago}
        >
          <Text style={styles.buttonText}>Pagar Suscripción</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  title: {
    fontSize: 24,
    marginBottom: 16,
    textAlign: "center",
  },
  estadoRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
  },
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
  },
  button: {
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 16,
  },
});

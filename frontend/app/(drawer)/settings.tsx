import { View, Text, StyleSheet } from "react-native";
import { layout, typography } from "@/styles/theme";
import { useUserStore } from "@/store/useUserStore";
import { useTheme } from "@/ThemeContext";

export default function SettingsScreen() {
  const { user } = useUserStore();
  const { theme: themeColors } = useTheme();

  return (
    <View
      style={[layout.container, { backgroundColor: themeColors.background }]}
    >
      <Text style={[typography.heading, { color: themeColors.textPrimary }]}>
        Configuración
      </Text>

      <View style={[styles.accountBox, { backgroundColor: themeColors.card }]}>
        <Text
          style={[typography.subtitle, { color: themeColors.textSecondary }]}
        >
          Cuenta
        </Text>
        <Text
          style={{ color: themeColors.textPrimary, fontSize: 16, marginTop: 4 }}
        >
          {user?.email ?? "Sesión no iniciada"}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  accountBox: {
    marginTop: 32,
    padding: 16,
    borderRadius: 8,
  },
});

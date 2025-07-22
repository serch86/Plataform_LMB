import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { useColorScheme } from "@/hooks/useColorScheme";
import { layout, typography, colors } from "@/styles/theme";
import useUserStore from "@/store/useUserStore";

export default function SettingsScreen() {
  const { preference, setColorScheme, colorScheme } = useColorScheme();
  const { user } = useUserStore();
  const themeColors = colors[colorScheme ?? "light"];

  const ThemeOption = ({
    label,
    value,
  }: {
    label: string;
    value: "light" | "dark" | "auto";
  }) => (
    <TouchableOpacity
      onPress={() => setColorScheme(value)}
      style={[
        styles.optionButton,
        {
          borderColor:
            preference === value
              ? themeColors.primary
              : themeColors.textSecondary,
        },
      ]}
    >
      <Text
        style={{
          color:
            preference === value
              ? themeColors.primary
              : themeColors.textPrimary,
          fontWeight: preference === value ? "bold" : "normal",
        }}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View
      style={[layout.container, { backgroundColor: themeColors.background }]}
    >
      <Text style={[typography.heading, { color: themeColors.textPrimary }]}>
        Configuración
      </Text>

      <Text
        style={[
          typography.subtitle,
          { color: themeColors.textSecondary, marginBottom: 12 },
        ]}
      >
        Tema de la aplicación:
      </Text>

      <View style={styles.optionsRow}>
        <ThemeOption label="Claro" value="light" />
        <ThemeOption label="Oscuro" value="dark" />
        <ThemeOption label="Automático" value="auto" />
      </View>

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
  optionsRow: {
    flexDirection: "row",
    gap: 12,
  },
  optionButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderRadius: 8,
  },
  accountBox: {
    marginTop: 32,
    padding: 16,
    borderRadius: 8,
  },
});

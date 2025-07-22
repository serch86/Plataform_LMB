import { View, Text } from "react-native";
import { layout, typography, colors } from "@/styles/theme";
import { useColorScheme } from "@/hooks/useColorScheme";

export default function TypingScreen() {
  const scheme = useColorScheme();
  const themeColors = colors[scheme ?? "light"];

  return (
    <View
      style={[layout.container, { backgroundColor: themeColors.background }]}
    >
      <Text style={[typography.heading, { color: themeColors.textPrimary }]}>
        Typing
      </Text>
      <Text style={[typography.subtitle, { color: themeColors.textSecondary }]}>
        Sección de pruebas de escritura.
      </Text>
    </View>
  );
}

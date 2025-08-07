import { View } from "react-native";
import { useTheme } from "@/ThemeContext";

export default function LogoutScreen() {
  const { theme: themeColors } = useTheme();

  return <View style={{ flex: 1, backgroundColor: themeColors.background }} />;
}

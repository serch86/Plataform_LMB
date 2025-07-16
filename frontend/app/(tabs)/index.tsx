// app/(tabs)/index.tsx
import { View, Text, Button } from "react-native";
import useUserStore from "../../store/useUserStore";
import { useRouter } from "expo-router";

export default function HomeScreen() {
  const user = useUserStore((s) => s.user);
  const clearSession = useUserStore((s) => s.clearSession);
  const router = useRouter();

  const handleLogout = () => {
    clearSession();
    router.replace("/login");
  };

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text>Bienvenido, {user?.name}</Text>
      <Text>{user?.email}</Text>
      <Button title="Cerrar sesión" onPress={handleLogout} />
    </View>
  );
}

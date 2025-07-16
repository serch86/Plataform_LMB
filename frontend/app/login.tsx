import { View, Text, Button } from "react-native";
import { useRouter } from "expo-router";
import useUserStore from "../store/useUserStore";

export default function LoginScreen() {
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const setToken = useUserStore((s) => s.setToken);

  const handleLogin = () => {
    setUser({ name: "Demo User", email: "demo@example.com" });
    setToken("demo-token");
    router.replace("(tabs)");
  };

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text>Login</Text>
      <Button title="Entrar" onPress={handleLogin} />
    </View>
  );
}

import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
} from "react-native";
import { layout, typography, colors } from "@/styles/theme";
import { useRouter } from "expo-router";
import { useGoogleAuth } from "@/lib/auth/google";
import useUserStore from "@/store/useUserStore";
import { useState } from "react";

export default function LoginScreen() {
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const setToken = useUserStore((s) => s.setToken);
  const { promptAsync } = useGoogleAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleEmailLogin = async () => {
    try {
      const res = await fetch("http://192.168.100.8:3000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) throw new Error("Credenciales inválidas");

      const { token, user } = await res.json();
      setUser(user);
      setToken(token);
      router.replace("/(drawer)/inicio");
    } catch (err) {
      Alert.alert("Error", "No se pudo iniciar sesión");
    }
  };

  const handleGoogleLogin = async () => {
    const result = await promptAsync();
    if (result?.type === "success") {
      setUser({ name: "Demo User", email: "demo@example.com" });
      setToken(result.authentication?.accessToken || "");
      router.replace("(drawer)/inicio");
    }
  };

  return (
    <View style={[layout.container, styles.centered]}>
      <View style={styles.card}>
        <Text style={[typography.heading, styles.title]}>Iniciar Sesión</Text>

        <TextInput
          placeholder="Correo electrónico"
          placeholderTextColor="#888"
          style={styles.input}
          autoCapitalize="none"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
        />
        <TextInput
          placeholder="Contraseña"
          placeholderTextColor="#888"
          secureTextEntry
          style={styles.input}
          value={password}
          onChangeText={setPassword}
        />

        <TouchableOpacity style={styles.loginButton} onPress={handleEmailLogin}>
          <Text style={styles.loginText}>Entrar</Text>
        </TouchableOpacity>

        <View style={styles.divider}>
          <View style={styles.line} />
          <Text style={styles.orText}>o</Text>
          <View style={styles.line} />
        </View>

        <TouchableOpacity
          onPress={handleGoogleLogin}
          style={styles.googleButton}
        >
          <Text style={styles.googleText}>Entrar con Google</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: colors.light.background,
  },
  card: {
    backgroundColor: "#fff",
    padding: 24,
    borderRadius: 12,
    width: "90%",
    maxWidth: 400,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 4,
  },
  title: {
    marginBottom: 20,
    textAlign: "center",
  },
  input: {
    backgroundColor: "#f0f0f0",
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    marginBottom: 12,
  },
  loginButton: {
    backgroundColor: colors.light.primary,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  loginText: {
    color: "#fff",
    fontWeight: "600",
    textAlign: "center",
  },
  divider: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  line: {
    flex: 1,
    height: 1,
    backgroundColor: "#ccc",
  },
  orText: {
    marginHorizontal: 12,
    color: "#888",
  },
  googleButton: {
    borderWidth: 1,
    borderColor: colors.light.primary,
    paddingVertical: 12,
    borderRadius: 8,
  },
  googleText: {
    color: colors.light.primary,
    fontWeight: "600",
    textAlign: "center",
  },
});

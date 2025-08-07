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
import { useUserStore } from "@/store/useUserStore";
import { useState, useEffect } from "react";
import * as Linking from "expo-linking";
import { useTheme } from "@/ThemeContext";
import { detectarGrupoDesdeCorreo } from "@/utils/detectarGrupo";
import axios from "axios";

// Ejemplo: usar una variable de entorno para la URL de la API
const API_URL =
  process.env.EXPO_PUBLIC_API_URL || "http://192.168.1.150:3000/api";

export default function Page() {
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const setToken = useUserStore((s) => s.setToken);
  const { promptAsync } = useGoogleAuth();
  const { setGrupo } = useTheme();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const handleUrl = async ({ url }: { url: string }) => {
      if (url) {
        const parsed = Linking.parse(url);
        const error = parsed.queryParams?.error;
        if (error) setErrorMessage(decodeURIComponent(error as string));
      }
    };

    const subscription = Linking.addEventListener("url", handleUrl);

    return () => {
      subscription.remove();
    };
  }, []);

  const handleEmailLogin = async () => {
    if (!email || !password) {
      Alert.alert("Error", "Correo y contraseña son obligatorios");
      return;
    }

    try {
      // Línea de diagnóstico: Imprime la URL antes de la llamada a la API
      const url = `${API_URL}/auth/login`;
      console.log("Intentando conectar a:", url);

      const res = await axios.post(url, {
        email,
        password,
      });

      const { token, user } = res.data;
      setUser(user);
      setToken(token);

      const grupo = detectarGrupoDesdeCorreo(email);
      setGrupo(grupo);

      router.replace("/(drawer)/inicio");
    } catch (err: any) {
      console.error(
        "Error al iniciar sesión con email:",
        err.response?.data || err.message
      );
      Alert.alert(
        "Error",
        err.response?.data?.message || "No se pudo iniciar sesión"
      );
    }
  };

  const handleGoogleLogin = async () => {
    const result = await promptAsync();

    if (result.type === "success" && result.authentication) {
      try {
        const url = `${API_URL}/auth/google`;
        console.log("Intentando conectar con Google a:", url);

        const res = await axios.post(url, {
          accessToken: result.authentication.accessToken,
        });

        const { token, user } = res.data;
        setUser(user);
        setToken(token);

        const grupo = detectarGrupoDesdeCorreo(user.email);
        setGrupo(grupo);

        router.replace("/(drawer)/inicio");
      } catch (err: any) {
        console.error(
          "Error al iniciar sesión con Google:",
          err.response?.data || err.message
        );
        Alert.alert(
          "Error",
          err.response?.data?.message || "No se pudo iniciar sesión con Google"
        );
      }
    } else if (result.type === "cancel") {
      Alert.alert("Inicio de sesión cancelado", "El proceso fue cancelado.");
    } else {
      Alert.alert(
        "Error",
        "No se pudo completar el inicio de sesión con Google."
      );
    }
  };

  return (
    <View style={[layout.container, styles.centered]}>
      <View style={styles.card}>
        <Text style={[typography.heading, styles.title]}>Iniciar Sesión</Text>

        {errorMessage && (
          <Text style={{ color: "red", marginBottom: 12, textAlign: "center" }}>
            {errorMessage}
          </Text>
        )}

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

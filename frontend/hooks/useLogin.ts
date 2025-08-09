// hooks/useLogin.ts
import { useState, useEffect } from "react";
import * as Linking from "expo-linking";
import { Alert } from "react-native";
import { useRouter } from "expo-router";
import { useUserStore } from "@/store/useUserStore";
import { useTheme } from "@/ThemeContext";
import { useGoogleAuth } from "@/lib/auth/google";
import { api } from "@/lib/api";
import { postAuthSuccess } from "@/lib/auth/session";
import { handleAuthError } from "@/lib/errors/auth";
import { isValidEmail, isValidPassword } from "@/utils/validation";

export function useLogin() {
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const setToken = useUserStore((s) => s.setToken);
  const { setGrupo } = useTheme();
  const { promptAsync } = useGoogleAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleUrl = ({ url }: { url: string }) => {
      if (!url) return;
      const parsed = Linking.parse(url);
      const error = parsed.queryParams?.error;
      if (error) setErrorMessage(decodeURIComponent(error as string));
    };
    const sub = Linking.addEventListener("url", handleUrl);
    return () => sub.remove();
  }, []);

  const handleEmailLogin = async () => {
    if (!isValidEmail(email)) {
      Alert.alert("Error", "Formato de correo inválido");
      return;
    }
    if (!isValidPassword(password)) {
      Alert.alert("Error", "La contraseña debe tener al menos 6 caracteres");
      return;
    }

    try {
      setLoading(true);
      const res = await api.post("/auth/login", { email, password });
      const { token, user } = res.data;
      postAuthSuccess({
        user,
        token,
        emailForGroup: email,
        router,
        setUser,
        setToken,
        setGrupo,
      });
    } catch (err: any) {
      handleAuthError(err, "No se pudo iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    const result = await promptAsync();

    if (result.type === "cancel") {
      Alert.alert("Inicio de sesión cancelado", "El proceso fue cancelado.");
      return;
    }
    if (result.type !== "success" || !result.authentication) {
      Alert.alert(
        "Error",
        "No se pudo completar el inicio de sesión con Google."
      );
      return;
    }

    try {
      setLoading(true);
      const res = await api.post("/auth/google", {
        accessToken: result.authentication.accessToken,
      });
      const { token, user } = res.data;
      postAuthSuccess({
        user,
        token,
        emailForGroup: user.email,
        router,
        setUser,
        setToken,
        setGrupo,
      });
    } catch (err: any) {
      handleAuthError(err, "No se pudo iniciar sesión con Google");
    } finally {
      setLoading(false);
    }
  };

  return {
    email,
    setEmail,
    password,
    setPassword,
    errorMessage,
    loading,
    handleEmailLogin,
    handleGoogleLogin,
  };
}

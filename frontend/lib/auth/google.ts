import * as WebBrowser from "expo-web-browser";
import * as Google from "expo-auth-session/providers/google";
import { useEffect } from "react";
import Constants from "expo-constants";
import { useRouter } from "expo-router";
import { Alert } from "react-native";
import useUserStore from "@/store/useUserStore";
import { saveSession } from "@/lib/secureStore"; // ✅ guardar sesión completa

WebBrowser.maybeCompleteAuthSession();

export function useGoogleAuth() {
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const setToken = useUserStore((s) => s.setToken);

  const [request, response, promptAsync] = Google.useAuthRequest({
    clientId: Constants.expoConfig?.extra?.GOOGLE_CLIENT_ID || "",
    scopes: ["profile", "email"],
  });

  useEffect(() => {
    if (response?.type === "success") {
      const { authentication } = response;

      if (!authentication?.accessToken) {
        console.warn("❌ No accessToken recibido");
        Alert.alert("Error", "No se recibió el token de autenticación.");
        return;
      }

      console.log("✅ accessToken:", authentication.accessToken);

      // Validar con backend
      fetch("http://localhost:3000/api/auth/google-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: authentication.accessToken }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (!data?.token) {
            Alert.alert("Error", "No se recibió JWT del servidor.");
            return;
          }

          console.log("✅ JWT:", data.token);
          console.log("👤 Usuario:", data.user);

          // ✅ Guardar sesión completa
          saveSession(data.user, data.token);

          // ✅ Estado global
          setUser(data.user);
          setToken(data.token);

          // ✅ Ir al drawer
          router.replace("/(drawer)/");
        })
        .catch((err) => {
          console.error("❌ Error en el backend:", err);
          Alert.alert("Error", "Fallo al validar sesión con el servidor.");
        });
    } else if (response?.type === "error") {
      console.error("❌ Error en login:", response.error);
      Alert.alert("Error", "Inicio de sesión cancelado o fallido.");
    }
  }, [response]);

  return {
    request,
    promptAsync,
  };
}

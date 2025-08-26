import { useEffect, useState } from "react";
import { View, ActivityIndicator } from "react-native";
import { Slot, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";

import { getSession } from "@/lib/secureStore";
import { useUserStore } from "@/store/useUserStore";
import { ThemeProvider, useTheme } from "@/ThemeContext";
import AuthGate from "@/components/AuthGate";

function useAppBootstrap() {
  const [booted, setBooted] = useState(false);
  const { setUser, setToken, loadSubscriptionStatus } = useUserStore();

  useEffect(() => {
    const load = async () => {
      const session = await getSession();
      if (session?.token) {
        setUser(session.user);
        setToken(session.token);
      }
      await loadSubscriptionStatus();
      setBooted(true);
    };
    load();
  }, []);

  return booted;
}

export default function RootLayout() {
  const booted = useAppBootstrap();
  const { token, subscriptionStatus } = useUserStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (!booted) return;

    const currentSegment = segments[0] ?? "";
    const inAuthGroup = currentSegment === "login";
    const inSubsAllowed =
      currentSegment === "suscripcion" || currentSegment === "logout";

    // AuthGate se encarga de redirigir a /login si no hay token.
    if (token && inAuthGroup) {
      router.replace("/(drawer)/inicio");
    } else if (token && subscriptionStatus === "inactivo" && !inSubsAllowed) {
      router.replace("/(drawer)/suscripcion");
    }
  }, [booted, token, subscriptionStatus, segments]);

  if (!booted) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#666" />
      </View>
    );
  }

  return (
    <ThemeProvider>
      <AuthGate>
        <InnerApp />
      </AuthGate>
    </ThemeProvider>
  );
}

function InnerApp() {
  const { theme } = useTheme();
  return (
    <>
      <Slot />
      <StatusBar style="auto" />
    </>
  );
}

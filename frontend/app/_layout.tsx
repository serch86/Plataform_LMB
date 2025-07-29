import { useEffect, useState } from "react";
import { View, ActivityIndicator } from "react-native";
import { Slot, useRouter, useSegments } from "expo-router";
import { useFonts } from "expo-font";
import {
  DarkTheme,
  DefaultTheme,
  ThemeProvider,
} from "@react-navigation/native";
import { StatusBar } from "expo-status-bar";

import { getSession } from "@/lib/secureStore";
import { useUserStore } from "@/store/useUserStore";
import { useColorScheme } from "@/hooks/useColorScheme";

function useAppBootstrap() {
  const [booted, setBooted] = useState(false);
  const { setUser, setToken } = useUserStore();

  useEffect(() => {
    const load = async () => {
      const session = await getSession();
      if (session?.token) {
        setUser(session.user);
        setToken(session.token);
      }
      setBooted(true);
    };

    load();
  }, []);

  return booted;
}

export default function RootLayout() {
  const booted = useAppBootstrap();
  const colorScheme = useColorScheme();
  const [fontsLoaded] = useFonts({
    SpaceMono: require("@/assets/fonts/SpaceMono-Regular.ttf"),
  });

  const { token } = useUserStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (!booted) return;

    const authRoutes = ["login"];
    const currentSegment = segments[0] ?? "";
    const inAuthGroup = authRoutes.includes(currentSegment);

    if (!token && !inAuthGroup) {
      router.replace("/login");
    }

    if (token && inAuthGroup) {
      router.replace("/(drawer)/inicio");
    }
  }, [booted, token, segments]);

  if (!booted || !fontsLoaded) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#666" />
      </View>
    );
  }

  return (
    <ThemeProvider value={colorScheme === "dark" ? DarkTheme : DefaultTheme}>
      <Slot />
      <StatusBar style="auto" />
    </ThemeProvider>
  );
}

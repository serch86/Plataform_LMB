import Constants from "expo-constants";

export const API_URL: string =
  Constants.expoConfig?.extra?.EXPO_PUBLIC_API_URL || "";

export const GOOGLE_CLIENT_ID: string =
  Constants.expoConfig?.extra?.EXPO_PUBLIC_GOOGLE_CLIENT_ID || "";

if (!API_URL) {
  console.warn("⚠️ EXPO_PUBLIC_API_URL no está definido en app.json o en .env");
}

if (!GOOGLE_CLIENT_ID) {
  console.warn(
    "⚠️ EXPO_PUBLIC_GOOGLE_CLIENT_ID no está definido en app.json o en .env"
  );
}

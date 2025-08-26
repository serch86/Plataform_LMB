import { create } from "zustand";
import AsyncStorage from "@react-native-async-storage/async-storage";

const SUBSCRIPTION_KEY = "subscription_status";

export const useUserStore = create((set) => ({
  user: null,
  token: null,
  subscriptionStatus: "inactivo", // valor por defecto

  setUser: (user) => set({ user }),

  setToken: (token) => {
    set({ token });
    if (token) {
      AsyncStorage.setItem("token", token).catch((error) =>
        console.error("Error al guardar el token:", error)
      );
    } else {
      AsyncStorage.removeItem("token").catch((error) =>
        console.error("Error al eliminar el token:", error)
      );
    }
  },

  setSubscriptionStatus: (status) => {
    set({ subscriptionStatus: status });
    AsyncStorage.setItem(SUBSCRIPTION_KEY, status).catch((error) =>
      console.error("Error al guardar estado de suscripción:", error)
    );
  },

  clearSession: () => {
    set({ user: null, token: null });
    AsyncStorage.removeItem("token").catch((error) =>
      console.error("Error al eliminar el token al cerrar sesión:", error)
    );
  },

  loadToken: async () => {
    try {
      const storedToken = await AsyncStorage.getItem("token");
      if (storedToken) {
        set({ token: storedToken });
        console.log("Token cargado desde AsyncStorage.");
      }
    } catch (error) {
      console.error("Error al cargar el token de AsyncStorage:", error);
    }
  },

  loadSubscriptionStatus: async () => {
    try {
      const storedStatus = await AsyncStorage.getItem(SUBSCRIPTION_KEY);
      if (storedStatus === "activo" || storedStatus === "inactivo") {
        set({ subscriptionStatus: storedStatus });
      }
    } catch (error) {
      console.error("Error al cargar estado de suscripción:", error);
    }
  },
}));

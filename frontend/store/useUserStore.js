import { create } from "zustand";
import AsyncStorage from "@react-native-async-storage/async-storage";

export const useUserStore = create((set) => ({
  user: null,
  token: null,

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
      } else {
        console.log("No se encontró token en AsyncStorage.");
      }
    } catch (error) {
      console.error("Error al cargar el token de AsyncStorage:", error);
    }
  },
}));

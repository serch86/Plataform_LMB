import { create } from "zustand";

const useUserStore = create((set) => ({
  user: null,
  token: null,

  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  clearSession: () => set({ user: null, token: null }),
}));

export default useUserStore;

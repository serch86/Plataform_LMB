import { clearSession } from "@/lib/secureStore";
import useUserStore from "@/store/useUserStore";

export const logout = async () => {
  await clearSession();
  useUserStore.getState().setUser(null);
  useUserStore.getState().setToken(null);
};

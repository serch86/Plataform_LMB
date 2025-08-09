import { clearSession as clearSecureSession } from "@/lib/secureStore";
import { useUserStore } from "@/store/useUserStore";

export async function logout() {
  // Limpia el estado global
  useUserStore.getState().clearSession();
  // Borra sesión del almacenamiento seguro
  await clearSecureSession();
}

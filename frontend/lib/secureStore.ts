import * as SecureStore from "expo-secure-store";
import jwtDecode from "jwt-decode";

// Guardar sesión
export async function saveSession(user: any, token: string) {
  await SecureStore.setItemAsync("session", JSON.stringify({ user, token }));
}

// Obtener sesión valida
export async function getSession() {
  const data = await SecureStore.getItemAsync("session");

  if (!data) return null;

  try {
    const { user, token } = JSON.parse(data);
    const decoded: any = jwtDecode(token);
    const now = Math.floor(Date.now() / 1000);
    const maxAge = 60 * 60 * 24; // 1 dia

    if (
      !decoded.exp ||
      now > decoded.exp ||
      decoded.exp - decoded.iat > maxAge
    ) {
      return null;
    }

    return { user, token };
  } catch {
    return null;
  }
}

// Borrar sesión
export async function clearSession() {
  await SecureStore.deleteItemAsync("session");
}

import { Alert } from "react-native";

/**
 * Maneja errores de autenticación de forma consistente.
 * Muestra mensaje detallado si está disponible, o un mensaje por defecto.
 */
export function handleAuthError(error: unknown, fallbackMessage: string): void {
  const message =
    (error as any)?.response?.data?.message ||
    (error as any)?.message ||
    fallbackMessage;

  console.error("Auth error:", message);
  Alert.alert("Error", message);
}

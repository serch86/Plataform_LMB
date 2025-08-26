/**
 * Valida formato básico de correo electrónico.
 */
export function isValidEmail(email: string): boolean {
  if (!email) return false;
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email.trim());
}

/**
 * Valida longitud mínima de contraseña.
 */
export function isValidPassword(password: string, minLength = 6): boolean {
  if (!password) return false;
  return password.length >= minLength;
}

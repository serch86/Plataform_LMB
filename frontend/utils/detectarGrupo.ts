export function detectarGrupoDesdeCorreo(email: string): "A" | "B" {
  const lower = email.toLowerCase();

  const grupoAEmails = ["test@example.com", "test@diablos.com"];

  if (grupoAEmails.includes(lower)) {
    return "A";
  }

  if (lower.includes("sultanes")) {
    return "B";
  }

  return "A";
}

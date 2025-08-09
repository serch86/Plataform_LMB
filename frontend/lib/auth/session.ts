import { detectarGrupoDesdeCorreo } from "@/utils/detectarGrupo";
import { Router } from "expo-router";
import { saveSession } from "@/lib/secureStore";

export async function postAuthSuccess({
  user,
  token,
  emailForGroup,
  router,
  setUser,
  setToken,
  setGrupo,
}: {
  user: any;
  token: string;
  emailForGroup: string;
  router: Router;
  setUser: (u: any) => void;
  setToken: (t: string) => void;
  setGrupo: (g: string) => void;
}) {
  setUser(user);
  setToken(token);
  await saveSession(user, token);

  const grupo = detectarGrupoDesdeCorreo(emailForGroup);
  setGrupo(grupo);

  router.replace("/(drawer)/inicio");
}

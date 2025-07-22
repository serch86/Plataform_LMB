import { Drawer } from "expo-router/drawer";
import { logout } from "@/lib/auth/logout";
import { useRouter } from "expo-router";
import { useEffect } from "react";

export default function DrawerLayout() {
  const router = useRouter();

  return (
    <Drawer>
      <Drawer.Screen name="inicio" options={{ title: "Inicio" }} />
      <Drawer.Screen name="roster" options={{ title: "Subir Roster" }} />
      <Drawer.Screen name="pagos" options={{ title: "Pagos" }} />
      <Drawer.Screen name="settings" options={{ title: "Configuración" }} />
      <Drawer.Screen
        name="logout"
        options={{ title: "Cerrar Sesión" }}
        listeners={{
          focus: async () => {
            await logout();
            router.replace("/login");
          },
        }}
      />
    </Drawer>
  );
}

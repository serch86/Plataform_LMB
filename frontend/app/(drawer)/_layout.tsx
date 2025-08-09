import { Drawer } from "expo-router/drawer";
import { logout } from "@/lib/auth/logout";
import { useRouter } from "expo-router";
import { useTheme } from "@/ThemeContext";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import {
  DrawerContentScrollView,
  DrawerItemList,
} from "@react-navigation/drawer";
import AuthGate from "@/components/AuthGate";

function CustomDrawerFooter(props: any) {
  const router = useRouter();
  const { theme } = useTheme();

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  return (
    <View style={styles.logoutContainer}>
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={[styles.logoutText, { color: theme.primary }]}>
          Cerrar Sesión
        </Text>
      </TouchableOpacity>
    </View>
  );
}

function CustomDrawerContent(props: any) {
  return (
    <View style={{ flex: 1 }}>
      <DrawerContentScrollView {...props}>
        <DrawerItemList {...props} />
      </DrawerContentScrollView>
      <CustomDrawerFooter {...props} />
    </View>
  );
}

export default function DrawerLayout() {
  const { theme } = useTheme();

  return (
    <AuthGate>
      <Drawer
        screenOptions={{
          drawerActiveTintColor: theme.primary,
          drawerLabelStyle: { fontWeight: "600" },
        }}
        drawerContent={(props) => <CustomDrawerContent {...props} />}
      >
        <Drawer.Screen name="inicio" options={{ title: "Inicio" }} />
        <Drawer.Screen name="roster" options={{ title: "Subir Roster" }} />
        <Drawer.Screen name="reportes" options={{ title: "Reportes" }} />
        <Drawer.Screen name="suscripcion" options={{ title: "Suscripción" }} />
        <Drawer.Screen name="settings" options={{ title: "Configuración" }} />
      </Drawer>
    </AuthGate>
  );
}

const styles = StyleSheet.create({
  logoutContainer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: "#eee",
  },
  logoutButton: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
  },
  logoutText: {
    marginLeft: 16,
    fontSize: 16,
    fontWeight: "600",
  },
});

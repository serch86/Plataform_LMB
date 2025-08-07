import { Link, Stack } from "expo-router";
import { StyleSheet, View } from "react-native";

import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";

// Pantalla para rutas no encontradas (404)
export default function NotFoundScreen() {
  return (
    <View style={{ flex: 1 }}>
      {/* Título visible en la cabecera */}
      <Stack.Screen options={{ title: "Oops!" }} />

      {/* Contenido principal */}
      <ThemedView style={styles.container}>
        <ThemedText type="title">This screen does not exist.</ThemedText>

        {/* Enlace para volver a la pantalla principal */}
        <Link href="/(drawer)/inicio" style={styles.link}>
          <ThemedText type="link">Go to home screen!</ThemedText>
        </Link>
      </ThemedView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  link: {
    marginTop: 15,
    paddingVertical: 15,
  },
});

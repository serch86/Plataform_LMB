import { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { colors, layout, typography } from "@/styles/theme";
import { useTheme } from "@/ThemeContext";

interface RosterItem {
  id: string;
  raw_name: string;
  position: string;
}

interface CoincidenciaItem {
  nombre_roster: string;
  nombre_trackman: string | null;
  coincidencia: boolean;
}

interface PythonMetadata {
  nombre_archivo: string;
  tamano_bytes: number;
  extension_archivo: string;
  tipo: string;
  datos_extraidos?: {
    roster?: RosterItem[];
    coincidencias_trackman?: CoincidenciaItem[];
    [key: string]: any;
  };
  error?: string;
  estado?: string;
  timestamp?: number;
}

export default function ReportesScreen() {
  const [reportes, setReportes] = useState<PythonMetadata[]>([]);
  const { theme: themeColors } = useTheme();

  useEffect(() => {
    const loadReportes = async () => {
      const stored = await AsyncStorage.getItem("reportes");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) {
            const filtrados = parsed
              .filter((item) => {
                return (
                  typeof item === "object" &&
                  item !== null &&
                  typeof item.nombre_archivo === "string" &&
                  typeof item.tamano_bytes === "number" &&
                  typeof item.extension_archivo === "string" &&
                  typeof item.tipo === "string"
                );
              })
              .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
            setReportes(filtrados);
          } else {
            console.warn(
              "El contenido de 'reportes' no es un arreglo:",
              parsed
            );
            setReportes([]);
          }
        } catch (err) {
          console.error("Error al parsear reportes:", err);
          Alert.alert("Error", "No se pudieron leer los reportes guardados.");
          setReportes([]);
        }
      }
    };

    loadReportes();
  }, []);

  const borrarReportes = async () => {
    await AsyncStorage.removeItem("reportes");
    setReportes([]);
    Alert.alert("Limpieza", "Se han borrado los reportes guardados.");
  };

  const renderRoster = (roster: RosterItem[]) => (
    <View style={styles.tableContainer}>
      <Text style={[styles.tableTitle, { color: themeColors.primary }]}>
        Roster
      </Text>
      {roster.map((row, index) => (
        <View key={row.id ?? index} style={styles.tableRow}>
          <Text style={[styles.cell, { flex: 1 }]}>{row.id ?? index}</Text>
          <Text style={[styles.cell, { flex: 3 }]}>{row.raw_name}</Text>
          <Text style={[styles.cell, { flex: 2 }]}>{row.position}</Text>
        </View>
      ))}
    </View>
  );

  const renderCoincidencias = (coincidencias: CoincidenciaItem[]) => (
    <View style={styles.tableContainer}>
      <Text style={[styles.tableTitle, { color: themeColors.primary }]}>
        Coincidencias con Trackman
      </Text>
      {coincidencias.map((item, idx) => (
        <View key={`${item.nombre_roster}-${idx}`} style={styles.tableRow}>
          <Text style={[styles.cell, { flex: 3 }]}>{item.nombre_roster}</Text>
          <Text style={[styles.cell, { flex: 3 }]}>
            {item.nombre_trackman ?? "—"}
          </Text>
          <Text style={[styles.cell, { flex: 1 }]}>
            {item.coincidencia ? "Sí" : "No"}
          </Text>
        </View>
      ))}
    </View>
  );

  return (
    <ScrollView
      style={{ flex: 1 }}
      contentContainerStyle={{
        backgroundColor: themeColors.background,
        padding: 20,
        flexGrow: 1,
      }}
    >
      <Text
        style={[
          typography.heading,
          styles.title,
          { color: themeColors.primary },
        ]}
      >
        Reportes Guardados
      </Text>

      <TouchableOpacity
        onPress={borrarReportes}
        style={[styles.clearButton, { borderColor: themeColors.textSecondary }]}
      >
        <Text
          style={[styles.clearButtonText, { color: themeColors.textSecondary }]}
        >
          Borrar todos los reportes
        </Text>
      </TouchableOpacity>

      {reportes.length === 0 ? (
        <Text style={{ color: themeColors.textSecondary }}>
          No hay reportes disponibles.
        </Text>
      ) : (
        reportes.map((r, i) => (
          <View
            key={i}
            style={[styles.card, { backgroundColor: themeColors.card }]}
          >
            <Text style={styles.label}>
              Nombre: <Text style={styles.value}>{r.nombre_archivo}</Text>
            </Text>
            <Text style={styles.label}>
              Tamaño:{" "}
              <Text style={styles.value}>
                {Math.round(r.tamano_bytes / 1024)} KB
              </Text>
            </Text>
            <Text style={styles.label}>
              Extensión: <Text style={styles.value}>{r.extension_archivo}</Text>
            </Text>
            <Text style={styles.label}>
              Tipo: <Text style={styles.value}>{r.tipo}</Text>
            </Text>
            {r.timestamp && (
              <Text style={styles.label}>
                Fecha:{" "}
                <Text style={styles.value}>
                  {new Date(r.timestamp).toLocaleString()}
                </Text>
              </Text>
            )}

            {r.datos_extraidos?.roster &&
              Array.isArray(r.datos_extraidos.roster) &&
              renderRoster(r.datos_extraidos.roster)}

            {r.datos_extraidos?.coincidencias_trackman &&
              Array.isArray(r.datos_extraidos.coincidencias_trackman) &&
              renderCoincidencias(r.datos_extraidos.coincidencias_trackman)}

            {r.error && (
              <Text style={{ color: "red", marginTop: 8 }}>
                Error: {r.error}
              </Text>
            )}
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  title: {
    fontSize: 24,
    marginBottom: 20,
    textAlign: "center",
  },
  card: {
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
  },
  label: {
    fontSize: 14,
    marginBottom: 4,
  },
  value: {
    fontWeight: "500",
  },
  clearButton: {
    borderWidth: 1,
    borderRadius: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 20,
    alignSelf: "flex-end",
  },
  clearButtonText: {
    fontSize: 12,
  },
  tableContainer: {
    marginTop: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 10,
  },
  tableTitle: {
    fontWeight: "700",
    fontSize: 16,
    marginBottom: 10,
  },
  tableRow: {
    flexDirection: "row",
    marginBottom: 6,
  },
  cell: {
    fontSize: 14,
  },
});

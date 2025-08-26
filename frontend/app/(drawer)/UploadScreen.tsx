import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  Alert,
  ActivityIndicator,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system";
import AsyncStorage from "@react-native-async-storage/async-storage";
import axios from "axios";
import { useRouter } from "expo-router";

import { layout, typography, colors } from "@/styles/theme";
import { useTheme } from "@/ThemeContext";
import { useUserStore } from "@/store/useUserStore";

interface RosterRow {
  id: string;
  raw_name: string;
  position: string;
  title: string;
}

interface Coincidencia {
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
    roster?: RosterRow[];
    coincidencias_trackman?: Coincidencia[];
    [key: string]: any;
  };
  error?: string;
  estado?: string;
  tables?: RosterRow[][];
  timestamp?: number;
}

const API_URL =
  process.env.EXPO_PUBLIC_API_URL || "http://192.168.100.8:3000/api";

export default function UploadScreen() {
  const [file, setFile] = useState<DocumentPicker.DocumentPickerAsset | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PythonMetadata | null>(null);

  const { theme: themeColors } = useTheme();
  const router = useRouter();
  const { subscriptionStatus } = useUserStore();

  useEffect(() => {
    if (subscriptionStatus === "inactivo") {
      router.replace("/(drawer)/suscripcion");
    }
  }, [subscriptionStatus]);

  const allowedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "image/jpeg",
  ];

  const handlePick = async () => {
    const pickerResult = await DocumentPicker.getDocumentAsync({
      type: allowedTypes,
      copyToCacheDirectory: true,
      multiple: false,
    });

    if (pickerResult.canceled) return;

    const fileAsset = pickerResult.assets?.[0];
    if (!fileAsset) return;

    const mimeType = fileAsset.mimeType || "";
    if (!allowedTypes.includes(mimeType)) {
      Alert.alert("Tipo no permitido", "Solo se permiten PDF, Excel y JPG");
      setFile(null);
      return;
    }

    setFile(fileAsset);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    const fileUri = file.uri;
    const fileInfo = await FileSystem.getInfoAsync(fileUri);

    if (!fileInfo.exists) {
      Alert.alert("Error", "El archivo no existe.");
      return;
    }

    const token = await AsyncStorage.getItem("token");
    if (!token) {
      Alert.alert("Error", "Token no encontrado. Por favor, inicie sesión.");
      return;
    }

    const formData = new FormData();
    formData.append("file", {
      uri: fileUri,
      name: file.name || "archivo_desconocido",
      type: file.mimeType || "application/octet-stream",
    } as unknown as Blob);

    try {
      setLoading(true);

      const res = await axios.post(`${API_URL}/ocr/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`,
        },
      });

      const parsedData = res.data;

      console.log("RESPUESTA DEL BACKEND >>>", parsedData);

      const datos_extraidos = {
        ...parsedData.metadata?.datos_extraidos,
      };

      if (Array.isArray(parsedData.tables) && parsedData.tables.length > 0) {
        datos_extraidos.roster = parsedData.tables.flat();
      }

      const nuevoReporte: PythonMetadata = {
        nombre_archivo: parsedData.metadata?.nombre_archivo || "",
        tamano_bytes: parsedData.metadata?.tamano_bytes || 0,
        extension_archivo: parsedData.metadata?.extension_archivo || "",
        tipo: parsedData.metadata?.tipo || "",
        datos_extraidos,
        estado: parsedData.metadata?.estado || "",
        tables: parsedData.tables || [],
        timestamp: Date.now(),
      };

      const almacenados = await AsyncStorage.getItem("reportes");
      const prev = almacenados ? JSON.parse(almacenados) : [];
      await AsyncStorage.setItem(
        "reportes",
        JSON.stringify([nuevoReporte, ...prev])
      );

      setResult(nuevoReporte);

      Alert.alert("Éxito", "Archivo procesado y guardado correctamente");
    } catch (err: any) {
      console.error(
        "Error al subir el archivo:",
        err.response?.data || err.message
      );
      Alert.alert(
        "Error",
        err.response?.data?.error || "Hubo un problema al subir el archivo."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView
      contentContainerStyle={[
        layout.container,
        { backgroundColor: themeColors.background, padding: 20 },
      ]}
    >
      <TouchableOpacity
        onPress={handlePick}
        style={[styles.button, { backgroundColor: themeColors.primary }]}
      >
        <Text style={styles.buttonText}>Seleccionar archivo</Text>
      </TouchableOpacity>

      {file && (
        <TouchableOpacity
          onPress={handleUpload}
          style={[styles.button, { backgroundColor: themeColors.primary }]}
        >
          <Text style={styles.buttonText}>Subir archivo</Text>
        </TouchableOpacity>
      )}

      {loading && (
        <ActivityIndicator size="large" color={themeColors.primary} />
      )}

      {result?.datos_extraidos?.roster && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: themeColors.primary }]}>
            Roster
          </Text>
          <ScrollView style={styles.sublist}>
            {result.datos_extraidos.roster.map((row) => (
              <Text key={row.id} style={styles.itemText}>
                {row.raw_name} - {row.position}
              </Text>
            ))}
          </ScrollView>
        </View>
      )}

      {result?.datos_extraidos?.coincidencias_trackman && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: themeColors.primary }]}>
            Coincidencias con Trackman
          </Text>
          <ScrollView style={styles.sublist}>
            {result.datos_extraidos.coincidencias_trackman.map(
              (item, index) => (
                <Text
                  key={`${item.nombre_roster}-${index}`}
                  style={[
                    styles.itemText,
                    { color: item.coincidencia ? "green" : "red" },
                  ]}
                >
                  {item.nombre_roster}{" "}
                  {item.coincidencia
                    ? `→ ${item.nombre_trackman}`
                    : "(Sin coincidencia)"}
                </Text>
              )
            )}
          </ScrollView>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  button: {
    padding: 12,
    marginVertical: 10,
    borderRadius: 6,
  },
  buttonText: {
    color: "#FFF",
    textAlign: "center",
    fontWeight: "bold",
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 10,
  },
  sublist: {
    maxHeight: 250,
  },
  itemText: {
    fontSize: 14,
    marginBottom: 4,
  },
});

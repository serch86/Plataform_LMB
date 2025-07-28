import React, { useState } from "react";
import {
  View,
  Text,
  Button,
  Alert,
  ActivityIndicator,
  ScrollView,
  Platform,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system";
import AsyncStorage from "@react-native-async-storage/async-storage";
import axios from "axios";

interface PythonMetadata {
  nombre_archivo: string;
  tamano_bytes: number;
  extension_archivo: string;
  tipo: string;
  datos_extraidos?: Record<string, any>;
  error?: string;
  estado?: string;
}

export default function UploadScreen() {
  const [file, setFile] = useState<DocumentPicker.DocumentPickerAsset | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PythonMetadata | null>(null);

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

    if (pickerResult.assets && pickerResult.assets.length > 0) {
      const picked = pickerResult.assets[0];
      if (!allowedTypes.includes(picked.mimeType || "")) {
        Alert.alert("Tipo no permitido", "Solo se permiten PDF, Excel y JPG");
        return;
      }
      setFile(picked);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const fileUri =
      Platform.OS === "ios" ? file.uri.replace("file://", "") : file.uri;

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
    } as any);

    try {
      setLoading(true);
      const res = await axios.post(
        "http://192.168.100.8:3000/api/ocr/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setResult(res.data.metadata);
      Alert.alert("Éxito", "Archivo procesado correctamente");
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
      contentContainerStyle={{
        flexGrow: 1,
        justifyContent: "center",
        alignItems: "center",
        padding: 20,
      }}
    >
      <Button title="Seleccionar archivo" onPress={handlePick} />

      {file && (
        <View style={{ marginTop: 20, width: "100%" }}>
          <Text>Nombre: **{file.name}**</Text>
          <Text>Tamaño: **{Math.round(file.size / 1024)} KB**</Text>
          <Text>Tipo: **{file.mimeType}**</Text>
          <View style={{ marginTop: 20 }}>
            <Button title="Subir archivo" onPress={handleUpload} />
          </View>
        </View>
      )}

      {loading && <ActivityIndicator size="large" style={{ marginTop: 20 }} />}

      {result && (
        <View style={{ marginTop: 30, width: "100%" }}>
          <Text style={{ fontWeight: "bold", fontSize: 18, marginBottom: 10 }}>
            Metadatos Extraídos:
          </Text>

          {result.error ? (
            <Text style={{ color: "red", fontWeight: "bold" }}>
              Error en el procesamiento: {result.error}
            </Text>
          ) : (
            <>
              <Text>• Nombre: **{result.nombre_archivo}**</Text>
              <Text>
                • Tamaño: **{Math.round(result.tamano_bytes / 1024)} KB**
              </Text>
              <Text>• Extensión: **{result.extension_archivo}**</Text>
              <Text>• Tipo detectado: **{result.tipo}**</Text>

              {result.datos_extraidos &&
                Object.keys(result.datos_extraidos).length > 0 && (
                  <View style={{ marginTop: 10 }}>
                    <Text style={{ fontWeight: "bold", marginBottom: 5 }}>
                      Detalles específicos:
                    </Text>
                    {Object.entries(result.datos_extraidos).map(
                      ([key, value]) => (
                        <Text key={key}>
                            {key.replace(/_/g, " ")}: **
                          {typeof value === "object"
                            ? JSON.stringify(value, null, 2)
                            : String(value)}
                          **
                        </Text>
                      )
                    )}
                  </View>
                )}
            </>
          )}
        </View>
      )}
    </ScrollView>
  );
}

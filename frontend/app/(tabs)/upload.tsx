import React, { useState } from "react";
import {
  View,
  Text,
  Button,
  Alert,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system";
import axios from "axios";

export default function UploadScreen() {
  const [file, setFile] = useState<DocumentPicker.DocumentPickerAsset | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    rawText: string;
    matches: string[];
  } | null>(null);

  const handlePick = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/*",
      ],
      copyToCacheDirectory: true,
      multiple: false,
    });

    if (result.assets && result.assets.length > 0) {
      setFile(result.assets[0]);
      setResult(null); // limpia resultado anterior
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const uri = file.uri;
    const formData = new FormData();

    formData.append("file", {
      uri,
      name: file.name,
      type: file.mimeType,
    } as any);

    try {
      setLoading(true);
      const res = await axios.post(
        "http://192.168.100.8:3000/api/ocr/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      setResult(res.data);
      Alert.alert("Éxito", "Archivo procesado correctamente");
    } catch (err) {
      console.error("Error al subir el archivo:", err);
      Alert.alert("Error", "Hubo un problema al subir el archivo");
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
          <Text>Nombre: {file.name}</Text>
          <Text>Tamaño: {Math.round(file.size / 1024)} KB</Text>
          <Text>Tipo: {file.mimeType}</Text>
          <View style={{ marginTop: 20 }}>
            <Button title="Subir archivo" onPress={handleUpload} />
          </View>
        </View>
      )}
      {loading && <ActivityIndicator size="large" style={{ marginTop: 20 }} />}
      {result && (
        <View style={{ marginTop: 30, width: "100%" }}>
          <Text style={{ fontWeight: "bold" }}>Texto detectado:</Text>
          <Text selectable>{result.rawText}</Text>
          <Text style={{ fontWeight: "bold", marginTop: 10 }}>
            Coincidencias:
          </Text>
          {result.matches.length > 0 ? (
            result.matches.map((name, idx) => <Text key={idx}>• {name}</Text>)
          ) : (
            <Text>No se detectaron nombres</Text>
          )}
        </View>
      )}
    </ScrollView>
  );
}

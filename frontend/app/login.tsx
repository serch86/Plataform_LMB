import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
} from "react-native";
import { layout, typography, colors } from "@/styles/theme";
import { useLogin } from "@/hooks/useLogin";

export default function Page() {
  const {
    email,
    setEmail,
    password,
    setPassword,
    errorMessage,
    loading,
    handleEmailLogin,
    handleGoogleLogin,
  } = useLogin();

  return (
    <View style={[layout.container, styles.centered]}>
      <View style={styles.card}>
        <Text style={[typography.heading, styles.title]}>Iniciar Sesión</Text>

        {errorMessage && (
          <Text style={{ color: "red", marginBottom: 12, textAlign: "center" }}>
            {errorMessage}
          </Text>
        )}

        <TextInput
          placeholder="Correo electrónico"
          placeholderTextColor={colors.light.textMuted}
          style={styles.input}
          autoCapitalize="none"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
          editable={!loading}
        />
        <TextInput
          placeholder="Contraseña"
          placeholderTextColor={colors.light.textMuted}
          secureTextEntry
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          editable={!loading}
        />

        <TouchableOpacity
          style={styles.loginButton}
          onPress={handleEmailLogin}
          disabled={loading}
        >
          <Text style={styles.loginText}>Entrar</Text>
        </TouchableOpacity>

        <View style={styles.divider}>
          <View style={styles.line} />
          <Text style={styles.orText}>o</Text>
          <View style={styles.line} />
        </View>

        <TouchableOpacity
          onPress={handleGoogleLogin}
          style={styles.googleButton}
          disabled={loading}
        >
          <Text style={styles.googleText}>Entrar con Google</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: colors.light.background,
  },
  card: {
    backgroundColor: colors.light.surface,
    padding: 24,
    borderRadius: 12,
    width: "90%",
    maxWidth: 400,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 4,
  },
  title: {
    marginBottom: 20,
    textAlign: "center",
  },
  input: {
    backgroundColor: colors.light.inputBg,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    marginBottom: 12,
  },
  loginButton: {
    backgroundColor: colors.light.primary,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  loginText: {
    color: colors.light.surface,
    fontWeight: "600",
    textAlign: "center",
  },
  divider: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  line: {
    flex: 1,
    height: 1,
    backgroundColor: colors.light.divider,
  },
  orText: {
    marginHorizontal: 12,
    color: colors.light.textMuted,
  },
  googleButton: {
    borderWidth: 1,
    borderColor: colors.light.primary,
    paddingVertical: 12,
    borderRadius: 8,
  },
  googleText: {
    color: colors.light.primary,
    fontWeight: "600",
    textAlign: "center",
  },
});

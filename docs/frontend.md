# Planificación del Frontend – Proyecto OCR + Matching

## Objetivo

Desarrollar una interfaz móvil/web que permita a los usuarios autenticarse, subir documentos (imagen, PDF o Excel), recibir resultados del procesamiento OCR y visualizar coincidencias con la base de datos de jugadores/equipos.

---

## Tecnologías

- **React Native (Expo)**: App móvil (iOS/Android)
- **Expo Router**: Navegación basada en estructura de archivos (`app/`)
- **Axios**: Comunicación con backend
- **Zustand**: Estado global (usuario, token, resultados)
- **JWT + OAuth (Google)**: Autenticación

---

## Estructura de Pantallas

### 1. Pantalla de Inicio

- Botones: “Iniciar sesión con Google” / “Acceder con Email”
- Redirección tras login exitoso

### 2. Pantalla Principal

- Botón para subir documento (imagen, PDF o Excel)
- Vista previa del archivo cargado
- Botón “Procesar”

### 3. Pantalla de Resultados

- Lista de nombres detectados por OCR
- Indicador de coincidencia (encontrado / no encontrado)
- Detalles (jugador, equipo, estadísticas)

### 4. Pantalla de Historial

- Lista de documentos cargados anteriormente
- Estado del procesamiento
- Acceso a resultados anteriores

### 5. Pantalla de Perfil / Configuración

- Información del usuario
- Cierre de sesión
- Idioma, preferencias

---

## Flujo General

[Login] → [Subida de archivo] → [Procesamiento OCR y Matching] → [Visualización de resultados]

---

---

## Módulos Clave

1. **Autenticación**

   - Login con Google
   - JWT persistente
   - Middleware de protección en frontend

2. **Subida de Archivos**

   - Selector de archivo (imagen, PDF, Excel)
   - Vista previa
   - Envío al backend

3. **Procesamiento y Visualización**

   - Indicadores de carga o estado
   - Mostrar resultados OCR y coincidencias
   - Acciones sobre cada resultado (ver más)

4. **Gestión de Usuario**

   - Perfil
   - Cierre de sesión
   - Cambio de idioma (opcional)

5. **Historial de Procesos**

   - Lista de cargas pasadas
   - Acceso a resultados antiguos

---

## Seguridad y Experiencia de Usuario

- Validación de archivos antes de subir
- Feedback visual (toast/snackbar) para errores o confirmaciones
- Manejo de token vencido
- Redirección automática si no hay sesión activa

---

## Estado Global con Zustand

### Archivo: `store/useUserStore.js`

Se implementó un store para manejar el estado de sesión del usuario:

- `user`: datos del usuario autenticado.
- `token`: token JWT activo.
- `setUser(user)`: guarda los datos del usuario.
- `setToken(token)`: guarda el token JWT.
- `clearSession()`: cierra sesión limpiando el estado.

---

## Integración con Pantallas

### app/login.tsx

- Al iniciar sesión, se usan `setUser` y `setToken` para guardar un usuario y token simulados.
- Luego se redirige a `(tabs)/` usando `router.replace('(tabs)')`.

### app/(tabs)/index.tsx

- Accede al estado actual del usuario y token desde el store.
- Muestra el nombre del usuario autenticado y su correo.
- Cerrar sesión ejecuta `clearSession()` y se redirige a `/login`.

---

### app/(tabs)/upload.tsx

- Usa `expo-document-picker` para permitir seleccionar archivos:
  - Imágenes (`image/*`)
  - PDFs (`application/pdf`)
  - Excel (`.xlsx`)
- Al seleccionar un archivo, muestra:
  - Nombre del archivo
  - Tamaño
  - Tipo MIME
- Pendiente integración con backend para envío del archivo con `axios`

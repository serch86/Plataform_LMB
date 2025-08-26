# Aplicación Móvil Privada – Resumen

## Objetivo

Permitir a equipos y staff consultar, filtrar y escanear información de reportes desde dispositivos móviles.

## Características Clave

- Autenticación por equipo
- Visualización y filtrado de reportes descargados
- Capacidad offline total
- Escaneo de alineaciones en papel (OCR)
- Gestión de suscripciones (Stripe, MercadoPago)
- Branding dinámico por equipo (logo, colores)
- Sincronización con backend y almacenamiento seguro local

## Funciones Destacadas

- Login seguro (Google OAuth / Email)
- OCR desde cámara compatible offline (Google ML Kit)
- Filtro interactivo para mostrar solo jugadores activos
- Almacenamiento seguro en dispositivo

## Tecnologías

- **Frontend móvil:** React Native (Expo)
- **Estado global:** Zustand v5
- **Navegación:** Expo Router
- **Comunicación backend:** Axios
- **Autenticación:** JWT + OAuth (Google)
- **OCR:** Google ML Kit (offline)
- **Pagos:** Stripe, MercadoPago
- **Opcional:** Firebase (auth, almacenamiento local)

---

# Planificación del Frontend – Proyecto OCR + Matching

## Objetivo

Desarrollar una interfaz móvil/web que permita:

1. Autenticarse
2. Subir documentos (imagen, PDF, Excel)
3. Recibir y visualizar resultados de OCR con coincidencias en la base de datos

---

## Estructura de Pantallas

### 1. Inicio

- Botones: “Iniciar sesión con Google” / “Acceder con Email”
- Redirección tras login

### 2. Principal

- Subida de documento
- Vista previa del archivo
- Botón “Procesar”

### 3. Resultados

- Lista de nombres detectados
- Indicador de coincidencia
- Detalles por jugador/equipo

### 4. Historial

- Lista de documentos previos
- Estado del procesamiento
- Acceso a resultados anteriores

### 5. Perfil / Configuración

- Datos del usuario
- Cierre de sesión
- Preferencias (idioma, tema)

---

## Flujo General

`[Login] → [Subida de archivo] → [Procesamiento OCR + Matching] → [Visualización de resultados]`

---

## Módulos Clave

### 1. Autenticación

- Google OAuth
- JWT persistente
- Middleware de protección

### 2. Subida de Archivos

- Document picker (imagen, PDF, Excel)
- Vista previa
- Envío al backend vía `axios`

### 3. Procesamiento y Visualización

- Indicadores de carga
- Lista OCR + coincidencias
- Acciones sobre resultados

### 4. Gestión de Usuario

- Perfil y cierre de sesión
- Configuración

### 5. Historial

- Documentos previos y resultados

---

## Seguridad y UX

- Validación previa de archivos
- Feedback visual (toast/snackbar)
- Manejo de expiración de token
- Redirección automática si no hay sesión

---

## Estado Global (Zustand)

**Archivo:** `store/useUserStore.js`

- `user`: datos del usuario
- `token`: JWT activo
- `setUser(user)`: guarda usuario
- `setToken(token)`: guarda token
- `clearSession()`: limpia sesión

---

## Integración con Pantallas

- **login.tsx**: guarda `user` y `token` al iniciar sesión, redirige a `(tabs)/`
- **index.tsx**: muestra datos del usuario y permite cerrar sesión
- **upload.tsx**: selecciona archivo, muestra datos, pendiente integración backend

---

## Tema y Personalización

- `utils/detectarGrupo.ts`: define grupo según email
- `ThemeContext.tsx`: contexto de tema por grupo
- `styles/theme.ts`: colores por grupo
- `inicio.tsx`: aplica tema y logo
- `_layout.tsx`: envuelve con `ThemeProvider`

---

## Documentacion de arquitectura

frontend
│
├── .expo/
│
├── app/ Pantallas y navegación principal
│ ├── (drawer)/ Layout y vistas del drawer
│ │ ├── \_layout.tsx
│ │ ├── inicio.tsx
│ │ ├── logout.tsx
│ │ ├── reportes.tsx
│ │ ├── settings.tsx
│ │ ├── suscripcion.tsx
│ │ └── SubirRoster.tsx
│ │
│ ├── \_layout.tsx Layout raíz
│ ├── +not-found.tsx Pantalla 404
│ └── login.tsx Login y guardado de sesión
│
├── assets/ Recursos estáticos
│ ├── fonts/
│ └── images/
│
├── components/ Componentes reutilizables
│ ├── ui/ Componentes de UI base
│ │ ├── iconSymbol.ios.tsx
│ │ ├── IconSymboltsx
│ │ ├── TabBarBackgroud.ios.tsx
│ │ └── TabBarBackground.tsx
│ │
│ ├── AuthGate.tsx
│ ├── Collapsible.tsx
│ ├── ExternalLink.tsx
│ ├── HapticTab.tsx
│ ├── HelloWave.tsx
│ ├── ParallaxScrollView.tsx
│ ├── ThemedText.tsx
│ └── ThemedView.tsx
│
├── constants/ Constantes globales
│ └── Colors.ts
│
├── hooks/ Hooks personalizados
│ ├── useLogin.ts
│ ├── useColorSheme.tsx
│ ├── useColorSheme.web.tsx
│ └── useThemeColor.tsx
│
├── lib/ Funciones de negocio o integración
│ ├── auth/ Autenticación
│ │ ├── errors/
│ │ │ └── auth.js
│ │ ├── session.ts
│ │ ├── google.ts
│ │ └── logout.ts
│ ├── config.ts
│ ├── api.ts Esto unifica el cliente HTTP y evita repetir la URL y headers en cada llamada
│ └── secureStore.ts Manejo seguro de sesión
│
├── node_modules/
│
├── scripts/ Scripts utilitarios
│ └── reset-project.js
│
├── store/ Estado global (Zustand)
│ └── useUserStore.js
│
├── styles/ Estilos globales
│ └── theme.ts
│
├── utils/ Utilidades varias
│ ├── validation.ts
│ └── detectarGrupo.ts
│
├── app.json Configuración Expo
├── eslint.config.js Configuración ESLint
├── expo-env.d.ts Tipos de entorno Expo
├── package-lock.json
├── package.json
├── ThemeContext.tsx Contexto de tema
└── tsconfig.json Configuración TypeScript

Usamos EAS Secrets para almacenar y gestionar variables sensibles de forma segura, evitando que claves privadas se expongan en el cliente o repositorios.

Las variables de entorno se pueden gestionar manualmente creando archivos .env específicos para cada entorno (por ejemplo, .env.development y .env.production). Estos archivos deben ser cargados localmente durante el desarrollo y usados para configurar las builds de forma manual.

Para producción, se recomienda reemplazar las variables en el archivo app.config.ts o usar scripts personalizados que inyecten las variables antes de compilar, asegurando que las claves sensibles no se expongan en el código fuente ni en el cliente.

Se definen perfiles de build en eas.json para cada entorno (desarrollo, staging, producción). Cada perfil especifica las variables de entorno que se inyectarán durante la compilación, permitiendo construir versiones configuradas según el ambiente deseado. Se selecciona el perfil con el comando eas build --profile <perfil>.

Entendido, no usarás servicios externos ni EAS Secrets.

En ese caso:

Gestiona manualmente los .env locales.

Configura scripts para cargar variables según entorno (dev/prod).

Asegúrate de no subir secretos privados al repositorio.

Controla el reemplazo o configuración manual en cada build.

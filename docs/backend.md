# Backend OCR

## Objetivo

Recibir un archivo (PDF, Excel o imagen), extraer nombres de jugadores y equipos mediante OCR, realizar coincidencias contra la base de datos y generar reportes automáticos que se puedan consultar desde la app móvil.

---

## Fase 1: Integración OCR (Imágenes)

### Tareas

- [x] Crear ruta `routes/ocr.js`
- [x] Crear controlador `controllers/ocrController.js`
- [x] Instalar dependencias:
  - `multer` (para subida de archivos)
  - `tesseract.js` (OCR)
  - `sharp` (procesamiento de imágenes)
- [x] Crear carpeta `uploads/` para archivos temporales
- [x] Implementar OCR sobre imágenes (`.jpg`, `.png`)
- [x] Realizar búsqueda en la base de datos (`players`, `teams`)
- [x] Eliminar archivos temporales después de procesar
- [x] Retornar nombres detectados y sus coincidencias
- [x] Procesar imágenes, PDFs y archivos Excel en el mismo controlador (`ocrController.js`)

---

## Fase 2: Soporte para PDFs

### Tareas

- [x] Instalar dependencias: `pdf-parse`
- [x] Detectar si el archivo es PDF y procesarlo apropiadamente
- [x] Extraer texto con `pdf-parse`
- [x] Integrar lógica con flujo de coincidencia de nombres

---

## Fase 3: Soporte para Excel

### Tareas

- [x] Instalar `xlsx` (lectura de archivos Excel)
- [x] Detectar si el archivo es `.xlsx`
- [x] Leer contenido y extraer nombres
- [x] Integrar lógica con flujo de coincidencia de nombres

---

## Fase 4: Reportes y Almacenamiento

### Tareas

- [ ] Generar PDF con los resultados del OCR y matching
- [ ] Subir reporte a Google Drive (Service Account)
- [ ] Guardar metadatos del reporte en base de datos
- [ ] Crear endpoint para listar reportes por equipo
- [ ] Permitir descarga desde app móvil (token + restricción por equipo)

---

## Fase 5: Seguridad y limpieza

### Tareas

- [ ] Validar tipos de archivo aceptados
- [ ] Limitar tamaño máximo
- [ ] Manejar errores y excepciones
- [ ] Asegurar eliminación de archivos temporales
- [ ] Requiere token JWT para acceso a `/api/ocr/upload`

---

## Fase 6: Observabilidad, Logs y Monitoreo

### Tareas

- [ ] Logging detallado (inicio/fin de OCR, resultados, errores)
- [ ] Herramienta de monitoreo (Sentry, LogRocket o GCP Logging)
- [ ] Alertas proactivas ante errores frecuentes
- [ ] Almacenamiento de logs (base de datos o externo)
- [ ] Endpoint para métricas OCR/matching

---

## Fase 7: Filtros y alineaciones

### Tareas

- [ ] Funcionalidad para extraer alineación del día (foto manuscrita)
- [ ] Filtrar reporte completo para mostrar solo jugadores detectados en alineación
- [ ] Opcional: permitir reordenar alineación detectada antes de generar reporte

---

## Fase 8: Acceso y pagos

### Tareas

- [ ] Integración con Stripe o MercadoPago
- [ ] Asociar tokens de sesión a suscripciones activas
- [ ] Validar acceso al OCR o a reportes según plan

---

## Base de Datos

- PostgreSQL + Sequelize
- Tablas:
  - `users` (id, email, password_hash, google_id, role, team_id)
  - `files` (id, name, type, uploaded_by, created_at)
  - `reports` (id, file_id, generated_at, team_id, drive_url)
  - `access_logs`, `folders`, `teams`, etc.

---

## Configuración Inicial

1. Requisitos

- Node.js v22.17.0
- npm
- PostgreSQL
- Cuenta de Google con:
  - Google Drive API habilitada
  - BigQuery habilitado
  - Service Account con credenciales (key.json)

2. Dependencias:

- npm install express cors dotenv
- npm install bcrypt jsonwebtoken
- npm install googleapis
- npm install sequelize pg pg-hstore
- npm install passport passport-google-oauth20
- npm install tesseract.js pdf-parse xlsx

3. Archivo principal:

- server.js

## Variables de Entorno

PORT=3000
DATABASE_URL=
JWT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_CALLBACK_URL=
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=

## Dependencias Utilizadas

| Paquete                     | Función                                       |
| --------------------------- | --------------------------------------------- |
| **express**                 |                                               |
| **cors**                    | Habilita CORS                                 |
| **dotenv**                  | Manejo de variables de entorno                |
| **bcrypt**                  | Encriptar contraseñas                         |
| **jsonwebtoken**            | Manejo de JWT                                 |
| **googleapis**              | SDK oficial de Google (Drive, BigQuery, etc.) |
| **sequelize**               | ORM para PostgreSQL                           |
| **pg / pg-hstore**          | Drivers necesarios para Sequelize             |
| **passport**                | Middleware para autenticación                 |
| **passport-google-oauth20** | Login con Google                              |

---

## Endpoints de la API

| Método | Endpoint                       | Autenticación | Estado       | Notas                                   |
| :----- | :----------------------------- | :------------ | :----------- | :-------------------------------------- |
| `POST` | `/api/auth/register`           | `Ninguna`     | Implementado | Registra un nuevo usuario.              |
| `POST` | `/api/auth/login`              | `Ninguna`     | Implementado | Autentica un usuario existente.         |
| `GET`  | `/api/auth/google`             | `Ninguna`     | No se usará? | Flujo OAuth con Google.                 |
| `GET`  | `/api/auth/google/callback`    | `Ninguna`     | No se usará? | Callback de autenticación Google.       |
| `GET`  | `/api/users/profile`           | `JWT`         | Pendiente    | Perfil del usuario autenticado.         |
| `GET`  | `/api/files`                   | `JWT`         | Implementado | Lista metadatos de archivos.            |
| `POST` | `/api/files`                   | `JWT`         | Implementado | Registra metadatos de un archivo.       |
| `GET`  | `/api/files/view/:driveFileId` | `JWT`         | No se usará? | Visualización desde Google Drive.       |
| `POST` | `/api/ocr/upload`              | `JWT`         | Implementado | Sube un archivo para procesamiento OCR. |
| `GET`  | `/api/data`                    | `JWT`         | Pendiente    | Consulta datos desde BigQuery.          |

---

## Base de Datos

- PostgreSQL + Sequelize
- Tablas:
  - `users` (id, email, password_hash, google_id, role, team_id)
  - `files` (id, name, type, uploaded_by, created_at)
  - `reports` (id, file_id, generated_at, team_id, drive_url)
  - `access_logs`, `folders`, `teams`.

---

## Estructura de archivos

```
backend/
├── config/
│   └── database.js              Conexión Sequelize
│
├── controllers/
│   ├── authController.js        Registro, login
│   ├── fileController.js        Subida, descarga, listado de archivos
│   ├── dataAccessController.js  Logs de acceso (falta este archivo)
│   ├── folderController.js      Manejo de carpetas (falta este archivo)
│   └── ocrController.js         Lógica para el procesamiento OCR (usa tesseract.js)
│
├── middlewares/
│   └── auth.js                  Validaciones JWT
│
├── models/
│   ├── dataAccessLog.js
│   ├── file.js
│   ├── folder.js
│   ├── index.js                Sequelize y relaciones
│   └── user.js
│
├── public/                     Archivos estáticos, incluidos los de tesseract.js (idiomas, workers)
│   └── tesseract-worker.js     Ejemplo de ubicación de archivos de Tesseract.js
│
├── routes/
│   ├── auth.js                 Registro, login
│   ├── files.js                Archivos Drive + BigQuery
│   ├── ocr.js                  Rutas para el módulo OCR
│   └── index.js                Agrega y organiza todas las rutas
│
├── services/                   Integraciones Google
│   ├── drive.js                (Arregla este) Google Drive API con Service Account
│   └── bigquery.js             (Arregla este) BigQuery SDK para consultas
│
├── uploads/                    Archivos temporales subidos para procesamiento (e.g., por OCR)
│
├── .env
├── app.js
├── package.json                Metadatos del proyecto y dependencias
├── server.js                   Punto de entrada, ejecuta servidor + base de datos
└── sync.js                     Sincroniza modelos con DB

```

---

## Notas

- Todo el backend está preparado para funcionar como servicio REST sobre Express.js.
- Todos los endpoints críticos están protegidos por JWT.
- El módulo OCR soporta `.jpg`, `.png`, `.pdf`, `.xlsx`.
- Falta implementar lógica de Google Drive y BigQuery.
- Falta implementar soporte para pagos.

---

# Resumen pdf

## Backend de Automatización de Reportes

- Objetivo:
  Generar automáticamente reportes PDF estructurados con estadísticas actualizadas, a partir de rosters cargados por los administradores.

- Entradas:

Roster en PDF, imagen, Excel o texto.

Estadísticas desde API oficial de liga.

- Proceso:

OCR para extracción de nombres desde documento.

Emparejamiento con datos estadísticos vía API.

Generación de PDF con plantilla predefinida.

Almacenamiento automático en la nube (OneDrive, etc.).

- Salidas:

PDF profesional listo para entrega al equipo.

Metadatos del procesamiento (logs, errores, validaciones).

Tecnologías sugeridas:

Python + Pandas + PDFPlumber (actualmente en uso)

OCR: Google Cloud Vision, AWS Textract o Microsoft AI Builder

Almacenamiento: OneDrive o Azure Blob

API de estadísticas: consumo vía HTTP

## Seguridad en Backend

### Validación y Saneamiento de Datos

- Validar rigurosamente los datos recibidos en rutas y controladores, asegurando tipo, formato y longitud esperados.
- Usar librerías como `express-validator` o `Zod` para validación de entradas.
- Saneamiento para eliminar o neutralizar caracteres que puedan causar inyección SQL o XSS.
- Validar también en middleware antes de la lógica de negocio.

### Protección contra Inyección y Ataques

- Usar Sequelize con consultas parametrizadas para evitar inyección SQL.
- Evitar construcción dinámica de consultas SQL sin parámetros.
- Implementar políticas estrictas de CORS en Express.
- Sanitizar datos antes de enviarlos al cliente para prevenir XSS.

### Autenticación y Autorización

- Proteger rutas con JWT y middleware de autorización.
- Verificar permisos de usuario para acceso o modificación de recursos.
- Manejar correctamente expiración y revocación de tokens JWT.

# Backend OCR

- API backend con Node.js (Express).
- ORM con Sequelize, base de datos relacional (PostgreSQL).
- Autenticación JWT y OAuth con Google.
- Subida de archivos con Multer.
- Procesamiento de archivos con script Python que extrae metadatos.
- Estructura MVC clara.
- Cada archivo subido está asociado a un usuario (owner_id).

## Flujo

```
      [ (Frontend) ]  ← frontend en Expo
              ↓
      [ (routes/) ]
              ↓
    [ (controllers/) ]  ← coordina lógica
              ↓
     [ (services/) ]      ← lógica de negocio compleja
              ↓
        [ (models/) ]
              ↓
     [ BDD (PostgreSQL) ]
```

---

## Documentacion de arquitectura

├── back_app_baseball
│ ├── bin/                    # Ejecutables del entorno virtual Python (no seguir en git)
│ ├── env/                    # Entorno virtual Python (ignorar en git)
│ ├── include/                # Cabeceras para entorno virtual (ignorar)
│ ├── lib/                    # Librerías instaladas en entorno virtual (ignorar)
│ ├── lib64/                  # Librerías 64 bits (ignorar)
│ ├── pyvenv.cfg              # Config del entorno virtual (opcional seguir, útil para recrear entorno)
│ └── requirements.txt        # Dependencias Python del proyecto, importante para instalación
│
├── config/                     # Configuraciones del backend
│ ├── database.js             # Configura Sequelize para conectar a bdd PostgreSQL usando DATABASE_URL.
│ │ # Desactiva logging (logging: false).
│ │ # Configuraciones pool (conexiones y tiempos) comentadas.
│ │ # Opciones conexión SSL comentadas (uso en producción).
│ │ # Prueba conexión, resultado en consola (usar solo en desarrollo).
│ │ # Exporta instancia sequelize para modelos y sincronización.
│ │
│ ├── logger.js # Configura Winston logger con:
│ │ # - Formato JSON con timestamp.
│ │ # - Logs en consola en formato simple.
│ │ # - Opcional: archivos error.log y combined.log para errores y logs generales.
│ │ # Exporta instancia logger para uso centralizado en app y controladores.
│ │  
│ └── passport.js             # autenticación con Google usandopassport-google-oauth20.
│ # Usa variables de entorno para clientID, clientSecret y callbackURL.
│ # Obtiene email del perfil y valida existencia.
│ # Busca usuario con google_id en base de datos.
│ # Si no encuentra usuario, falla autenticación con mensaje USER_NOT_FOUND.
│ # Si encuentra usuario, completa autenticación.
│ # Maneja errores y exporta instancia Passport configurada.
│
├── controllers/ # Controladores, coordinan lógica para rutas
│ ├── authController.js # Controlador para autenticación y gestión de usuarios.
│ │ # Usa bcrypt para hash y validación de contraseñas.
│ │ # Usa jsonwebtoken para emitir tokens JWT con payload { id, role } y expiración de 1 día.
│ │ # Funciones principales: generateJwtToken, register, login, getProfile, googleOAuthCallback.
│ │ # Manejo de errores con respuestas HTTP claras y logs.
│ ├── fileController.js # Controlador para manejo de archivos asociados a usuarios autenticados.
│ │ # Funciones: listFiles, uploadFileRecord, deleteFile.
│ │ # Manejo básico de errores con respuestas HTTP apropiadas.
│ └── ocrController.js # Procesar archivos usando script Python externo.
│ # Ejecuta script Python dentro de entorno virtual especificado.
│ # Usa instancia Sequelize y modelo File para guardar registro del archivo en una transacción.
│ # Maneja errores en la ejecución del script y en el parseo JSON, haciendo rollback en caso de fallo.
│ # Utiliza logger centralizado (Winston) para registrar información, advertencias y errores.
│ # Elimina archivos temporales después del procesamiento.

├── middlewares/               # Middleware para validar peticiones y seguridad
│ └── auth.js                # Middleware de autenticación JWT:
│ # Verifica token en header Authorization.
│ # Valida token con secret, decodifica y agrega usuario a req.user.
│ # Responde 401 si token no existe o expirado, 403 si inválido.
│ # Configura multer para subida de archivos en /uploads con nombre único.
│ # Exporta router para usar en servidor.
│ # Uso de un sistema de registro de errores (Winston)
│
├── models/                    # Modelos ORM Sequelize
│ ├── dataAccessLog.js       # Modelo para logs de acceso a datos.
│ │ # Campos: id UUID, action string, timestamp, metadata JSONB.
│ │ # Tabla: data_access_logs, sin timestamps automáticos.
│ ├── file.js                # Modelo para archivos.
│ │ # Campos: id UUID, drive_file_id, name, type, uploaded_at, bigquery_table.
│ │ # Tabla: files, sin timestamps automáticos.
│ ├── folder.js              # Modelo para carpetas.
│ │ # Campos: id UUID, drive_folder_id, name.
│ │ # Tabla: folders, sin timestamps automáticos.
│ ├── user.js                # Modelo usuario.
│ │ # Campos: id UUID, email, password_hash, google_id, role, language, created_at.
│ │ # Tabla: users, sin timestamps automáticos.
│ └── index.js               # Inicializa Sequelize, modelos y relaciones.
│ # Relaciones: User tiene muchos Files, Logs, Folders.
│ # Exporta objeto db con Sequelize y modelos.
│
├── node_modules/              # Dependencias instaladas Node.js (ignorar en git)
│
├── routes/                    # Definición de rutas y endpoints API
│ ├── auth.js                # Rutas autenticación tradicional y Google OAuth.
│ │ # POST /login, GET /profile, GET /google, GET /google/callback.
│ │ # Uso de Passport y middleware JWT.
│ ├── files.js               # Rutas para gestión de archivos protegidas con JWT.
│ │ # GET lista, POST registra archivo, DELETE elimina registro.
│ ├── ocr.js                 # Ruta POST /upload para subir y procesar archivos OCR.
│ │ # Usa multer y llama a ocrController.processFile.
│ └── index.js               # Monta rutas /auth, /files, /ocr en servidor principal.
│
├── services/                  # Lógica para integraciones externas (APIs)
│ └── drive.js               # Integración con Google Drive usando googleapis.
│ │ # Autenticación con credenciales key.json.
│ │ # Exporta instancia drive para llamadas API.
│ └── python_scripts/ # Nueva ubicación para los scripts de Python.
│ # Se ha movido esta carpeta a services/python_scripts/ para mejorar la organización del proyecto.
│ ├── pycache/           # Archivos compilados Python (ignorar)
│ ├── create_reports.py      # Script para generación de reportes estadísticos de béisbol.
│ │ # Usa pandas, numpy, matplotlib, BigQuery, y módulos batter_tools y pitcher_tools.
│ │ # Normaliza nombres y genera reportes con gráficos y estadísticas.
│ ├── extract_metadata.py    # Extrae metadatos y previsualiza contenido de archivos.
│ │ # Usa clase Tools para procesamiento.
│ │ # Valida extensión y formato, devuelve JSON.
│ │ # Se ha agregado el uso de la biblioteca logging de Python para registrar eventos.
│ ├── nombres_trackman.csv   # Datos estáticos con nombres para comparación.
│ └── tools.py               # Clase Tools con métodos para procesamiento de Excel, CSV, PDF.
│ # Normalización y comparación de nombres, extracción heurística.
│ # Función principal procesar_archivo para integrar procesamiento flexible.  
│
├── uploads/                   # Archivos subidos por usuarios, temporales (ignorar)
│
├── .env                       # Variables de entorno sensibles (no subir a git)
├── app.js                     # Configuración y arranque del backend (punto inicial)
│ # Configura Express, middleware, Passport, monta rutas /api.
│ # Exporta instancia app para server.js o tests.
│ # Se ha agregado la configuración de Winston para el sistema de registro centralizado.
├── server.js                  # Servidor principal (escucha peticiones)
│ # Carga variables entorno, importa app y modelos.
│ # Autentica DB, sincroniza modelos y arranca servidor.
│ # Maneja errores con logs.
│ # Se ha eliminado la sincronización de modelos, ya que se usará un sistema de migraciones.
├── docker-compose.yml         # Orquestación docker para desarrollo/producción
│ # Define servicio backend, expone puerto 8080, monta volumen.
├── Dockerfile                 # Imagen Docker para backend
│ # Base Node.js 20, instala Python3 y pip.
│ # Copia backend, instala dependencias Node y Python.
│ # Expone puerto 8080, inicia con node server.js.
│ # Se ha actualizado para copiar los scripts de Python desde la nueva ruta services/python_scripts/.
├── eng.traineddata            # Archivo de datos entrenados para OCR (necesario)
├── package-lock.json          # Control de versiones de dependencias (importante)
├── package.json               # Dependencias y scripts Node.js
│
└── sync.js                   # Sincroniza modelos Sequelize con base de datos
    # Autentica conexión, usa sync({ alter: true }) para desarrollo.
    # Opciones comentadas para producción y limpieza total.
    # Muestra mensajes de éxito o error en consola.
    # Código autoejecutable asíncrono.
    # Este archivo ha sido marcado como obsoleto. Las migraciones serán gestionadas a través de Sequelize CLI.

Notas importantes para contexto global:
server.js y app.js son punto de entrada.
aqui determinar creo que server abre app

sync.js mantiene actualizados modelos Sequelize.

Consideraciones Futuras
Sistema de Registro de Errores

Despliegue en Google Cloud

Considerado: Se sugiere Cloud Run como la opción más eficiente y moderna, dada la arquitectura basada en Docker.

Alternativas: App Engine y Compute Engine también son opciones viables dependiendo de las necesidades.

## Entornos virtuales y dependencias no se deben subir a git, agregar a .gitignore.

## Base de datos – PostgreSQL + Sequelize

Tablas principales:
users
(id, email, password_hash, google_id, role, team_id)

files
(id, name, type, uploaded_by, created_at)

reports
(id, file_id, generated_at, team_id, drive_url)

Otras: access_logs, folders, teams, etc.

## Migraciones de Base de Datos

- Uso de Sequelize CLI para manejar migraciones incrementales.
- Permite versionar y aplicar cambios al esquema de forma controlada y segura.
- Evita riesgos asociados a sincronización automática (`sync.js`) en producción.
- Incluye comandos para crear, ejecutar y revertir migraciones.
- Cada migración debe estar documentada y revisada en control de versiones.
- Integración en pipeline de despliegue para actualizar la base de datos antes de iniciar el backend.

| Método | Endpoint                       | Auth       | Estado          | Notas                          |
| ------ | ------------------------------ | ---------- | --------------- | ------------------------------ |
| POST   | `/api/auth/register`           | [ ]Ninguna | [x]Implementado | Registro de usuario            |
| POST   | `/api/auth/login`              | [ ]Ninguna | [x]Implementado | Login tradicional              |
| GET    | `/api/auth/google`             | [ ]Ninguna | [ ]No usado     | OAuth inicio                   |
| GET    | `/api/auth/google/callback`    | [ ]Ninguna | [ ]No usado     | Callback OAuth                 |
| GET    | `/api/users/profile`           | [x] JWT    | [ ]Pendiente    | Perfil del usuario autenticado |
| GET    | `/api/files`                   | [x] JWT    | [x]Implementado | Lista archivos                 |
| POST   | `/api/files`                   | [x] JWT    | [x]Implementado | Sube metadatos de archivo      |
| GET    | `/api/files/view/:driveFileId` | [x] JWT    | [ ]No usado     | Ver archivo en Google Drive    |
| POST   | `/api/ocr/upload`              | [x] JWT    | [x]Implementado | Sube y procesa archivo OCR     |
| GET    | `/api/data`                    | [x] JWT    | [ ]Pendiente    | Consulta BigQuery              |

# Checklist General del Proyecto Backend OCR

## Fase 1: Integración OCR (Imágenes)

### Tareas

- [ ] Crear ruta `routes/ocr.js`
- [ ] Crear controlador `controllers/ocrController.js`
- [ ] Instalar dependencias:
  - `multer` (para subida de archivos)
  - `tesseract.js` (OCR)
  - `sharp` (procesamiento de imágenes)
- [ ] Crear carpeta `uploads/` para archivos temporales
- [ ] Implementar OCR sobre imágenes (`.jpg`, `.png`)
- [ ] Realizar búsqueda en la base de datos (`players`, `teams`)
- [ ] Eliminar archivos temporales después de procesar
- [ ] Retornar nombres detectados y sus coincidencias
- [ ] Procesar imágenes, PDFs y archivos Excel en el mismo controlador (`ocrController.js`)

---

## Fase 2: Soporte para PDFs

### Tareas

- [ ] Instalar dependencias: `pdf-parse`
- [ ] Detectar si el archivo es PDF y procesarlo apropiadamente
- [ ] Extraer texto con `pdf-parse`
- [ ] Integrar lógica con flujo de coincidencia de nombres

---

## Fase 3: Soporte para Excel

### Tareas

- [ ] Instalar `xlsx` (lectura de archivos Excel)
- [ ] Detectar si el archivo es `.xlsx`
- [ ] Leer contenido y extraer nombres
- [ ] Integrar lógica con flujo de coincidencia de nombres

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

# Checklist Técnico General

## Autenticación y Seguridad

- [ ] Registro y login con email y contraseña (`bcrypt`, `JWT`)
- [ ] Login con Google OAuth (`passport-google-oauth20`)
- [ ] Protección de rutas con middleware JWT
- [ ] Validación fuerte de entradas (`email`, `password`, etc.)
- [ ] Evitar uso de `console.log` → usar logger como `winston`
- [ ] Verificar propiedad del recurso (`owner_id`) antes de modificar/eliminar
- [ ] Manejo de sesión avanzada (refresh tokens, revocación) — opcional

## Arquitectura y Organización

- [ ] Uso de `controllers/`, `models/`, `routes/`, `services/`
- [ ] Separación clara entre controladores y modelos
- [ ] Mover lógica pesada a `services/`
- [ ] Implementar `utils/` para funciones auxiliares comunes
- [ ] Middleware global de manejo de errores

## Gestión de Archivos

- [ ] Subida con `multer`
- [ ] Procesamiento con Python y eliminación posterior
- [ ] Validar tipo y tamaño de archivo
- [ ] Subida a almacenamiento externo (Google Drive o S3)
- [ ] Registrar `path` o `drive_file_id` en la base de datos

## API REST

- [ ] Endpoints bien organizados en rutas por módulo
- [ ] JWT protegido
- [ ] Documentación técnica de los endpoints (Swagger o markdown)
- [ ] Agregar paginación a `GET /files`
- [ ] Tests de integración (Postman, Jest)

## OCR y procesamiento

- [ ] Script en Python ejecutado por Node
- [ ] Validar estructura de salida JSON del script
- [ ] Integración con `tesseract.js`, `pdf-parse`, `xlsx`
- [ ] Lógica OCR debe migrar a `services/ocrService.js` para mantener el controlador limpio

## DevOps y Producción

- [ ] Uso de `.env` para configuración sensible
- [ ] Configurar Winston como logger principal
- [ ] Soporte para entornos múltiples (`dev`, `prod`)
- [ ] Middleware de manejo centralizado de errores
- [ ] Scripts dev (`start`, `dev`, `sync`) en `package.json`

## Base de Datos

- [ ] Uso de Sequelize con PostgreSQL
- [ ] Relaciones entre modelos (`users`, `files`, etc.)
- [ ] Migraciones con `sequelize-cli` en lugar de `.sync()`
- [ ] Unificación de campos (`owner_id`, `uploaded_by`)
- [ ] Timestamps habilitados en todos los modelos

## Validaciones y UX

- [ ] Validar inputs con `express-validator` o Zod
- [ ] Mensajes de error claros y consistentes
- [ ] Códigos de error específicos para facilitar manejo en frontend
- [ ] Tests unitarios de funciones clave

## Integraciones externas

- [ ] Subida y consulta en Google Drive (API + Service Account)
- [ ] Consultas a BigQuery
- [ ] Carga de credenciales de servicio desde variable segura
- [ ] Endpoint `/api/data` funcional

## Monetización

- [ ] Integrar Stripe o MercadoPago
- [ ] Validar tokens contra suscripciones activas
- [ ] Acceso a OCR y reportes condicionado por plan

## QA y Pruebas

- [ ] Tests unitarios (`jest`)
- [ ] Tests de integración (`supertest`, Postman)
- [ ] Archivos de prueba para todos los formatos soportados
- [ ] Pipeline de CI/CD mínimo (GitHub Actions, etc.)

## Logging y Monitoreo

- El backend usa Winston para logging centralizado con formatos JSON y niveles info, warn, error.
- Los scripts Python incorporan logging con módulo `logging`, enviando salida a archivo y stdout.
- La salida stdout y stderr de scripts Python se captura desde Node.js y se registra en Winston para monitoreo unificado.
- Los logs se almacenan en archivos `error.log` y `combined.log` y también se muestran en consola para desarrollo.
- En producción, se recomienda integrar con sistemas de monitoreo externos (Sentry, Google Cloud Logging, etc.).
- El sistema registra inicio, progreso, errores y resultados de procesamiento de archivos OCR y reportes.

### Flujo de Logs

1. Usuario sube archivo vía API.
2. Backend registra recepción y datos iniciales.
3. Se ejecuta script Python, cuyos logs se capturan y registran en tiempo real.
4. Resultado o error del procesamiento se registra y devuelve al usuario.
5. Eventos y errores críticos se almacenan para auditoría y alertas.

# Mejora en Logging del Backend y Scripts Python

## Objetivo

Centralizar y mejorar el sistema de logging para facilitar la detección y solución de errores, así como el monitoreo continuo.

## Alcance

- Backend Node.js (Winston)
- Ejecución y monitoreo de scripts Python externos

## Detalles

### Backend

- Uso de Winston como logger centralizado con formatos JSON y texto.
- Niveles de log: info, warn, error.
- Logs con timestamps y contexto de petición/usuario.
- Rotación y retención de archivos de log para control de espacio.

### Scripts Python

- Redirigir stdout y stderr al logger del backend o a un sistema de logs centralizado.
- Añadir timestamps y contexto en mensajes de logs Python.
- Manejo de errores y excepciones registradas explícitamente.

### Beneficios

- Facilita depuración y análisis post-mortem.
- Mejora la visibilidad operacional.
- Permite alertas tempranas mediante integración con servicios externos.

## Recomendaciones futuras

- Integrar con plataformas de monitoreo (Stackdriver, Datadog, etc.)
- Automatizar análisis de logs para detección proactiva de incidentes.

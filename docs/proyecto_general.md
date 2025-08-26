# Plan General - OCR Matching App

## Misión

Desarrollar una solución integral que permita a equipos de béisbol automatizar la generación de reportes profesionales basados en sus alineaciones. La app móvil permitirá subir un archivo (foto, PDF o Excel) con nombres de jugadores, ejecutar OCR en el backend, hacer coincidencias con la base de datos y mostrar los resultados o un reporte. Todo el flujo estará diseñado para funcionar offline durante los juegos.

---

# Arquitectura

```
Usuario (App Móvil)
↓
Frontend (React Native + Expo)
↓
Backend (Node.js + Express)
↓
Autenticación (JWT / Google OAuth2)
↓
Base de Datos (PostgreSQL / BigQuery)
↓
OCR + Parsing (Tesseract.js, pdf-parse, xlsx)
↓
Matching contra Base de Datos
↓
Generación de PDF + Almacenamiento en la nube
```

---

---

# Componentes

| Capa               | Herramienta                     | Función principal                         |
| ------------------ | ------------------------------- | ----------------------------------------- |
| **Frontend móvil** | React Native + Expo             | UI de carga, resultados, historial        |
| **Backend**        | Express.js                      | Recepción, OCR, matching, PDF             |
| **OCR**            | tesseract.js / pdf-parse / xlsx | Extraer texto de imagen, PDF, Excel       |
| **Matching**       | PostgreSQL + Sequelize          | Buscar coincidencias en jugadores/equipos |
| **PDF Reports**    | PDFKit / Puppeteer              | Generar reportes formateados              |
| **Auth**           | JWT + Google OAuth2             | Autenticación por equipo/usuario          |
| **Almacenamiento** | OneDrive / GCS / local          | Guardar archivos/reportes OCR             |

---

# Flujo de uso

1. Usuario inicia sesión en la app (Google o email).
2. Sube un archivo del roster (imagen, PDF, Excel).
3. El backend lo procesa con OCR/parsing.
4. Se extraen los nombres y se normalizan.
5. Se hace el matching con la base de datos.
6. Se genera un PDF con los datos coincidentes.
7. El archivo se guarda en la nube y en memoria del equipo, se muestra al usuario.
8. Preguntar ¿El usuario puede consultar historial de envíos?
9.

---

# Fases de desarrollo

## Fase 1: Infraestructura base

- Backend Express + Sequelize
- Frontend React Native + Expo
- Login con JWT
- Manejo de sesiones con Zustand
- Subida de archivos (`multer`, `expo-document-picker`)

## Fase 2: OCR y Parsing

- OCR de imágenes con `tesseract.js`
- PDFs con `pdf-parse`
- Excel con `xlsx`
- Limpieza y normalización de nombres

## Fase 3: Matching y respuesta

- Matching exacto y parcial con SQL
- Tolerancia a variantes con algoritmos tipo Levenshtein
- Generación dinámica de reportes
- API para recibir y responder con los datos procesados

## Fase 4: Frontend móvil

- Navegación con Expo Router
- Pantalla login / perfil
- Pantalla de subida
- Resultados / errores
- Historial de reportes
- Modo offline con caché local

## Fase 5: Almacenamiento y sincronización

- Subida de reportes a OneDrive / GCS
- Descarga previa para uso offline
- Sincronización selectiva por usuario/equipo

## Fase 6: Branding y pagos

- Personalización por equipo (logos, colores)
- Integración con Stripe / MercadoPago
- Gestión de suscripciones y acceso

---

# Mejoras futuras?

| Mejora                 | Tecnología                 | Propósito                      |
| ---------------------- | -------------------------- | ------------------------------ |
| Matching difuso        | Algoritmo tipo Levenshtein | Aumentar tasa de coincidencias |
| Generación de reportes | PDFKit / Puppeteer         | PDF visualmente consistente    |
| Notificaciones push    | Expo Notifications         | Avisos de nuevos reportes      |
| Estadísticas gráficas  | Victory / Recharts         | Visualización avanzada         |
| Distribución privada   | TestFlight / APK Ad Hoc    | Deploy interno                 |
| Logs y monitoreo       | Sentry / LogRocket         | Errores y métricas de uso      |
| Gestión web            | Panel React + Admin SDK    | Administración fuera del móvil |

---

# Mejoras y Consideraciones de Infraestructura

Aquí se documentan las áreas de mejora y consideraciones para backend, despliegue, seguridad y mantenimiento.

## 1. Sincronización de Base de Datos

Ya implementado: migraciones con Sequelize CLI para control incremental y seguro de esquemas.

### 1.1 Gestión de Migraciones con Sequelize CLI

- Las migraciones permiten controlar cambios en el esquema de la base de datos de forma incremental y segura, evitando problemas con sincronizaciones automáticas.
- Cada cambio estructural debe definirse en una migración con funciones `up` y `down`.
- Se versionan y revisan en control de código antes de desplegar.
- Antes de iniciar la app en cualquier entorno, se debe ejecutar:
  ```bash
  npx sequelize-cli db:migrate --env <entorno>
  ```

### En caso de error, se puede revertir con:

- npx sequelize-cli db:migrate:undo --env <entorno>
  Se recomienda integrar este proceso en pipelines CI/CD para despliegues automáticos seguros.

Es clave revisar migraciones en PR y testear en desarrollo antes de producción.

## 2. Logging

Ya implementado: centralización con Winston en backend y captura de logs de scripts Python para monitoreo y depuración.

## 3. Seguridad

Ya implementado: validación y saneamiento de entradas en controladores y middleware para prevenir inyección SQL, XSS y vulnerabilidades.

## 4. Escalabilidad y Despliegue

Pendiente: uso de Cloud Run con acceso seguro a base de datos, autoescalado y configuración stateless.

## 5. Manejo de Archivos Temporales

Pendiente: eliminación robusta de archivos temporales para evitar acumulación y pérdidas.

---

# Documentación de Despliegue

## Ejecución de Migraciones

Antes de iniciar la aplicación en cualquier entorno (desarrollo, prueba o producción), es necesario aplicar las migraciones de la base de datos para asegurar que el esquema esté actualizado.

Comando para aplicar migraciones:

```bash
npx sequelize-cli db:migrate --env <entorno>

Reemplazar `<entorno>` por `development`, `test` o `production` según corresponda.

## Flujo recomendado

- Actualizar el código fuente con la última versión y nuevas migraciones.
- Ejecutar migraciones con el comando anterior.
- Iniciar la aplicación normalmente.

Esto previene inconsistencias entre el código y la base de datos.

## Consideraciones

- Las migraciones deben ser revisadas y aprobadas antes de ser desplegadas
"Por Yael, líder. Otras personalidades no tienen permiso. Decreto oficial del Consorcio de Personalidades de Yael."
- En producción, considerar backups previos a la ejecución.
- Automatizar este paso en scripts o pipelines CI/CD es recomendable.

```

Recibe el archivo.

Ejecuta un script Python que extrae metadatos y hace coincidencias de nombres.

Guarda información del archivo en la base de datos.

Devuelve un JSON con metadatos y resultados del procesamiento.

El frontend:

Permite seleccionar y subir archivos.

Envía el archivo al backend usando la URL configurada.

Procesa la respuesta JSON para mostrar los datos extraídos (roster, coincidencias).

Guarda resultados localmente en AsyncStorage para historial.

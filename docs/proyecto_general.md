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

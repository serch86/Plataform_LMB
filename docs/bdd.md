# Base de Datos `baseball_platform`

usuario: nuevo_usuario@example.com  
contraseña: admin123

---

## Propósito

- Autenticación de usuarios vía correo o Google.
- Asociación de usuarios y archivos a equipos.
- Registro de actividad sobre archivos y reportes.
- Generación y almacenamiento de reportes estructurados.
- Escalabilidad en la nube (Cloud SQL, BigQuery, Google Drive, GCS).

---

## Entidades principales

### `users`

Contiene la información de cada usuario registrado.

| Campo         | Tipo         | Descripción                               |
| ------------- | ------------ | ----------------------------------------- |
| id            | UUID         | Identificador único                       |
| email         | VARCHAR(255) | Correo electrónico único                  |
| password_hash | TEXT         | Contraseña cifrada (si aplica)            |
| google_id     | VARCHAR(255) | ID de Google si autenticado por OAuth     |
| role          | VARCHAR(20)  | Rol del usuario (`admin`, `viewer`, etc.) |
| team_id       | UUID         | FK → `teams.id`                           |
| created_at    | TIMESTAMP    | Fecha de registro                         |

---

### `teams`

Información de cada equipo registrado.

| Campo      | Tipo         | Descripción              |
| ---------- | ------------ | ------------------------ |
| id         | UUID         | Identificador del equipo |
| name       | VARCHAR(255) | Nombre del equipo        |
| logo_url   | TEXT         | Logo personalizado       |
| created_at | TIMESTAMP    | Registro                 |

---

### `files`

Archivos cargados al sistema por los usuarios.

| Campo       | Tipo         | Descripción                           |
| ----------- | ------------ | ------------------------------------- |
| id          | UUID         | Identificador del archivo             |
| name        | VARCHAR(255) | Nombre del archivo                    |
| type        | VARCHAR(50)  | Tipo de archivo (`pdf`, `xlsx`, etc.) |
| uploaded_by | UUID         | FK → `users.id`                       |
| team_id     | UUID         | FK → `teams.id`                       |
| created_at  | TIMESTAMP    | Fecha de carga                        |

---

### `reports`

Reportes PDF generados automáticamente desde archivos.

| Campo        | Tipo      | Descripción                          |
| ------------ | --------- | ------------------------------------ |
| id           | UUID      | ID único del reporte                 |
| file_id      | UUID      | FK → `files.id`                      |
| team_id      | UUID      | FK → `teams.id`                      |
| drive_url    | TEXT      | URL al reporte en Google Drive o GCS |
| generated_at | TIMESTAMP | Fecha de generación del reporte      |

---

### `data_access_logs`

Registro de interacciones de los usuarios con archivos y reportes.

| Campo     | Tipo      | Descripción                                      |
| --------- | --------- | ------------------------------------------------ |
| id        | UUID      | Log único                                        |
| user_id   | UUID      | FK → `users.id`                                  |
| file_id   | UUID      | FK → `files.id` (nullable si aplica a reporte)   |
| report_id | UUID      | FK → `reports.id` (nullable si aplica a archivo) |
| action    | VARCHAR   | Tipo de acción (`upload`, `view`, `download`)    |
| timestamp | TIMESTAMP | Cuándo ocurrió la acción                         |
| metadata  | JSONB     | Información adicional (IP, filtros, etc.)        |

---

## Relaciones

- Un `team` tiene muchos `users`, `files` y `reports`.
- Un `user` puede cargar múltiples `files`.
- Un `file` puede generar múltiples `reports`.
- Un `file` y un `report` pueden tener múltiples accesos en `data_access_logs`.

---

## Consideraciones técnicas

- Uso de `UUID` y `pgcrypto` (`gen_random_uuid()`).
- `JSONB` permite trazabilidad flexible en logs.
- Fechas (`created_at`, `generated_at`, etc.) para auditoría.
- Claves foráneas explícitas para integridad entre usuarios, archivos, equipos y reportes.

---

## Escalabilidad en Google Cloud

| Componente      | Local            | Google Cloud                        |
| --------------- | ---------------- | ----------------------------------- |
| Motor de DB     | PostgreSQL       | Cloud SQL                           |
| Reportes        | Disco local      | Google Drive / Google Cloud Storage |
| Archivos fuente | Local + temporal | sincronización con Drive            |
| Datos tabulares | (local)          | BigQuery                            |

---

## Conexión con Sequelize

Configuración en `.env`:

```
dotenv
DB_USER=postgres
DB_PASS=admin123
DB_NAME=baseball_platform
DB_HOST=localhost
```

---

### modelos/relacione en models/index.js

---

## Pendiente

- [ ] **Ajustar `data_access_logs`** para distinguir entre accesos a archivos (`file_id`) y reportes (`report_id`), garantizando que al menos uno esté presente por registro, pero no ambos simultáneamente si no aplica.

- [ ] **Validar claves foráneas y constraints en Sequelize**, incluyendo:

  - Integridad referencial entre `users`, `teams`, `files`, `reports`.
  - Restricciones de `NOT NULL` donde aplique.
  - Cascadas adecuadas (`onDelete: SET NULL`, `CASCADE`, etc.).

- [ ] **Preparar seed de ejemplo** para poblar la base de datos con:

  - 2–3 equipos (`teams`)
  - 2–3 usuarios por equipo (`users`)
  - Archivos de prueba (`files`)
  - Reportes generados (`reports`)
  - Logs simulados de acceso (`data_access_logs`)

- [ ] **Documentar reglas de acceso** basadas en `role` y `team_id`
  - `admin`: acceso total al sistema.
  - `staff`: acceso completo a su equipo (`team_id`).
  - `viewer`: solo lectura de archivos/reportes de su equipo.

---

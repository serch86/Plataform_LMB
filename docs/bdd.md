# Base de Datos `baseball_platform`

usuario: nuevo_usuario@example.com  
contraseña: admin123

---

## Propósito

- Autenticación de usuarios vía correo o Google.
- Asociación de usuarios, archivos y reportes a equipos.
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

| Campo          | Tipo         | Descripción                                |
| -------------- | ------------ | ------------------------------------------ |
| id             | UUID         | Identificador del archivo                  |
| name           | VARCHAR(255) | Nombre del archivo                         |
| type           | VARCHAR(50)  | Tipo de archivo (`pdf`, `xlsx`, etc.)      |
| uploaded_at    | TIMESTAMP    | Fecha de carga                             |
| bigquery_table | VARCHAR(255) | Nombre de la tabla en BigQuery (si aplica) |

---

### `reports`

Reportes PDF generados automáticamente desde archivos.

| Campo        | Tipo      | Descripción                                           |
| ------------ | --------- | ----------------------------------------------------- |
| id           | UUID      | ID único del reporte                                  |
| file_id      | UUID      | FK → `files.id`                                       |
| team_id      | UUID      | FK → `teams.id`                                       |
| drive_url    | TEXT      | URL al reporte en Google Drive o Google Cloud Storage |
| generated_at | TIMESTAMP | Fecha de generación del reporte                       |

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
- Se asegura `NOT NULL` en claves foráneas esenciales (`owner_id`, `user_id`, etc.).
- Eliminación de columnas y constraints duplicadas para mantener esquema limpio.

---

## Escalabilidad en Google Cloud

| Componente      | Local            | Google Cloud                        |
| --------------- | ---------------- | ----------------------------------- |
| Motor de DB     | PostgreSQL       | Cloud SQL                           |
| Reportes        | Disco local      | Google Drive / Google Cloud Storage |
| Archivos fuente | Local + temporal | Sincronización con Drive            |
| Datos tabulares | (local)          | BigQuery                            |

---

## Conexión con Sequelize

Configuración en `.env`:

DB_USER=postgres
DB_PASS=admin123
DB_NAME=baseball_platform
DB_HOST=localhost

---

### modelos/relaciones en `models/index.js`

Incluye asociaciones con claves foráneas, por ejemplo:

- `User.hasMany(File, { foreignKey: "owner_id" })`
- `File.belongsTo(User, { foreignKey: "owner_id" })`
- Similar para `DataAccessLog` y `Folder`

---

## Pendiente

- [x] Ajustar `data_access_logs` para distinguir accesos a archivos y reportes (nullable y lógica).
- [x] Validar claves foráneas, constraints `NOT NULL` y cascadas (`CASCADE`, `SET NULL`).
- [x] Eliminar columnas no usadas y constraints duplicadas.
- [ ] Preparar seed de ejemplo para equipos, usuarios, archivos, reportes y logs.
- [ ] Documentar reglas de acceso según roles (`admin`, `staff`, `viewer`).

---

## Protocolo para Manejo de Migraciones en Equipo

1. **Nomenclatura clara**

   - Usar nombres descriptivos y con formato: `YYYYMMDDHHMMSS-descripcion-cambio.js`.
   - Ejemplo: `20250807120000-add-role-to-users.js`.

2. **Generación de migraciones**

   - Cada cambio en esquema debe tener una migración nueva.
   - No modificar migraciones ya aplicadas en entornos compartidos.

3. **Revisión y aprobación**

   - Enviar migración a revisión de código (pull request).
   - Validar que la migración crea/actualiza/elimina correctamente sin afectar datos.
   - Confirmar que la migración es reversible (`down` definida).

4. **Ejecución coordinada**

   - Aplicar migraciones primero en entornos de desarrollo local.
   - Coordinar aplicación en staging y producción.
   - Ejecutar con:
     ```bash
     npx sequelize-cli db:migrate
     ```

5. **Control de versiones**

   - Mantener migraciones versionadas en repositorio.
   - No ejecutar migraciones manualmente fuera del flujo establecido.

6. **Rollback y manejo de errores**

   - Definir función `down` para revertir cambios.
   - En caso de fallo, hacer rollback y reportar al equipo.

7. **Documentación y comunicación**

   - Documentar cada migración en su pull request.
   - Comunicar cambios mayores o críticos al equipo.

8. **Testing**

   - Probar migraciones en bases de datos de prueba.
   - Validar integridad y compatibilidad tras migraciones.

9. **Automatización futura**
   - Evaluar integración CI/CD para aplicar migraciones automáticamente en despliegues.

## Uso de Migraciones con Sequelize CLI

- Las migraciones permiten aplicar cambios al esquema de forma incremental y controlada, evitando riesgos de sincronización automática.
- Cada migración se crea con comandos `sequelize-cli` y debe incluir funciones `up` y `down`.
- Se versionan en control de código para mantener el historial de cambios.
- El despliegue en ambientes requiere aplicar migraciones antes de iniciar el backend con:
  ```
  npx sequelize-cli db:migrate
  En caso de error, se puede revertir con:
  ```

-npx sequelize-cli db:migrate:undo

Las migraciones deben revisarse en pull requests y probarse en entorno de desarrollo antes de producción.

Se recomienda integrar migraciones en pipelines CI/CD para despliegues automáticos seguros.

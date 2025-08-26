# Flujo combinado `gui_main.py` + `tools.py`

## Inicio general

- `gui_main.py` arranca `App` (Tkinter).
- `App` importa `Tools` y `_rol_desde_title` de `tools.py`.
- Se gestionan credenciales embebidas (BigQuery).
- Flujo principal: seleccionar archivo → procesar con `Tools.procesar_archivo` → poblar tabla GUI → generar reportes.

---

## Módulo `tools.py`

### Clase `Tools`

- **`__init__`**
  - Define regex para títulos de secciones (catchers, pitchers, etc.).
  - Lista mínima embebida de nombres (`trackman_names`).
  - Cache opcional de nombres (`_bq_names_cache`).
  - Parámetro `preview_rows`.

### Normalización y simplificación

- **`normalizar_nombre`**: elimina tildes, minúsculas, espacios.
- **`_norm_title`**: normaliza título, elimina `:-`.
- **`simplificar_nombre`**: normaliza y descarta palabras ≤2 letras.
- **`_clean_name_reports_style`**: estandariza nombre al estilo `reports`.

### Detección de secciones

- **`_TITULOS`**: conjunto de títulos esperados.
- **`is_header_row`**: detecta fila encabezado por palabras clave.
- **`is_section_title`**: detecta si una celda es título válido.
- **`_titles_in_row`**: devuelve índices y títulos encontrados.
- **`_row_is_mostly_title`**: verifica si fila tiene 1 título y ≤1 celda adicional.
- **`_title_from_position_value`**: asigna título según abreviaturas de posición.

### Extracción de nombres desde Excel

- **`extract_table_sections_from_excel`**: decide modo horizontal o vertical.
- **`_extract_vertical_blocks`**: corta bloques según títulos/headers, limpia, extrae nombres y posiciones.
- **`_extract_horizontal_blocks`**: detecta nombres listados en columnas bajo títulos.
- **`_extraer_nombres_y_posicion`**:
  - Maneja esquemas: `Nombre/Posición`, `First/Last`, solo `nombre`, o heurístico.
  - Devuelve DataFrame `id, raw_name, position, title`.

- **`cargar_excel`**: intenta leer hoja `Roster`; si falla, usa secciones detectadas.

### Extracción de nombres desde PDF

- **`cargar_pdf`**: usa `pdfplumber`.
  - Lee líneas por página.
  - Detecta títulos de sección.
  - Acumula nombres con ≥2 palabras bajo título activo.
  - Devuelve DataFrame `id, raw_name, position=None, title`.

### Nombres desde Trackman

- **`_bq_get_distinct_names`**: consulta BigQuery `trackman_db.trackman_table`, obtiene `Batter` y `Pitcher`.
  - Limpia nombres (`_clean_name_reports_style`).
  - Cachea resultado en `_bq_names_cache`.
- **`cargar_nombres_trackman`**:
  - Si CSV → lee columna `nombre`.
  - Si no, usa BigQuery o fallback lista embebida.
- **`cargar_nombres_trackman_por_rol`**: retorna dict `{batters: [...], pitchers: [...]}`.

### Matching

- **`encontrar_similares`**: compara `nombres_archivo` con `nombres_trackman` usando `rapidfuzz`.
  - Paso 1: compara nombres normalizados.
  - Paso 2: si <umbral, compara nombres simplificados.
  - Retorna lista de dicts con `nombre_roster, nombre_trackman, coincidencia, similitud, algoritmo`.

### Resúmenes y procesamiento

- **`obtener_preview`**: primeras filas en dict.
- **`generar_resumen`**: total y conteo de posiciones.
- **`procesar_archivo`**:
  - Detecta tipo de archivo: Excel → `cargar_excel`, CSV → `_extraer_nombres_y_posicion`, PDF → `cargar_pdf`.
  - Obtiene nombres de Trackman por rol.
  - Construye `roles_by_name` con `_rol_desde_title`.
  - Separa roster en `pitchers`, `batters` (omitiendo staff).
  - Llama `encontrar_similares` por rol.
  - Retorna dict `{archivo: {"tables": preview, "datos_extraidos": {resumen, coincidencias}, "roles_by_name": ...}}`.

---

### Funciones externas en `tools.py`

- **`_rol_desde_title`**: mapea string de título → `"Pitcher" | "Batter/..." | "Staff" | "Unknown"`.
- **`run_tools_from_pdf`**: wrapper para flujo completo con un PDF.
  - Usa `Tools.cargar_pdf`.
  - Asigna roles.
  - Obtiene nombres Trackman por rol.
  - Realiza matching por rol.
  - Retorna dict con listas `*_matched`, `*_unmatched`, y `totals`.

---

## Integración con `gui_main.py` + `reports.py`

1. **Selección de archivo** (`on_select_file`)
   - Llama `Tools.procesar_archivo(path, umbral=self.umbral)` por cada archivo.
   - Consume `res[base]["tables"]`, `res[base]["datos_extraidos"]["coincidencias_trackman"]`, `res[base]["roles_by_name"]`.
   - Pobla `Treeview`:
     - **Matched**: inserta `canonico|rol|score|Matched` para bateadores y pitchers.
     - **Unmatched**: inserta `nombre|rol|—|Unmatched`.
   - Calcula métricas `% capturados` por categoría y actualiza `StringVar`.
   - Habilita botones con `_update_buttons()` según `matched`.

2. **Generación de reportes** (`on_generate_b`, `on_generate_p`)
   - Verifica `self.creds_ok`.
   - Extrae listas:
     - Bateadores: `[m["canonico"] for m in self.batters_matched if m["canonico"]]`.
     - Pitchers: `[m["canonico"] for m in self.pitchers_matched if m["canonico"]]`.
   - Llama a `reports.run_batter_reports(nombres)` o `reports.run_pitcher_reports(nombres)`.
   - Lee y loguea `processed|generated|paths`.

3. **Funciones auxiliares**
   - `_rol_desde_title(title)` mapea títulos a `"Pitcher"|"Batter/..."|"Staff"|"Unknown"`.
   - Matching y preview provienen de `tools.py`.

---

## Flujo interno de `reports.py` usado por la GUI

### Entrada desde la GUI

- **`run_batter_reports(nombres: List[str])`**
  1. Si `df` no se pasa, carga datos con `load_trackman_dataframe()` (BigQuery).
  2. Normaliza `nombres` con `_normalize_person_list`.
  3. Llama `_run_batter_reports_core(df, batter_filter=nombres, work_dir=None, clean_temp=True)`.
  4. Retorna `{"processed": int, "generated": int, "paths": List[str]}`.

- **`run_pitcher_reports(nombres: List[str])`**
  1. Si `df` no se pasa, carga datos con `load_trackman_dataframe()` (BigQuery).
  2. Normaliza `nombres` con `_normalize_person_list`.
  3. Llama `_run_pitcher_reports_core(df, pitcher_filter=nombres, work_dir=None, clean_temp=True)`.
  4. Retorna `{"processed": int, "generated": int, "paths": List[str]}`.

### Carga y limpieza de datos

- **`load_trackman_dataframe(query=BQ_DEFAULT_QUERY)`**
  - Ejecuta consulta en `baseballlmb.trackman_db.trackman_table` (años: Invierno/Verano 2024–2025).
  - Convierte a DataFrame con `bigquery_storage` si está disponible.
  - Limpia nombres con `clean_name` en columnas `Batter` y `Pitcher`.
  - Retorna `df` con columnas de juego (p.ej., `ExitSpeed`, `AutoPitchType`, `fecha_carga`, etc.).

### Generación de reportes de bateadores

- **`_run_batter_reports_core(df, batter_filter, work_dir, clean_temp)`**
  1. Filtra `df` por `Batter.isin(batter_filter)` si se provee.
  2. Valida registros: `BatterId` no nulo y `fecha_carga` válida.
  3. Si vacío: limpia directorio (`clean_directory("Batter")`) y retorna `processed=0`.
  4. Calcula tabla de estadísticas con `bt.create_stats_table(df_games)`.
  5. Itera `nombres` (índice de `df_stats`) y para cada uno ejecuta:
     - `bt.create_report_full(batter_name, df_stats, df_games, dict_short=dict_baseball_teams_short, work_dir)`.
     - Acumula rutas devueltas en `paths`.
  6. Si `clean_temp`: `clean_directory("Batter")`.
  7. Retorna `{"processed": len(nombres), "generated": count, "paths": artefactos}`.

### Generación de reportes de lanzadores

- **`_run_pitcher_reports_core(df, pitcher_filter, work_dir, clean_temp)`**
  1. Filtra `df` por `Pitcher.isin(pitcher_filter)` si se provee.
  2. Restringe `BatterSide` a `["Left","Right"]`, exige `Pitcher` y `fecha_carga` válidos.
  3. Si vacío: limpia directorio (`clean_directory("Pitcher")`) y retorna `processed=0`.
  4. Prepara `df_table` y traduce `AutoPitchType` con `dict_launch`.
  5. Define condiciones:
     - `1er Pitcheo`: `PitchofPA == 1`
     - `General`: `True`
     - `2 Strikes`: `Strikes == 2`
  6. Agrupa por condición: `groupby(["Pitcher","BatterSide","AutoPitchType"]).size().unstack(1)` y guarda en `dict_df_cond`.
  7. Itera `name_pitchers` y para cada uno ejecuta:
     - `pt.create_report_full(pitcher_name, dict_df_cond, dict_cond, dict_short=dict_baseball_teams_short, df_table, work_dir)`.
     - Acumula rutas en `paths`.
  8. Si `clean_temp`: `clean_directory("Pitcher")`.
  9. Retorna `{"processed": len(name_pitchers), "generated": count, "paths": artefactos}`.

### Utilidades y catálogos

- **`clean_name(name)`**: normaliza nombres (title-case sin acentos).
- **`_normalize_person_list(names)`**: aplica `clean_name` y elimina duplicados.
- **`clean_directory(base_subdir, base_path=None)`**: elimina `.png` residuales del subdirectorio de reportes.
- **`dict_baseball_teams` / `dict_baseball_teams_short`**: catálogos de equipos usados en etiquetas y rutas de reportes.

### Dependencias de generación

- **`batter_tools` (`bt`)**:
  - `create_stats_table(df_games)`.
  - `create_report_full(...)` para artefactos de bateadores.
- **`pitcher_tools` (`pt`)**:
  - `create_report_full(...)` para artefactos de lanzadores.

## Integración de `reports.py`

## Módulo `pitcher_tools.py`

### Carga desde BigQuery

- **`_external_load_pitcher_stats()`**  
  Carga desde la tabla `trackman_db.pitchers_stats_2025`. Retorna un `DataFrame` con columnas relevantes para el análisis de lanzadores:
  - `Pitcher`, `PitcherTeam`, `AutoPitchType`, `RelSpeed`, `SpinRate`, `BatterSide`, `PlateLocSide`, `PlateLocHeight`, `InducedVertBreak`, `HorzBreak`, `Date`, `fecha_carga`, `id_path`, `auto_pitch_type_2`.

### Utilidades de datos

- **`get_last_games(df, pitcher)`**: retorna últimos 5 juegos disponibles para un lanzador.
- **`get_perc_shot(pitcher, df_perc)`**: extrae % de uso por tipo de lanzamiento.
- **`get_range_mean(pitcher, df)`**: retorna DataFrame con columnas `rango`, `mean`, `Spin` para el lanzador.
- **`get_table_1(t1, t2)`**: fusiona % uso (`t1`) con rangos (`t2`), produce tabla ordenada.
- **`_ensure_dir(path)`**: crea directorios si no existen.

### Visualizaciones

- **`scatter_pitcher(df, pitcher, auto_all, colours)`**: gráfico de dispersión `InducedVertBreak` vs `HorzBreak` coloreado por `AutoPitchType`.
- **`pie_charts(dict_df_cond, dict_cond, pitcher, side)`**:
  - Tres gráficos tipo pastel por condición (`1er Pitcheo`, `General`, `2 Strikes`).
  - Muestra distribución de tipos de pitcheos (`AutoPitchType`) por lado del bateador (`Left`, `Right`).
- **`pitcher_view_scatter(df, pitcher, side, colours)`**:
  - Densidades KDE de zona de strike por tipo de lanzamiento agrupado (`auto_pitch_type_2`).
  - Diferenciado por lado (`Left`, `Right`), muestra los últimos 100 lanzamientos.

### Estilos y exportación

- **`create_style_launcherbyteam(df)`**: aplica estilos visuales (HTML) a tabla de uso/rango.
- **`from_df_to_tablepng(dir, df_style, name)`**: convierte tabla estilizada a imagen `.png` (usa `dataframe_image` y `html2image`).
- **`save_fig(dir, fig, name, dpi=200)`**: guarda figuras `matplotlib` como `.png`.
- **`create_report(pitcher, team, dir_images, tt, dict_short)`**:
  - Ensambla PDF con secciones visuales (`scatter`, `pies`, `tabla`).
  - Usa `fpdf`. Inserta imágenes solo si existen.

### Generación de reporte completo

- **`create_report_full(pitcher_name, dict_df_cond, dict_cond, dict_short, df_table=None, work_dir=None)`**:
  1. Si `df_table` no se provee, carga datos desde BigQuery.
  2. Extrae últimos juegos para el lanzador (`get_last_games`).
  3. Determina equipo (`PitcherTeam`) más reciente.
  4. Define rutas de trabajo `base_dir`, `dir_images`.
  5. Si no hay datos: genera PDF mínimo (`create_report`).
  6. Si hay datos:
     - Calcula:
       - % uso (`df_perc`, `get_perc_shot`)
       - rangos (`df_range_mean_2`, `get_range_mean`)
     - Genera y guarda visualizaciones:
       - Tabla combinada (`get_table_1` → PNG).
       - Gráfico `scatter_mov`.
       - `pie_left` y `pie_right`.
       - Densidades `scatter_left` y `scatter_right`.
     - Llama `create_report(...)` con altura adaptada (`tt`) según cantidad de tipos de pitcheos.
  7. Devuelve ruta al PDF final.

### Utilidades

- **`clean_name(name)`**: normaliza nombres para uso consistente.
- **`clean_directory(base_subdir, base_path=None)`**: limpia `.png` residuales en `BaseballBatterPitcherReports/<subdir>`.
- **`_normalize_person_list(names)`**: normaliza y deduplica listas de nombres.

### Catálogos

- **`dict_baseball_teams` / `dict_baseball_teams_short`**: mapeos de equipos para rotulación en reportes.

### Carga de datos (BigQuery)

- **`BQ_DEFAULT_QUERY`**: consulta base a `baseballlmb.trackman_db.trackman_table` (temporadas 2024–2025).
- **`load_trackman_dataframe(query=BQ_DEFAULT_QUERY)`**:
  - Ejecuta consulta.
  - Limpia columnas `Batter` y `Pitcher` con `clean_name`.
  - Retorna `pd.DataFrame` con juegos filtrados.

### Núcleo de generación: Bateadores

- **`_run_batter_reports_core(df, batter_filter=None, work_dir=None, clean_temp=True)`**:
  - Filtra por `batter_filter` si aplica.
  - Depura filas: `BatterId` no nulo y `fecha_carga` válida.
  - Calcula stats con `bt.create_stats_table(df_games)`.
  - Itera nombres índice y genera reporte con  
    `bt.create_report_full(batter_name, df_stats, df_games, dict_short, work_dir)`.
  - Limpia temporales con `clean_directory("Batter", base)`.
  - Retorna `{"processed", "generated", "paths"}`.

### Núcleo de generación: Pitchers

- **`_run_pitcher_reports_core(df, pitcher_filter=None, work_dir=None, clean_temp=True)`**:
  - Filtra por `pitcher_filter` si aplica.
  - Depura filas: `BatterSide` en `{"Left","Right"}`, `Pitcher` no nulo, `fecha_carga` válida.
  - Normaliza `AutoPitchType` con `dict_launch`.
  - Define condiciones: `1er Pitcheo`, `General`, `2 Strikes`; agrupa para tablas.
  - Para cada lanzador genera con  
    `pt.create_report_full(pitcher_name, dict_df_cond, dict_cond, dict_short, df_table, work_dir)`.
  - Limpia temporales con `clean_directory("Pitcher", base)`.
  - Retorna `{"processed", "generated", "paths"}`.

### API pública usada por la GUI

- **`run_batter_reports(arg1, df=None, work_dir=None, clean_temp=True)`**:
  - Si `arg1` es `DataFrame` → llama `_run_batter_reports_core(df)`.
  - Si `arg1` es `List[str]` → carga `df` con `load_trackman_dataframe()` y filtra por nombres normalizados (`_normalize_person_list`).
  - Retorna `{"processed","generated","paths"}`.

- **`run_pitcher_reports(arg1, df=None, work_dir=None, clean_temp=True)`**:
  - Si `arg1` es `DataFrame` → llama `_run_pitcher_reports_core(df)`.
  - Si `arg1` es `List[str]` → carga `df` con `load_trackman_dataframe()` y filtra por nombres normalizados.
  - Retorna `{"processed","generated","paths"}`.

### Flujo GUI ↔ Reports

1. **Desde `on_select_file`**:
   - Obtiene `canonico` por jugador en `matched` (separados por rol).

2. **`on_generate_b`**:
   - Construye `nombres = [m["canonico"] ...]`.
   - Llama `reports.run_batter_reports(nombres)`:
     - Internamente carga BigQuery (`load_trackman_dataframe`).
     - Filtra por `nombres` y genera con `bt.create_stats_table` + `bt.create_report_full`.
     - Limpia directorio `Batter` si `clean_temp=True`.
   - Lee `processed | generated | paths` y los registra en log.

3. **`on_generate_p`**:
   - Construye `nombres = [m["canonico"] ...]`.
   - Llama `reports.run_pitcher_reports(nombres)`:
     - Internamente carga BigQuery.
     - Prepara `dict_df_cond` y genera con `pt.create_report_full`.
     - Limpia directorio `Pitcher` si `clean_temp=True`.
   - Lee `processed | generated | paths` y los registra en log.

### Punto de entrada adicional

- **`main(df=None, query=BQ_DEFAULT_QUERY, batter_filter=None, pitcher_filter=None, work_dir=None, clean_temp=True)`**:
  - Carga `df` si no se provee.
  - Ejecuta núcleos de bateador y lanzador con filtros opcionales.
  - Retorna resumen:
    - `{"batter": {"processed","generated","paths"}, "pitcher": {...}}`.

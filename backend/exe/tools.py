import os
import pandas as pd
import unicodedata
import re
from typing import List, Dict, Optional, Tuple
import rapidfuzz
from itertools import zip_longest
import pdfplumber
import logging

# BigQuery
from google.cloud import bigquery
import google.auth
from google.cloud import bigquery_storage

# Logger del módulo
logger = logging.getLogger(__name__)


class Tools:
    def __init__(self, preview_rows: int = 5):
        # borrar log
        logger.info("Inicializando clase Tools.")
        self.preview_rows = preview_rows
        # Acepta variantes con ":" o "-" al final
        self.section_title_pattern = re.compile(
            r"^(catchers|pitchers|infielders|outfielders|cuerpo\s*t[eé]cnico|roster)[:\-]?$",
            re.IGNORECASE
        )

        # Lista mínima embebida SOLO como último recurso si falla BigQuery y no se pasa CSV
        self.trackman_names: List[str] = [
            "javier mireles",
            "javier contreras",
        ]

        # Cache opcional de nombres desde BigQuery por rol
        self._bq_names_cache: Optional[Dict[str, List[str]]] = None
        # borrar log
        logger.info("Clase Tools inicializada.")

    # === normalizar y simplificar ===
    def normalizar_nombre(self, nombre: str) -> str:
        # borrar log
        logger.debug(f"Normalizando nombre: '{nombre}'")
        nombre = unicodedata.normalize("NFKD", nombre)
        nombre = "".join(c for c in nombre if not unicodedata.combining(c))
        normalized_name = " ".join(nombre.strip().lower().split())
        # borrar log
        logger.debug(f"Nombre normalizado a: '{normalized_name}'")
        return normalized_name

    def _norm_title(self, s: str) -> str:
        # borrar log
        logger.debug(f"Normalizando título: '{s}'")
        s = unicodedata.normalize("NFKD", str(s))
        s = "".join(c for c in s if not unicodedata.combining(c))
        norm_title = " ".join(s.strip().lower().split())
        norm_title = norm_title.rstrip(":-").strip()
        # borrar log
        logger.debug(f"Título normalizado a: '{norm_title}'")
        return norm_title

    def simplificar_nombre(self, nombre: str) -> str:
        # borrar log
        logger.debug(f"Simplificando nombre: '{nombre}'")
        nombre = self.normalizar_nombre(nombre)
        partes = nombre.split()
        partes_filtradas = [p for p in partes if len(p) > 2]
        simplified_name = " ".join(partes_filtradas)
        # borrar log
        logger.debug(f"Nombre simplificado a: '{simplified_name}'")
        return simplified_name

    # Limpieza de nombres compatible con reports.clean_name
    @staticmethod
    def _clean_name_reports_style(name: str) -> str:
        # borrar log
        logger.debug(f"Limpiando nombre estilo reports: '{name}'")
        if not name:
            # borrar log
            logger.debug("Nombre vacío, devolviendo 'Sin_nombre'.")
            return "Sin_nombre"
        parts = [p.strip() for p in str(name).split(",")]
        rearranged = f"{parts[-1]} {parts[0]}".strip() if len(parts) >= 2 else parts[0]
        rearranged = " ".join(rearranged.title().split())
        normalized = unicodedata.normalize("NFKD", rearranged)
        cleaned_name = "".join(c for c in normalized if not unicodedata.combining(c))
        # borrar log
        logger.debug(f"Nombre limpiado estilo reports a: '{cleaned_name}'")
        return cleaned_name

    # === utilidades de títulos ===
    @property
    def _TITULOS(self) -> set:
        return {'catchers', 'pitchers', 'infielders', 'outfielders', 'cuerpo tecnico', 'roster'}

    def is_header_row(self, row) -> bool:
        # borrar log
        logger.debug(f"Verificando si la fila es un encabezado: {row}")
        is_header = any(str(cell).strip().lower() in ['nombre', 'posición', 'pos'] for cell in row)
        # borrar log
        logger.debug(f"Fila es encabezado: {is_header}")
        return is_header

    def is_section_title(self, row) -> bool:
        # borrar log
        logger.debug(f"Verificando si la fila es un título de sección: {row}")
        is_title = any(self._norm_title(cell) in self._TITULOS for cell in row if pd.notna(cell))
        # borrar log
        logger.debug(f"Fila es título de sección: {is_title}")
        return is_title

    def _titles_in_row(self, row) -> List[Tuple[int, str]]:
        # borrar log
        logger.debug(f"Buscando títulos en la fila: {row}")
        out = []
        for j, cell in enumerate(row):
            if pd.isna(cell):
                continue
            t = self._norm_title(str(cell))
            if t in self._TITULOS:
                out.append((j, t))
        # borrar log
        logger.debug(f"Títulos encontrados en la fila: {out}")
        return out

    def _row_is_mostly_title(self, row) -> bool:
        # borrar log
        logger.debug(f"Verificando si la fila es mayormente un título: {row}")
        non_empty = sum(1 for c in row if pd.notna(c) and str(c).strip() != "")
        has_title = len(self._titles_in_row(row)) >= 1
        is_mostly_title = has_title and non_empty <= 2  # 1 título + <=1 celda más
        # borrar log
        logger.debug(f"Fila es mayormente un título: {is_mostly_title}")
        return is_mostly_title

    def _title_from_position_value(self, pos_val: Optional[str]) -> Optional[str]:
        # borrar log
        logger.debug(f"Derivando título de valor de posición: '{pos_val}'")
        if not pos_val:
            # borrar log
            logger.debug("Valor de posición vacío, devolviendo None.")
            return None
        p = self._norm_title(str(pos_val))
        # pitchers
        if p in {"p", "pit", "pitcher", "pitchers", "rhp", "lhp"}:
            # borrar log
            logger.debug(f"'{pos_val}' mapeado a 'pitchers'.")
            return "pitchers"
        # catchers
        if p in {"c", "c1", "catcher", "catchers"}:
            # borrar log
            logger.debug(f"'{pos_val}' mapeado a 'catchers'.")
            return "catchers"
        # infielders
        if p in {"if", "inf", "infield", "infielders", "1b", "2b", "3b", "ss", "1st base", "2nd base", "3rd base", "shortstop"}:
            # borrar log
            logger.debug(f"'{pos_val}' mapeado a 'infielders'.")
            return "infielders"
        # outfielders
        if p in {"of", "outfield", "outfielders", "lf", "cf", "rf", "left field", "center field", "right field"}:
            # borrar log
            logger.debug(f"'{pos_val}' mapeado a 'outfielders'.")
            return "outfielders"
        # cuerpo tecnico
        if p in {"coach", "coaches", "staff", "cuerpo tecnico", "cuerpo técnico"}:
            # borrar log
            logger.debug(f"'{pos_val}' mapeado a 'cuerpo tecnico'.")
            return "cuerpo tecnico"
        # borrar log
        logger.debug(f"'{pos_val}' no mapeado a ningún título conocido, devolviendo None.")
        return None

    # === PARTE 1: EXTRACCIÓN DE NOMBRES DESDE EXCEL ===
    def extract_table_sections_from_excel(self, filepath: str) -> List[pd.DataFrame]:
        logger.info(f"Buscando secciones en archivo: {filepath}")
        try:
            df_raw = pd.read_excel(filepath, header=None)
            # borrar log
            logger.info(f"Archivo Excel '{filepath}' cargado con {df_raw.shape[0]} filas y {df_raw.shape[1]} columnas.")
        except Exception as e:
            logger.error(f"Error al leer el archivo Excel '{filepath}': {e} borrar log")
            return []

        # Detección de modo
        titles_by_row = {}
        horizontal_row_idx = None
        for i, row in df_raw.iterrows():
            found = self._titles_in_row(row)
            if found:
                titles_by_row[i] = found
                if len(found) >= 2 and horizontal_row_idx is None:
                    horizontal_row_idx = i
                    # borrar log
                    logger.debug(f"Múltiples títulos en fila {i}, potencial modo horizontal.")

        if horizontal_row_idx is not None:
            logger.info(f"Modo HORIZONTAL detectado en fila {horizontal_row_idx}")
            return self._extract_horizontal_blocks(df_raw, horizontal_row_idx, titles_by_row[horizontal_row_idx])
        else:
            logger.info("Modo VERTICAL detectado")
            return self._extract_vertical_blocks(df_raw)

    def _extract_vertical_blocks(self, df_raw: pd.DataFrame) -> List[pd.DataFrame]:
        # borrar log
        logger.info("Extrayendo bloques en modo vertical.")
        start_rows: List[int] = []
        title_rows: List[Optional[str]] = []
        last_title: Optional[str] = None
        n = len(df_raw)

        for i, row in df_raw.iterrows():
            if self._row_is_mostly_title(row):
                titles = self._titles_in_row(row)
                if titles:
                    last_title = titles[0][1]
                    # borrar log
                    logger.debug(f"Título de sección vertical encontrado en fila {i}: '{last_title}'")
                next_is_header = (i + 1 < n) and self.is_header_row(df_raw.iloc[i + 1])
                start_rows.append(i + 1 if next_is_header else i)
                title_rows.append(last_title)
                # borrar log
                logger.debug(f"Inicio de bloque vertical en fila: {start_rows[-1]}")
            elif self.is_header_row(row):
                if last_title is not None:
                    start_rows.append(i)
                    title_rows.append(last_title)
                    # borrar log
                    logger.debug(f"Encabezado de bloque vertical encontrado en fila: {i}")

        if not start_rows:
            # borrar log
            logger.warning("No se encontraron filas de inicio para bloques verticales.")
            return []

        tables: List[pd.DataFrame] = []
        for (start, end), title in zip(zip_longest(start_rows, start_rows[1:]), title_rows):
            # borrar log
            logger.debug(f"Procesando sección vertical de fila {start} a {end} con título '{title}'.")
            section = df_raw.iloc[start:end].copy()

            header_row = section.iloc[0]
            header_norm = [str(c).lower() if pd.notna(c) else "" for c in header_row]
            if any(h in ['nombre', 'posición', 'pos', 'first name', 'last name'] for h in header_norm):
                section.columns = [
                    str(c).lower() if pd.notna(c) else f'unnamed_{idx}'
                    for idx, c in enumerate(section.iloc[0])
                ]
                section = section[1:].reset_index(drop=True)
                # borrar log
                logger.debug(f"Sección vertical con encabezados detectados y aplicados.")
            else:
                section.columns = [f'col_{k}' for k in range(section.shape[1])]
                section = section.reset_index(drop=True)
                # borrar log
                logger.debug(f"Sección vertical sin encabezados explícitos, columnas genéricas asignadas.")

            section.dropna(axis=1, how='all', inplace=True)
            section.dropna(axis=0, how='all', inplace=True)
            # borrar log
            logger.debug(f"Sección vertical después de eliminar NAs. Filas: {len(section)}")

            processed_section = self._extraer_nombres_y_posicion(section, title or "unknown")
            if not processed_section.empty:
                tables.append(processed_section)
                logger.info(f"Sección detectada (vertical): {title} con {len(processed_section)} filas")
            else:
                # borrar log
                logger.warning(f"Sección vertical procesada está vacía para el título '{title}'.")

        # borrar log
        logger.info(f"Finalizada la extracción de bloques verticales. {len(tables)} tablas extraídas.")
        return tables

    def _extract_horizontal_blocks(self, df_raw: pd.DataFrame, row_idx: int, titles_in_row: List[Tuple[int, str]]) -> List[pd.DataFrame]:
        # borrar log
        logger.info(f"Extrayendo bloques en modo horizontal desde fila {row_idx}.")
        tables: List[pd.DataFrame] = []
        n_rows = df_raw.shape[0]

        for col_idx, title in titles_in_row:
            # borrar log
            logger.debug(f"Procesando columna {col_idx} para título '{title}' en modo horizontal.")
            nombres_detectados: List[str] = []
            r = row_idx + 1
            while r < n_rows:
                row = df_raw.iloc[r]
                if all(pd.isna(c) or str(c).strip() == "" for c in row):
                    # borrar log
                    logger.debug(f"Fila {r} está vacía, terminando bloque horizontal para '{title}'.")
                    break

                cell = row.iloc[col_idx] if col_idx < len(row) else None
                if pd.isna(cell) or str(cell).strip() == "":
                    r += 1
                    continue

                txt = str(cell).strip()
                if self._norm_title(txt) in self._TITULOS:
                    # borrar log
                    logger.debug(f"Título de sección '{txt}' encontrado en fila {r}, terminando bloque para '{title}'.")
                    break

                if len(txt.split()) >= 2:
                    nombres_detectados.append(txt)
                    # borrar log
                    logger.debug(f"Nombre detectado para '{title}' en fila {r}: '{txt}'")

                r += 1

            if nombres_detectados:
                df = pd.DataFrame({
                    'id': range(1, len(nombres_detectados) + 1),
                    'raw_name': nombres_detectados,
                    'position': None,
                    'title': title
                })
                tables.append(df)
                logger.info(f"Sección detectada (horizontal): {title} con {len(df)} filas")
            else:
                # borrar log
                logger.warning(f"No se detectaron nombres para el título '{title}' en modo horizontal.")

        # borrar log
        logger.info(f"Finalizada la extracción de bloques horizontales. {len(tables)} tablas extraídas.")
        return tables

    def _extraer_nombres_y_posicion(self, df: pd.DataFrame, title: str) -> pd.DataFrame:
        # borrar log
        logger.info(f"Extrayendo nombres y posiciones de un DataFrame con título '{title}'.")
        df = df.copy()
        TITULOS = self._TITULOS

        # 1) Esquema Nombre/Posición directo
        cols = {c.strip().lower(): c for c in df.columns if isinstance(c, str)}
        # candidatos de nombre y posición
        name_cols = [cols[k] for k in cols if k in {"nombre", "name", "player"}]
        pos_cols = [cols[k] for k in cols if k in {"posición", "pos", "position", "positions"}]

        if name_cols and pos_cols:
            name_col = name_cols[0]
            pos_col = pos_cols[0]
            # borrar log
            logger.debug(f"Detectado esquema Nombre/Posición: Nombre='{name_col}', Posición='{pos_col}'")
            df_out = pd.DataFrame({
                "raw_name": df[name_col].astype(str).str.strip()
            })
            df_out["position"] = df[pos_col].astype(str).str.strip()
            df_out = df_out[(df_out["raw_name"] != "") & df_out["raw_name"].notna()]

            # Derivar title por fila sólo si el title entrante es desconocido
            if not title or title == "unknown":
                titles = df_out["position"].map(lambda v: self._title_from_position_value(v) or "roster")
                # borrar log
                logger.debug("Título derivado por fila desde la columna de posición.")
            else:
                titles = pd.Series(title, index=df_out.index)
                # borrar log
                logger.debug(f"Título fijo '{title}' aplicado a todas las filas.")

            df_out.insert(0, "id", range(1, len(df_out) + 1))
            df_out["title"] = titles
            # borrar log
            logger.info(f"Extraídos {len(df_out)} nombres usando esquema Nombre/Posición directo.")
            return df_out[["id", "raw_name", "position", "title"]]

        # 2) Esquema First/Last (ya existente)
        if 'first name' in cols and 'last name' in cols:
            # borrar log
            logger.debug("Detectado esquema First Name/Last Name.")
            df['raw_name'] = (
                df[cols['first name']].astype(str).str.strip()
                + ' '
                + df[cols['last name']].astype(str).str.strip()
            )
            
            df['position'] = df[cols['positions']].astype(str).str.strip() if 'positions' in cols else None
            # borrar log
            logger.debug(f"Nombres combinados de 'first name' y 'last name'.")

        # 3) Esquema con columna 'nombre'
        elif 'nombre' in cols:
            # borrar log
            logger.debug("Detectado esquema con columna 'nombre'.")
            df['raw_name'] = df[cols['nombre']].astype(str).str.strip()
            # si existe alguna forma de posición, úsala; si no, None
            pos_col = None
            for k in ("posición", "pos", "position", "positions"):
                if k in cols:
                    pos_col = cols[k]
                    break
            df['position'] = df[pos_col].astype(str).str.strip() if pos_col else None
            # borrar log
            logger.debug(f"Nombres extraídos de columna 'nombre', posición de '{pos_col or 'N/A'}'.")

        # 4) Fallback heurístico
        else:
            # borrar log
            logger.debug("Usando fallback heurístico para extraer nombres.")
            nombres_detectados: List[Optional[str]] = []
            for _, row in df.iterrows():
                nombre = None
                for cell in row:
                    if isinstance(cell, str) and len(cell.strip().split()) >= 2:
                        if self._norm_title(cell) in TITULOS:
                            continue
                        nombre = cell.strip()
                        break
                nombres_detectados.append(nombre)
            df = pd.DataFrame({
                'raw_name': nombres_detectados,
                'position': None
            })
            df = df[df['raw_name'].notna()]
            # borrar log
            logger.debug(f"Fallback heurístico extrajo {len(df)} nombres.")

        df['id'] = range(1, len(df) + 1)
        # Si el title entrante es desconocido y tenemos 'position', derivar por fila
        if (not title or title == "unknown") and ('position' in df.columns):
            df['title'] = df['position'].map(lambda v: self._title_from_position_value(v) or "roster")
            # borrar log
            logger.debug("Título derivado por fila usando columna 'position' en fallback.")
        else:
            df['title'] = title
            # borrar log
            logger.debug(f"Título fijo '{title}' aplicado en fallback.")
        # borrar log
        logger.info(f"Nombres y posiciones extraídos. Total: {len(df)}.")
        return df[['id', 'raw_name', 'position', 'title']]

    def cargar_excel(self, filepath: str) -> pd.DataFrame:
        logger.info("Cargando hoja 'Roster' desde Excel...")
        try:
            df = pd.read_excel(filepath, sheet_name="Roster", header=None)
            # borrar log
            logger.info(f"Hoja 'Roster' cargada inicialmente con {df.shape[0]} filas.")
            header_keywords = ['first name', 'last name', 'date of birth', 'positions']
            header_row_index = None
            for i, row in df.iterrows():
                row_str = [str(cell).strip().lower() for cell in row if pd.notna(cell)]
                if sum(hk in ' '.join(row_str) for hk in header_keywords) >= 2:
                    header_row_index = i
                    # borrar log
                    logger.debug(f"Encabezado de hoja 'Roster' encontrado en fila {i}.")
                    break
            if header_row_index is None:
                # borrar log
                logger.warning("No se encontró fila de encabezado válida en la hoja 'Roster'.")
                raise ValueError("No se encontró fila de encabezado válida en la hoja 'Roster'.")

            df_data = df.iloc[header_row_index:].copy()
            df_data.columns = [
                str(c).lower() if pd.notna(c) else f'unnamed_{i}'
                for i, c in enumerate(df_data.iloc[0])
            ]
            df_data = df_data[1:].reset_index(drop=True)
            logger.info("Hoja 'Roster' cargada correctamente")
            # borrar log
            logger.info(f"DataFrame final de 'Roster' tiene {len(df_data)} filas.")
            return self._extraer_nombres_y_posicion(df_data, 'unknown')
        except ValueError as e:
            logger.warning(f"Falló la carga directa: {e}, intentando extraer por secciones... borrar log")
            secciones = self.extract_table_sections_from_excel(filepath)
            if secciones:
                # borrar log
                logger.info(f"Secciones extraídas con éxito: {len(secciones)}.")
            else:
                # borrar log
                logger.warning("No se extrajeron secciones del archivo Excel.")
            return pd.concat(secciones, ignore_index=True) if secciones else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error al cargar hoja 'Roster', intentando extraer secciones... ({type(e).__name__}: {e}) borrar log")
            secciones = self.extract_table_sections_from_excel(filepath)
            if secciones:
                # borrar log
                logger.info(f"Secciones extraídas con éxito (después de error general): {len(secciones)}.")
            else:
                # borrar log
                logger.warning("No se extrajeron secciones del archivo Excel (después de error general).")
            return pd.concat(secciones, ignore_index=True) if secciones else pd.DataFrame()

    # === PARTE 2: EXTRACCIÓN DE NOMBRES DESDE PDF ===
    def cargar_pdf(self, filepath: str) -> pd.DataFrame:
        logger.info(f"Extrayendo texto de PDF: {filepath}")
        TITULOS = self._TITULOS
        try:
            with pdfplumber.open(filepath) as pdf:
                lines: List[str] = []
                for page_num, page in enumerate(pdf.pages):
                    # borrar log
                    logger.debug(f"Extrayendo texto de la página {page_num + 1} del PDF.")
                    text = page.extract_text()
                    if text:
                        lines.extend(text.splitlines())
                # borrar log
                logger.info(f"Total de líneas extraídas del PDF: {len(lines)}.")

                current_title: Optional[str] = None
                nombres: List[Dict[str, Optional[str]]] = []
                for line in lines:
                    line_clean = line.strip()
                    if not line_clean:
                        continue

                    norm = self._norm_title(line_clean)
                    if norm in TITULOS:
                        current_title = norm
                        # borrar log
                        logger.debug(f"Título de sección PDF encontrado: '{current_title}'")
                        continue

                    if current_title and len(line_clean.split()) >= 2:
                        nombres.append({
                            'id': len(nombres) + 1,
                            'raw_name': line_clean,
                            'position': None,
                            'title': current_title
                        })
                        # borrar log
                        logger.debug(f"Nombre PDF detectado bajo '{current_title}': '{line_clean}'")
            df = pd.DataFrame(nombres)
            logger.info(f"Extraídos {len(df)} nombres desde PDF")
            return df
        except Exception as e:
            logger.error(f"Error al cargar el archivo PDF '{filepath}': {e} borrar log")
            return pd.DataFrame()

    # === PARTE 3: OBTENER NOMBRES DESDE TRACKMAN (BigQuery o CSV) ===
    def _bq_get_distinct_names(self) -> Dict[str, List[str]]:
        """
        Consulta BigQuery y devuelve nombres distintos por rol:
        {'batters': [...], 'pitchers': [...]}, limpios al estilo reports.clean_name.
        Cachea el resultado en self._bq_names_cache.
        """
        if self._bq_names_cache is not None:
            # borrar log
            logger.info("Devolviendo nombres de BigQuery desde la caché.")
            return self._bq_names_cache

        logger.info("Consultando BigQuery para nombres distintos de Batter/Pitcher...")
        query = """
        SELECT DISTINCT Batter AS name, 'b' AS role
        FROM `baseballlmb.trackman_db.trackman_table`
        WHERE Batter IS NOT NULL AND Batter != '-' AND Temporada_Anio IN (
            "Invierno-2025","Verano-2025","Invierno-2024","Verano-2024"
        )
        UNION ALL
        SELECT DISTINCT Pitcher AS name, 'p' AS role
        FROM `baseballlmb.trackman_db.trackman_table`
        WHERE Pitcher IS NOT NULL AND Pitcher != '-' AND Temporada_Anio IN (
            "Invierno-2025","Verano-2025","Invierno-2024","Verano-2024"
        )
        """
        # Ejecutar query
        try:
            client = bigquery.Client()
            job = client.query(query)
            # borrar log
            logger.debug("Consulta a BigQuery enviada.")
            try:
                credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=credentials)
                df = job.result().to_dataframe(bqstorage_client=bqstorageclient)
                # borrar log
                logger.debug("Resultados de BigQuery obtenidos usando BigQueryReadClient.")
            except Exception as e_bq_storage:
                logger.warning(f"Falló el uso de BigQueryReadClient: {e_bq_storage}. Intentando con to_dataframe() normal. borrar log")
                df = job.result().to_dataframe()
                # borrar log
                logger.debug("Resultados de BigQuery obtenidos usando to_dataframe() normal.")
        except Exception as e_query:
            logger.error(f"Error al ejecutar la consulta BigQuery: {e_query} borrar log")
            self._bq_names_cache = {"batters": [], "pitchers": []}
            return self._bq_names_cache

        if df.empty:
            logger.warning("BigQuery devolvió 0 nombres distintos.")
            self._bq_names_cache = {"batters": [], "pitchers": []}
            return self._bq_names_cache

        # Limpieza consistente
        df["name"] = df["name"].astype(str).map(self._clean_name_reports_style)
        df = df.dropna(subset=["name"]).query("name != ''")
        # borrar log
        logger.debug(f"Nombres de BigQuery limpiados. Total de filas después de limpieza: {len(df)}.")

        batters = sorted(df[df["role"] == "b"]["name"].unique().tolist())
        pitchers = sorted(df[df["role"] == "p"]["name"].unique().tolist())

        self._bq_names_cache = {"batters": batters, "pitchers": pitchers}
        logger.info(f"BigQuery nombres: batters={len(batters)}, pitchers={len(pitchers)}")
        return self._bq_names_cache

    def cargar_nombres_trackman(self, path_csv: Optional[str] = None) -> List[str]:
        """
        Mantiene compatibilidad: si se pasa CSV, carga desde CSV.
        Si NO se pasa CSV:
            - Intenta BigQuery y devuelve lista combinada (bateadores ∪ pitchers).
            - Si falla, usa la lista embebida.
        """
        # borrar log
        logger.info(f"Cargando nombres de Trackman. path_csv: {path_csv}")
        if path_csv is not None:
            logger.info(f"Cargando nombres de Trackman desde: {path_csv}")
            try:
                df = pd.read_csv(path_csv)
                if 'nombre' not in df.columns:
                    # borrar log
                    logger.error("El archivo CSV no contiene una columna llamada 'nombre'.")
                    raise ValueError("El archivo CSV debe contener una columna llamada 'nombre'")
                nombres = df['nombre'].astype(str).tolist()
                logger.info(f"{len(nombres)} nombres cargados desde Trackman (CSV)")
                return nombres
            except Exception as e:
                logger.error(f"Error al cargar nombres desde CSV '{path_csv}': {e} borrar log")
                return []

        try:
            bq = self._bq_get_distinct_names()
            combined_names = sorted(list(set(bq["batters"]) | set(bq["pitchers"])))
            # borrar log
            logger.info(f"Nombres de Trackman cargados desde BigQuery. Total: {len(combined_names)}.")
            return combined_names
        except Exception as e:
            logger.error(f"No fue posible obtener nombres desde BigQuery: {e}. Usando lista embebida. borrar log")
            return list(self.trackman_names)

    def cargar_nombres_trackman_por_rol(self, path_csv: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Nuevo helper para matching por rol.
        Si CSV: usa la misma lista para ambos roles.
        Si BigQuery: retorna {'batters': [...], 'pitchers': [...]}.
        """
        # borrar log
        logger.info(f"Cargando nombres de Trackman por rol. path_csv: {path_csv}")
        if path_csv is not None:
            base = self.cargar_nombres_trackman(path_csv)
            # borrar log
            logger.info(f"Nombres cargados de CSV y aplicados a ambos roles. Total: {len(base)}.")
            return {"batters": base, "pitchers": base}
        
        bq_names_by_role = self._bq_get_distinct_names()
        # borrar log
        logger.info(f"Nombres cargados de BigQuery por rol. Batters: {len(bq_names_by_role.get('batters', []))}, Pitchers: {len(bq_names_by_role.get('pitchers', []))}.")
        return bq_names_by_role

    # === PARTE 4: COMPARACIÓN CON TRACKMAN ===
    def encontrar_similares(self, nombres_archivo: List[str], nombres_trackman: List[str], umbral: float = 90) -> List[Dict]:
        logger.info(f"Buscando coincidencias entre {len(nombres_archivo)} nombres de roster y {len(nombres_trackman)} de Trackman con umbral {umbral:.1f}...")
        coincidencias = []
        nombres_track_norm_to_orig = {self.normalizar_nombre(n): n for n in nombres_trackman}
        
        if not nombres_trackman:
            logger.warning("La lista de nombres de Trackman está vacía, no se pueden realizar comparaciones. borrar log")
            for nombre in nombres_archivo:
                coincidencias.append({
                    "nombre_roster": nombre,
                    "nombre_trackman": None,
                    "coincidencia": False,
                    "similitud": 0.0,
                    "algoritmo": None
                })
            return coincidencias

        for nombre in nombres_archivo:
            mejor_match = None
            mejor_score = 0
            algoritmo = None
            normalizado = self.normalizar_nombre(nombre)
            # borrar log
            logger.debug(f"Evaluando nombre de roster: '{nombre}' (Normalizado: '{normalizado}')")

            for track_norm, track_orig in nombres_track_norm_to_orig.items():
                score = rapidfuzz.fuzz.ratio(normalizado, track_norm)
                if score > mejor_score:
                    mejor_score = score
                    mejor_match = track_orig
                    algoritmo = "rapidfuzz.ratio (normalizado)"
                # borrar log
                logger.debug(f" Comparando '{normalizado}' con '{track_norm}', score: {score:.1f}")


            if mejor_score < umbral:
                simplificado = self.simplificar_nombre(nombre)
                # borrar log
                logger.debug(f"Score inicial bajo ({mejor_score:.1f}), intentando con nombres simplificados. Simplificado: '{simplificado}'")
                for track_norm, track_orig in nombres_track_norm_to_orig.items():
                    score = rapidfuzz.fuzz.ratio(simplificado, self.simplificar_nombre(track_orig))
                    if score > mejor_score:
                        mejor_score = score
                        mejor_match = track_orig
                        algoritmo = "rapidfuzz.ratio (simplificado)"
                    # borrar log
                    logger.debug(f" Comparando simplificado '{simplificado}' con simplificado '{self.simplificar_nombre(track_orig)}', score: {score:.1f}")


            if mejor_score >= umbral:
                logger.info(f"✓ Match: '{nombre}' ≈ '{mejor_match}' → {mejor_score:.1f} ({algoritmo})")
            else:
                logger.info(f"✗ Sin match para: '{nombre}' (score máx: {mejor_score:.1f})")

            coincidencias.append({
                "nombre_roster": nombre,
                "nombre_trackman": mejor_match if mejor_score >= umbral else None,
                "coincidencia": mejor_score >= umbral,
                "similitud": mejor_score,
                "algoritmo": algoritmo if mejor_score >= umbral else None
            })
        # borrar log
        logger.info(f"Finalizada la búsqueda de coincidencias. Total de coincidencias evaluadas: {len(coincidencias)}.")
        return coincidencias

    # === RESÚMENES Y PROCESAMIENTO FINAL (CLI/GUI) ===
    def obtener_preview(self, df: pd.DataFrame) -> List[Dict]:
        # borrar log
        logger.debug(f"Obteniendo preview de {self.preview_rows} filas de DataFrame.")
        return df.head(self.preview_rows).to_dict(orient='records')

    def generar_resumen(self, df: pd.DataFrame) -> Dict:
        # borrar log
        logger.info("Generando resumen del DataFrame.")
        total = len(df)
        if "position" in df.columns:
            posiciones = df['position'].fillna("").astype(str).str.strip().str.lower().value_counts().to_dict()
            # borrar log
            logger.debug(f"Resumen de posiciones: {posiciones}")
        else:
            posiciones = {}
            # borrar log
            logger.debug("Columna 'position' no encontrada para el resumen.")
        summary = {
            "total_jugadores": total,
            "posiciones": posiciones
        }
        # borrar log
        logger.info("Resumen generado.")
        return summary

    def procesar_archivo(self, filepath: str, trackman_csv: Optional[str] = None, umbral: float = 90) -> Dict:
        base = os.path.basename(filepath)
        logger.info(f"Procesando archivo: {base}")
        # borrar log
        logger.debug(f"Parámetros de procesamiento: filepath='{filepath}', trackman_csv='{trackman_csv}', umbral={umbral}")
        try:
            if filepath.lower().endswith(('.xls', '.xlsx')):
                logger.info("Detectado archivo Excel")
                tabla = self.cargar_excel(filepath)
            elif filepath.lower().endswith('.csv'):
                logger.info("Detectado archivo CSV")
                raw_df = pd.read_csv(filepath)
                # borrar log
                logger.debug(f"Archivo CSV '{filepath}' cargado con {raw_df.shape[0]} filas.")
                tabla = self._extraer_nombres_y_posicion(raw_df, 'roster')
            elif filepath.lower().endswith('.pdf'):
                logger.info("Detectado archivo PDF")
                tabla = self.cargar_pdf(filepath)
            else:
                logger.error(f"Tipo de archivo no soportado: {filepath} borrar log")
                raise ValueError("Tipo de archivo no soportado. Se aceptan .xls, .xlsx, .csv y .pdf.")

            if tabla.empty:
                logger.warning("No se extrajeron nombres del archivo. Tabla vacía. borrar log")
                return {base: {"error": "Archivo sin datos válidos"}}

            # Nombres Trackman por rol
            bq_names = self.cargar_nombres_trackman_por_rol(trackman_csv)
            # borrar log
            logger.debug(f"Nombres Trackman por rol cargados: Batters={len(bq_names.get('batters', []))}, Pitchers={len(bq_names.get('pitchers', []))}")

            # Nombres extraídos del archivo
            nombres_archivo = tabla['raw_name'].dropna().astype(str).tolist()
            # borrar log
            logger.debug(f"Nombres extraídos del archivo: {len(nombres_archivo)}")

            # Roles por nombre (para dividir matching por rol)
            roles_by_name = {
                str(r).strip(): _rol_desde_title(str(t).strip().lower())
                for r, t in zip(tabla['raw_name'].astype(str), tabla['title'].astype(str))
            }
            # borrar log
            logger.debug(f"Roles extraídos por nombre: {len(roles_by_name)} entradas.")

            # Separar por rol de roster
            roster_pitchers = [n for n in nombres_archivo if roles_by_name.get(n, "Unknown").lower().startswith("pitcher")]
            roster_batters  = [n for n in nombres_archivo if not roles_by_name.get(n, "Unknown").lower().startswith("pitcher")
                               and not roles_by_name.get(n, "Unknown").lower().startswith("staff")]
            # borrar log
            logger.debug(f"Roster Pitchers: {len(roster_pitchers)}, Roster Batters: {len(roster_batters)}")

            # Matching por rol usando las listas de BigQuery
            coincidencias: List[Dict] = []
            if roster_batters:
                # borrar log
                logger.info(f"Iniciando matching para {len(roster_batters)} bateadores.")
                coincidencias += self.encontrar_similares(roster_batters, bq_names.get("batters", []), umbral=umbral)
            if roster_pitchers:
                # borrar log
                logger.info(f"Iniciando matching para {len(roster_pitchers)} pitchers.")
                coincidencias += self.encontrar_similares(roster_pitchers, bq_names.get("pitchers", []), umbral=umbral)

            logger.info(f"Procesamiento completado: {len(coincidencias)} coincidencias evaluadas")

            return {
                base: {
                    "tables": self.obtener_preview(tabla),
                    "datos_extraidos": {
                        **self.generar_resumen(tabla),
                        "coincidencias_trackman": coincidencias
                    },
                    "roles_by_name": roles_by_name
                }
            }
        except Exception as e:
            logger.error(f"Error durante el procesamiento de '{base}': {type(e).__name__} - {e} borrar log")
            return {base: {"error": f"Error al procesar archivo: {type(e).__name__} - {e}"}}


# ========================= #
# Adaptador para la GUI     #
# ========================= #
def _rol_desde_title(title: Optional[str]) -> str:
    # borrar log
    logger.debug(f"Derivando rol desde título: '{title}'")
    if not title:
        # borrar log
        logger.debug("Título vacío, devolviendo 'Unknown'.")
        return "Unknown"
    t = str(title).strip().lower().rstrip(":-")
    if t == "pitchers":
        # borrar log
        logger.debug(f"Título '{title}' mapeado a 'Pitcher'.")
        return "Pitcher"
    if t == "catchers":
        # borrar log
        logger.debug(f"Título '{title}' mapeado a 'Batter/catcher'.")
        return "Batter/catcher"
    if t == "infielders":
        # borrar log
        logger.debug(f"Título '{title}' mapeado a 'Batter/infielders'.")
        return "Batter/infielders"
    if t == "outfielders":
        # borrar log
        logger.debug(f"Título '{title}' mapeado a 'Batter/outfielders'.")
        return "Batter/outfielders"
    if t == "roster":
        # borrar log
        logger.debug(f"Título '{title}' mapeado a 'Batter'.")
        return "Batter"
    if t in ("cuerpo tecnico", "cuerpo técnico"):
        # borrar log
        logger.debug(f"Título '{title}' mapeado a 'Staff'.")
        return "Staff"
    # borrar log
    logger.debug(f"Título '{title}' no mapeado a rol conocido, devolviendo 'Unknown'.")
    return "Unknown"


def run_tools_from_pdf(path_pdf: str, trackman_csv: Optional[str] = None, umbral: float = 90.0) -> Dict[str, object]:
    """
    Retorna:
    - batters_matched: List[{"extraido": str, "canonico": str, "score": float}]
    - pitchers_matched: List[{"extraido": str, "canonico": str, "score": float}]
    - staff_matched: List[{"extraido": str, "canonico": str, "score": float}]
    - batters_unmatched: List[str]
    - pitchers_unmatched: List[str]
    - staff_unmatched: List[str]
    - totals: {"batters": int, "pitchers": int, "staff": int}
    """
    # borrar log
    logger.info(f"Iniciando run_tools_from_pdf para: '{path_pdf}'")
    t = Tools()
    if not path_pdf.lower().endswith(".pdf"):
        # borrar log
        logger.error(f"Tipo de archivo no válido: '{path_pdf}'. Se esperaba PDF. borrar log")
        raise ValueError("El archivo debe ser PDF.")

    tabla = t.cargar_pdf(path_pdf)
    if tabla.empty:
        # borrar log
        logger.warning(f"Tabla extraída del PDF '{path_pdf}' está vacía. Devolviendo resultados vacíos. borrar log")
        return {
            "batters_matched": [],
            "pitchers_matched": [],
            "staff_matched": [],
            "batters_unmatched": [],
            "pitchers_unmatched": [],
            "staff_unmatched": [],
            "totals": {"batters": 0, "pitchers": 0, "staff": 0}
        }

    tabla = tabla.copy()
    tabla["rol"] = tabla["title"].map(_rol_desde_title)
    # borrar log
    logger.debug(f"Roles asignados a {len(tabla)} entradas en la tabla.")

    # Obtener nombres Trackman por rol
    try:
        bq_names = t.cargar_nombres_trackman_por_rol(trackman_csv)
        # borrar log
        logger.debug(f"Nombres de Trackman por rol cargados: {bq_names.keys()}")
    except Exception as e:
        # Fallback compatible
        logger.error(f"Error al cargar nombres Trackman por rol desde BigQuery, usando fallback a CSV/embebidos: {e} borrar log")
        base_trackman = t.cargar_nombres_trackman(trackman_csv)
        bq_names = {"batters": base_trackman, "pitchers": base_trackman}
        # borrar log
        logger.debug("Fallback de nombres Trackman realizado.")

    def _match_por_rol(df_rol: pd.DataFrame, lista_ref: List[str]):
        # borrar log
        logger.debug(f"Iniciando matching para rol con {len(df_rol)} entradas y {len(lista_ref)} nombres de referencia.")
        nombres = df_rol["raw_name"].dropna().astype(str).tolist()
        coincidencias = t.encontrar_similares(nombres, lista_ref, umbral=umbral)
        matched, unmatched = [], []
        for c in coincidencias:
            if c.get("coincidencia"):
                matched.append({
                    "extraido": c.get("nombre_roster"),
                    "canonico": c.get("nombre_trackman"),
                    "score": float(c.get("similitud", 0.0))
                })
                # borrar log
                logger.debug(f"Match encontrado: {c.get('nombre_roster')} -> {c.get('nombre_trackman')}")
            else:
                unmatched.append(c.get("nombre_roster"))
                # borrar log
                logger.debug(f"No match para: {c.get('nombre_roster')}")
        # borrar log
        logger.debug(f"Matching por rol finalizado. Matched: {len(matched)}, Unmatched: {len(unmatched)}.")
        return matched, unmatched

    df_b = tabla[tabla["rol"].str.startswith("Batter")] # Incluye catchers, infielders, outfielders
    df_p = tabla[tabla["rol"] == "Pitcher"]
    df_s = tabla[tabla["rol"] == "Staff"]
    # borrar log
    logger.debug(f"Dividiendo tabla por roles: Batters={len(df_b)}, Pitchers={len(df_p)}, Staff={len(df_s)}")

    batters_matched, batters_unmatched = _match_por_rol(df_b, bq_names.get("batters", []))
    pitchers_matched, pitchers_unmatched = _match_por_rol(df_p, bq_names.get("pitchers", []))
    # Staff: usamos lista combinada
    staff_base = sorted(list(set(bq_names.get("batters", [])) | set(bq_names.get("pitchers", []))))
    staff_matched, staff_unmatched = _match_por_rol(df_s, staff_base)

    totals = {
        "batters": int(len(df_b)),
        "pitchers": int(len(df_p)),
        "staff": int(len(df_s))
    }
    # borrar log
    logger.info(f"Finalizado run_tools_from_pdf. Totales: {totals}. Matches: Batters={len(batters_matched)}, Pitchers={len(pitchers_matched)}, Staff={len(staff_matched)}")

    return {
        "batters_matched": batters_matched,
        "pitchers_matched": pitchers_matched,
        "staff_matched": staff_matched,
        "batters_unmatched": batters_unmatched,
        "pitchers_unmatched": pitchers_unmatched,
        "staff_unmatched": staff_unmatched,
        "totals": totals
    }
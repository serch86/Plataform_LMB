import os
import pandas as pd
import unicodedata
import re
from typing import List, Dict
import rapidfuzz
from itertools import zip_longest
import pdfplumber
import logging

# Solo obtiene logger, sin configurar global aquí
logger = logging.getLogger(__name__)


class Tools:
    def __init__(self, preview_rows: int = 5):
        self.preview_rows = preview_rows
        self.section_title_pattern = re.compile(r"(catchers|pitchers|infielders|outfielders)", re.IGNORECASE)

    # === normalizar y simplificar ===
    def normalizar_nombre(self, nombre: str) -> str:
        nombre = unicodedata.normalize("NFKD", nombre)
        nombre = "".join(c for c in nombre if not unicodedata.combining(c))
        return " ".join(nombre.strip().lower().split())

    def simplificar_nombre(self, nombre: str) -> str:
        nombre = self.normalizar_nombre(nombre)
        partes = nombre.split()
        partes_filtradas = [p for p in partes if len(p) > 2]
        return " ".join(partes_filtradas)

    # === DETECCIÓN DE ENCABEZADOS Y SECCIONES EN EXCEL ===
    def is_header_row(self, row) -> bool:
        return any(str(cell).strip().lower() in ['nombre', 'posición', 'pos'] for cell in row)

    def is_section_title(self, row) -> bool:
        return any(self.section_title_pattern.fullmatch(str(cell).strip()) for cell in row)

    # === PARTE 1: EXTRACCIÓN DE NOMBRES DESDE EXCEL ===
    def extract_table_sections_from_excel(self, filepath: str) -> List[pd.DataFrame]:
        logger.info(f"Buscando secciones en archivo: {filepath}")
        df_raw = pd.read_excel(filepath, header=None)
        start_rows = []
        title_rows = []

        for i, row in df_raw.iterrows():
            if self.is_header_row(row) or self.is_section_title(row):
                title = next(
                    (str(cell).strip().lower()
                     for cell in row
                     if str(cell).strip().lower() in ['catchers', 'pitchers', 'infielders', 'outfielders']),
                    None
                )
                start_rows.append(i)
                title_rows.append(title)

        if not start_rows:
            return []

        tables = []
        for (start, end), title in zip(zip_longest(start_rows, start_rows[1:]), title_rows):
            section = df_raw.iloc[start:end].copy()
            section.columns = [
                str(c).lower() if pd.notna(c) else f'unnamed_{i}'
                for i, c in enumerate(section.iloc[0])
            ]
            section = section[1:].reset_index(drop=True)
            section.dropna(axis=1, how='all', inplace=True)
            section.dropna(axis=0, how='all', inplace=True)

            try:
                processed_section = self._extraer_nombres_y_posicion(section, title or "unknown")
                tables.append(processed_section)
                logger.info(f"Sección detectada: {title} con {len(processed_section)} filas")
            except ValueError as e:
                logger.warning(f"No se pudo procesar una sección ({title}): {e}")
                continue

        return tables

    def _extraer_nombres_y_posicion(self, df: pd.DataFrame, title: str) -> pd.DataFrame:
        df = df.copy()

        if 'nombre' in df.columns:
            df['raw_name'] = df['nombre'].astype(str).str.strip()
            df['position'] = df.get('posición', None)
        elif 'first name' in df.columns and 'last name' in df.columns:
            df['raw_name'] = df['first name'].astype(str).str.strip() + ' ' + df['last name'].astype(str).str.strip()
            df['position'] = None
        else:
            nombres_detectados = []
            for _, row in df.iterrows():
                nombre = None
                for cell in row:
                    if isinstance(cell, str) and len(cell.strip().split()) >= 2:
                        if cell.strip().lower() in ['catchers', 'pitchers', 'infielders', 'outfielders']:
                            continue
                        nombre = cell.strip()
                        break
                nombres_detectados.append(nombre)

            df = pd.DataFrame({
                'raw_name': nombres_detectados,
                'position': None
            })

        df = df[df['raw_name'].notna()]
        df['id'] = range(1, len(df) + 1)
        df['title'] = title
        return df[['id', 'raw_name', 'position', 'title']]

    def cargar_excel(self, filepath: str) -> pd.DataFrame:
        logger.info("Cargando hoja 'Roster' desde Excel...")
        try:
            df = pd.read_excel(filepath, sheet_name="Roster", header=None)
            header_keywords = ['first name', 'last name', 'date of birth', 'positions']
            header_row_index = None

            for i, row in df.iterrows():
                row_str = [str(cell).strip().lower() for cell in row if pd.notna(cell)]
                if sum(hk in ' '.join(row_str) for hk in header_keywords) >= 2:
                    header_row_index = i
                    break

            if header_row_index is None:
                raise ValueError("No se encontró fila de encabezado válida en la hoja 'Roster'.")

            df_data = df.iloc[header_row_index:].copy()
            df_data.columns = [
                str(c).lower() if pd.notna(c) else f'unnamed_{i}'
                for i, c in enumerate(df_data.iloc[0])
            ]
            df_data = df_data[1:].reset_index(drop=True)
            logger.info("Hoja 'Roster' cargada correctamente")
            return self._extraer_nombres_y_posicion(df_data, 'roster')

        except ValueError as e:
            logger.warning(f"Falló la carga directa: {e}, intentando extraer por secciones...")
            secciones = self.extract_table_sections_from_excel(filepath)
            return pd.concat(secciones, ignore_index=True) if secciones else pd.DataFrame()

        except Exception as e:
            logger.error(f"Error al cargar hoja 'Roster', intentando extraer secciones... ({type(e).__name__}: {e})")
            secciones = self.extract_table_sections_from_excel(filepath)
            return pd.concat(secciones, ignore_index=True) if secciones else pd.DataFrame()

    # === PARTE 2: EXTRACCIÓN DE NOMBRES DESDE PDF ===
    def cargar_pdf(self, filepath: str) -> pd.DataFrame:
        logger.info(f"Extrayendo texto de PDF: {filepath}")
        with pdfplumber.open(filepath) as pdf:
            lines = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.splitlines())

        current_title = None
        nombres = []

        for line in lines:
            line_clean = line.strip()
            lower = line_clean.lower()
            if lower in ['catchers', 'pitchers', 'infielders', 'outfielders']:
                current_title = lower
                continue

            if current_title and len(line_clean.split()) >= 2:
                nombres.append({
                    'id': len(nombres) + 1,
                    'raw_name': line_clean,
                    'position': None,
                    'title': current_title
                })

        df = pd.DataFrame(nombres)
        logger.info(f"Extraídos {len(df)} nombres desde PDF")
        return df

    # === PARTE 3: COMPARACIÓN CON TRACKMAN ===
    def cargar_nombres_trackman(self, path_csv: str) -> List[str]:
        logger.info(f"Cargando nombres de Trackman desde: {path_csv}")
        df = pd.read_csv(path_csv)
        if 'nombre' not in df.columns:
            raise ValueError("El archivo CSV debe contener una columna llamada 'nombre'")
        nombres = [self.normalizar_nombre(n) for n in df['nombre'].astype(str).tolist()]
        logger.info(f"{len(nombres)} nombres cargados desde Trackman")
        return nombres

    def encontrar_similares(self, nombres_archivo: List[str], nombres_trackman: List[str], umbral: float = 90) -> List[Dict]:
        logger.info(f"Buscando coincidencias entre {len(nombres_archivo)} nombres de roster y Trackman...")
        coincidencias = []
        nombres_trackman_normalizados = {self.normalizar_nombre(n): n for n in nombres_trackman}

        for nombre in nombres_archivo:
            mejor_match = None
            mejor_score = 0
            algoritmo = None

            normalizado = self.normalizar_nombre(nombre)
            for nombre_track_norm, nombre_track_orig in nombres_trackman_normalizados.items():
                score = rapidfuzz.fuzz.ratio(normalizado, nombre_track_norm)
                if score > mejor_score:
                    mejor_score = score
                    mejor_match = nombre_track_orig
                    algoritmo = "rapidfuzz.ratio (normalizado)"

            if mejor_score < umbral:
                simplificado = self.simplificar_nombre(nombre)
                for nombre_track_norm, nombre_track_orig in nombres_trackman_normalizados.items():
                    score = rapidfuzz.fuzz.ratio(simplificado, self.simplificar_nombre(nombre_track_orig))
                    if score > mejor_score:
                        mejor_score = score
                        mejor_match = nombre_track_orig
                        algoritmo = "rapidfuzz.ratio (simplificado)"

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
        return coincidencias

    # === RESÚMENES Y PROCESAMIENTO FINAL ===
    def obtener_preview(self, df: pd.DataFrame) -> List[Dict]:
        return df.head(self.preview_rows).to_dict(orient='records')

    def generar_resumen(self, df: pd.DataFrame) -> Dict:
        total = len(df)
        if "position" in df.columns:
            posiciones = df['position'].fillna("").astype(str).str.strip().str.lower().value_counts().to_dict()
        else:
            posiciones = {}
        return {
            "total_jugadores": total,
            "posiciones": posiciones
        }

    def procesar_archivo(self, filepath: str, trackman_csv: str = None, umbral: float = 90) -> Dict:
        base = os.path.basename(filepath)
        logger.info(f"Procesando archivo: {base}")
        try:
            if filepath.endswith(('.xls', '.xlsx')):
                logger.info("Detectado archivo Excel")
                tabla = self.cargar_excel(filepath)
            elif filepath.endswith('.csv'):
                logger.info("Detectado archivo CSV")
                raw_df = pd.read_csv(filepath)
                tabla = self._extraer_nombres_y_posicion(raw_df, 'roster')
            elif filepath.endswith('.pdf'):
                logger.info("Detectado archivo PDF")
                tabla = self.cargar_pdf(filepath)
            else:
                raise ValueError("Tipo de archivo no soportado. Se aceptan .xls, .xlsx, .csv y .pdf.")

            if tabla.empty:
                logger.warning("No se extrajeron nombres del archivo")
                return {base: {"error": "Archivo sin datos válidos"}}

            if not trackman_csv:
                trackman_csv = os.path.join(os.path.dirname(__file__), "nombres_trackman.csv")

            nombres_trackman = self.cargar_nombres_trackman(trackman_csv)
            nombres_archivo = tabla['raw_name'].dropna().tolist()
            coincidencias = self.encontrar_similares(nombres_archivo, nombres_trackman, umbral=umbral)

            logger.info(f"Procesamiento completado: {len(coincidencias)} coincidencias evaluadas")
            return {
                base: {
                    "tables": self.obtener_preview(tabla),
                    "datos_extraidos": {
                        **self.generar_resumen(tabla),
                        "coincidencias_trackman": coincidencias
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error durante el procesamiento: {type(e).__name__} - {e}")
            return {base: {"error": f"Error al procesar archivo: {type(e).__name__} - {e}"}}

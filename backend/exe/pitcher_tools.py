# reports.py
import os
import re
import unicodedata
from typing import List, Optional, Dict, Any, Union

import pandas as pd
import numpy as np
import logging

from google.cloud import bigquery
import google.auth
from google.cloud import bigquery_storage

import batter_tools as bt
import pitcher_tools as pt

logger = logging.getLogger(__name__)

# borrar log
logger.info("Inicio de reports.py") # borrar log

# -------------------------------
# Utilidades
# -------------------------------

def clean_name(name: str) -> str:
    """Normaliza un nombre para su procesamiento."""
    # borrar log
    logger.debug(f"clean_name: Normalizando nombre: '{name}'") # borrar log
    if not name or str(name).strip() == "":
        # borrar log
        logger.debug("clean_name: Nombre vacío, regresando 'Sin_nombre'") # borrar log
        return "Sin_nombre"
    parts = [p.strip() for p in str(name).split(",")]
    rearranged = f"{parts[-1]} {parts[0]}".strip() if len(parts) >= 2 else parts[0]
    rearranged = " ".join(rearranged.title().split())
    normalized = unicodedata.normalize("NFKD", rearranged)
    result = "".join(c for c in normalized if not unicodedata.combining(c))
    # borrar log
    logger.debug(f"clean_name: Nombre normalizado a: '{result}'") # borrar log
    return result

def clean_directory(base_subdir: str, base_path: Optional[str] = None) -> None:
    """Limpia los archivos .png de un directorio de reportes."""
    # borrar log
    logger.info(f"clean_directory: Limpiando directorio {base_subdir}") # borrar log
    base_path = base_path or os.path.join("BaseballBatterPitcherReports", base_subdir)
    if not os.path.isdir(base_path):
        # borrar log
        logger.debug(f"clean_directory: Directorio no existe: {base_path}") # borrar log
        return

    for root, _, files in os.walk(base_path, topdown=False):
        for file in files:
            is_png = file.lower().endswith(".png")
            is_batter_non_spray = (base_subdir != "Pitcher") and ("spray_chart" not in file)
            if is_png and (base_subdir == "Pitcher" or is_batter_non_spray):
                try:
                    # borrar log
                    logger.debug(f"clean_directory: Eliminando archivo: {os.path.join(root, file)}") # borrar log
                    os.remove(os.path.join(root, file))
                except OSError:
                    logger.warning(f"No se pudo eliminar: {os.path.join(root, file)}")
                    # borrar log
                    logger.warning(f"clean_directory: Error de OS al eliminar {os.path.join(root, file)}") # borrar log
        try:
            if not os.listdir(root):
                # borrar log
                logger.debug(f"clean_directory: Eliminando directorio vacío: {root}") # borrar log
                os.rmdir(root)
        except OSError:
            # borrar log
            logger.warning(f"clean_directory: Error de OS al eliminar directorio {root}") # borrar log
            pass
    # borrar log
    logger.info(f"clean_directory: Limpieza de {base_subdir} finalizada") # borrar log


def _normalize_person_list(names: Optional[List[str]]) -> Optional[List[str]]:
    """Normaliza y elimina duplicados de una lista de nombres."""
    # borrar log
    logger.debug(f"_normalize_person_list: Normalizando lista de nombres con {len(names or [])} elementos") # borrar log
    if names is None:
        return None
    normed = [clean_name(str(n).strip()) for n in names if n]
    return sorted(list(set(normed)))

# -------------------------------
# Catálogos de equipos
# -------------------------------

dict_baseball_teams = {
    "SUL_MON": "Sultanes de Monterrey (Verano)", "GEN_MEX": "Generales de Durango",
    "ACE_MEX": "Acereros del Norte", "DIA_ROJ": "Diablos Rojos del México",
    "VAQ_LAG": "Algodoneros Unión Laguna", "AGU_VER": "El Aguila de Veracruz",
    "GUE_MEX": "Guerreros de Oaxaca", "MAR_GUA": "Mariachis de Guadalajara",
    "LEO_MEX": "Leones de Yucatán", "REI_MEX": "Rieleros de Aguascalientes",
    "PER_MEX": "Pericos de Puebla", "SAR_SAL": "Saraperos de Saltillo",
    "PIR_MEX": "Piratas de Campeche", "TIG_QUI": "Tigres de Quintana Roo",
    "TOR_TIJ": "Toros de Tijuana", "BRA_MEX": "Bravos de Leon",
    "OLM_MEX": "Olmecas de Tabasco", "ROJ_MEX": "Tecolotes de los Dos Laredos",
    "SUL_MON1": "Sultanes de Monterrey (Invierno)", "AGU_MEX": "Águilas de Mexicali",
    "CHA_JAL1": "Charros de Jalisco (Verano)", "CHA_JAL": "Charros de Jalisco (Invierno)",
    "YAQ_OBR": "Yaquis Ciudad Obregon", "HER": "Naranjeros de Hermosillo",
    "CAN_LOS": "Caneros Los Mochis", "VEN_MAZ": "Venados de Mazatlan",
    "TOM_CUL": "Tomateros de Culiacan", "ALG_GUA": "Algodoneros de Guasave",
    "MAY_NAV": "Mayos de Navajoa", "LMB_WIN6": "Pericos de Puebla",
    "DOR_CHI": "Dorados de Chihuahua", "CON_QUE": "Conspiradores de Queretaro",
    "MXC": "Aguilas de Mexicali", "RAM_ARA": "Ramón Arano", "NEL_BAR": "Nelson Barrera"
}

dict_baseball_teams_short = {
    "SUL_MON": "Monterrey (Verano)", "GEN_MEX": "Durango", "ACE_MEX": "Acereros_Norte",
    "DIA_ROJ": "México", "VAQ_LAG": "Unión_Laguna", "AGU_VER": "Veracruz",
    "GUE_MEX": "Oaxaca", "MAR_GUA": "Guadalajara", "LEO_MEX": "Yucatán",
    "REI_MEX": "Aguascalientes", "PER_MEX": "Puebla", "SAR_SAL": "Saltillo",
    "PIR_MEX": "Campeche", "TIG_QUI": "Quintana_Roo", "TOR_TIJ": "Tijuana",
    "BRA_MEX": "Leon", "OLM_MEX": "Tabasco", "ROJ_MEX": "Dos_Laredos",
    "SUL_MON1": "Monterrey (Invernal)", "AGU_MEX": "Mexicali", "CHA_JAL": "Jalisco (Invernal)",
    "CHA_JAL1": "Jalisco (Verano)", "YAQ_OBR": "Obregon", "HER": "Hermosillo",
    "CAN_LOS": "Los_Mochis", "VEN_MAZ": "Mazatlan", "TOM_CUL": "Culiacan",
    "ALG_GUA": "Guasave", "MAY_NAV": "Navajoa", "LMB_WIN6": "Puebla",
    "DOR_CHI": "Chihuahua", "CON_QUE": "Queretaro", "MXC": "Mexicali",
    "RAM_ARA": "Ramón Arano", "NEL_BAR": "Nelson Barrera"
}

# -------------------------------
# Columnas estándar y alias
# -------------------------------

STANDARD_COLUMNS = [
    "Angle", "AutoHitType", "AutoPitchType", "AwayTeam",
    "BatterId", "Batter", "BatterSide", "BatterTeam", "Bearing",
    "CatcherTeam", "Date", "Distance", "ExitSpeed", "HomeTeam", "HorzBreak", "KorBB",
    "InducedVertBreak", "PitcherId", "Pitcher", "PitcherTeam", "PitchCall", "PitcherThrows", "PitchofPA",
    "PlateLocHeight", "PlateLocSide", "PlayResult", "RelSpeed", "SpinRate", "Strikes", "Temporada",
    "Temporada_Anio", "id_path", "fecha_carga"
]

# alias de encabezados frecuentes en PDF/Excel
COL_ALIASES = {
    r"^batter\s*id$": "BatterId",
    r"^(batter|bateador|hitter|player)$": "Batter",
    r"^(batter\s*side|lado\s*bateador|side)$": "BatterSide",
    r"^(batter\s*team|equipo\s*bateador)$": "BatterTeam",
    r"^pitcher\s*id$": "PitcherId",
    r"^(pitcher|lanzador|thrower|pitcher\s*name)$": "Pitcher",
    r"^(pitcher\s*team|equipo\s*lanzador)$": "PitcherTeam",
    r"^(pitcher\s*throws|throws)$": "PitcherThrows",

    r"^auto\s*hit\s*type$": "AutoHitType",
    r"^auto\s*pitch\s*type$": "AutoPitchType",
    r"^pitch\s*call$": "PitchCall",
    r"^pitch\s*of\s*pa$": "PitchofPA",
    r"^plate\s*loc\s*height$": "PlateLocHeight",
    r"^plate\s*loc\s*side$": "PlateLocSide",
    r"^exit\s*speed$": "ExitSpeed",
    r"^rel\s*speed$": "RelSpeed",
    r"^spin\s*rate$": "SpinRate",
    r"^horz\s*break$": "HorzBreak",
    r"^induced\s*vert\s*break$": "InducedVertBreak",
    r"^bearing$": "Bearing",
    r"^angle$": "Angle",
    r"^distance$": "Distance",
    r"^korbb$": "KorBB",
    r"^strikes?$": "Strikes",
    r"^play\s*result$": "PlayResult",

    r"^away\s*team$": "AwayTeam",
    r"^home\s*team$": "HomeTeam",
    r"^catcher\s*team$": "CatcherTeam",
    r"^temporada$": "Temporada",
    r"^temporada[_\s-]*(año|anio)$": "Temporada_Anio",
    r"^id[_\s-]*path$": "id_path",
    r"^fecha[_\s-]*carga$": "fecha_carga",
    r"^date$": "Date",
}

# mapeos de valores típicos en PDF
BATTER_SIDE_ALIASES = {
    "l": "Left", "left": "Left", "izq": "Left", "i": "Left",
    "r": "Right", "right": "Right", "der": "Right", "d": "Right"
}

PITCHTYPE_ALIASES = {
    "four-seam": "Four-Seam",
    "four seam": "Four-Seam",
    "fs": "Four-Seam",
    "changeup": "Changeup",
    "cu": "Curveball",
    "curve": "Curveball",
    "curveball": "Curveball",
    "slider": "Slider",
    "sl": "Slider",
}

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra por alias, agrega faltantes, reordena y formatea tipos/valores."""
    # borrar log
    logger.debug("_normalize_columns: Iniciando normalización de columnas") # borrar log
    # renombrado por alias regex
    rename_map: Dict[str, str] = {}
    for col in list(df.columns):
        key = str(col or "").strip()
        k_norm = re.sub(r"\s+", " ", key).strip()
        for patt, target in COL_ALIASES.items():
            if re.match(patt, k_norm, flags=re.IGNORECASE):
                rename_map[col] = target
                break
    if rename_map:
        # borrar log
        logger.debug(f"_normalize_columns: Renombrando columnas: {rename_map}") # borrar log
        df = df.rename(columns=rename_map)

    # limpia espacios en nombres
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]

    # agrega columnas faltantes
    for c in STANDARD_COLUMNS:
        if c not in df.columns:
            # borrar log
            logger.debug(f"_normalize_columns: Agregando columna faltante: {c}") # borrar log
            df[c] = np.nan

    # reordena
    df = df[STANDARD_COLUMNS]
    # borrar log
    logger.debug("_normalize_columns: Columnas reordenadas") # borrar log

    # tipifica numéricas clave
    numeric_cols = ["ExitSpeed", "RelSpeed", "SpinRate", "Angle", "Distance",
                     "HorzBreak", "InducedVertBreak", "PitchofPA", "Strikes"]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # borrar log
    logger.debug("_normalize_columns: Columnas numéricas tipificadas") # borrar log

    # fechas
    if "fecha_carga" in df.columns:
        df["fecha_carga"] = pd.to_datetime(df["fecha_carga"], errors="coerce")
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    # borrar log
    logger.debug("_normalize_columns: Columnas de fecha tipificadas") # borrar log

    # normaliza valores de lado del bateador
    if "BatterSide" in df.columns:
        df["BatterSide"] = (
            df["BatterSide"].astype(str).str.strip().str.lower()
            .map(BATTER_SIDE_ALIASES).fillna(df["BatterSide"])
        )
    # borrar log
    logger.debug("_normalize_columns: 'BatterSide' normalizado") # borrar log

    # normaliza tipos de pitcheo básicos si vienen abreviados
    if "AutoPitchType" in df.columns:
        df["AutoPitchType"] = df["AutoPitchType"].astype(str).str.strip()
        df["AutoPitchType"] = (
            df["AutoPitchType"].str.lower().map(PITCHTYPE_ALIASES)
            .fillna(df["AutoPitchType"])
        )
    # borrar log
    logger.debug("_normalize_columns: 'AutoPitchType' normalizado") # borrar log

    # limpia nombres
    if "Batter" in df.columns:
        df["Batter"] = df["Batter"].apply(clean_name)
    if "Pitcher" in df.columns:
        df["Pitcher"] = df["Pitcher"].apply(clean_name)
    # borrar log
    logger.debug("_normalize_columns: Nombres de jugadores limpiados") # borrar log

    # bucket uniforme de tipos de pitcheo → auto_pitch_type_2
    MAP_PITCH_BUCKETS = {
        "Four-Seam": "Rectas y sinkers",
        "Two-Seam": "Rectas y sinkers",
        "Sinker": "Rectas y sinkers",
        "Cutter": "Cutters y Sliders",
        "Slider": "Cutters y Sliders",
        "Sweeper": "Cutters y Sliders",
        "Curveball": "Curvas",
        "Knuckle-Curve": "Curvas",
        "Changeup": "Cambios y Splits",
        "Splitter": "Cambios y Splits",
        "Split-Finger": "Cambios y Splits",
    }
    df["auto_pitch_type_2"] = df["AutoPitchType"].map(MAP_PITCH_BUCKETS).fillna("Other")
    # borrar log
    logger.debug("_normalize_columns: 'auto_pitch_type_2' creado") # borrar log
    
    # borrar log
    logger.info("_normalize_columns: Normalización de columnas finalizada") # borrar log
    return df


# -------------------------------
# Consulta BigQuery
# -------------------------------

BQ_DEFAULT_QUERY = """
SELECT 
    Angle, AutoHitType, AutoPitchType, AwayTeam,
    BatterId, Batter, BatterSide, BatterTeam, Bearing,
    CatcherTeam, Date, Distance, ExitSpeed, HomeTeam, HorzBreak, KorBB,
    InducedVertBreak, PitcherId, Pitcher, PitcherTeam, PitchCall, PitcherThrows, PitchofPA,
    PlateLocHeight, PlateLocSide, PlayResult, RelSpeed, SpinRate, Strikes, Temporada,
    Temporada_Anio, id_path, fecha_carga
FROM `baseballlmb.trackman_db.trackman_table`
WHERE Temporada_Anio IN (
    "Invierno-2025","Verano-2025",
    "Invierno-2024","Verano-2024"
)
"""

def load_trackman_dataframe(query: str = BQ_DEFAULT_QUERY) -> pd.DataFrame:
    """Carga datos desde BigQuery y aplica limpieza de nombres."""
    # borrar log
    logger.info("load_trackman_dataframe: Cargando datos desde BigQuery") # borrar log
    client = bigquery.Client()
    query_job = client.query(query)
    try:
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=credentials)
        # borrar log
        logger.debug("load_trackman_dataframe: Usando BigQueryReadClient para cargar DataFrame") # borrar log
        df = query_job.result().to_dataframe(bqstorage_client=bqstorageclient)
    except Exception:
        # borrar log
        logger.warning("load_trackman_dataframe: Fallo al usar BigQueryReadClient. Recurriendo a to_dataframe() normal.") # borrar log
        df = query_job.result().to_dataframe()
    if df.empty:
        # borrar log
        logger.error("load_trackman_dataframe: BigQuery devolvió un DataFrame vacío") # borrar log
        raise RuntimeError("BigQuery no devolvió registros.")
    if "Batter" in df.columns:
        df["Batter"] = df["Batter"].apply(clean_name)
    if "Pitcher" in df.columns:
        df["Pitcher"] = df["Pitcher"].apply(clean_name)
    # borrar log
    logger.info("load_trackman_dataframe: Carga desde BigQuery finalizada") # borrar log
    return df

# -------------------------------
# Carga desde PDF 
# -------------------------------
# crea identificadores únicos basados en el nombre cuando el PDF no trae BatterId o PitcherId
def _derive_ids_if_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Genera IDs determinísticos a partir de nombres cuando faltan en PDFs."""
    # borrar log
    logger.debug("_derive_ids_if_missing: Derivando IDs de jugadores si es necesario") # borrar log
    if "BatterId" in df.columns and df["BatterId"].isna().all() and "Batter" in df.columns:
        vals, _ = pd.factorize(df["Batter"].fillna("Sin_nombre"))
        df["BatterId"] = vals.astype("Int64")
        # borrar log
        logger.debug("_derive_ids_if_missing: IDs de Batter derivados") # borrar log
    if "PitcherId" in df.columns and df["PitcherId"].isna().all() and "Pitcher" in df.columns:
        vals, _ = pd.factorize(df["Pitcher"].fillna("Sin_nombre"))
        df["PitcherId"] = vals.astype("Int64")
        # borrar log
        logger.debug("_derive_ids_if_missing: IDs de Pitcher derivados") # borrar log
    return df
# asegura que fecha_carga tenga un valor válido, usando prioridad: la columna → columna Date → timestamp del archivo → fecha actual.
def _fill_fecha_carga(df: pd.DataFrame, source_path: Optional[str]) -> pd.DataFrame:
    """Asegura 'fecha_carga' válida para no filtrar todo al correr núcleos."""
    # borrar log
    logger.debug(f"_fill_fecha_carga: Rellenando 'fecha_carga' para el path: {source_path}") # borrar log
    if "fecha_carga" not in df.columns:
        df["fecha_carga"] = pd.NaT
    df["fecha_carga"] = pd.to_datetime(df["fecha_carga"], errors="coerce")
    
    # borrar log
    logger.debug(f"_fill_fecha_carga: 'fecha_carga' con {df['fecha_carga'].notna().sum()} valores no nulos") # borrar log
    if df["fecha_carga"].notna().any():
        return df

    if "Date" in df.columns and df["Date"].notna().any():
        df["fecha_carga"] = df["Date"]
        # borrar log
        logger.debug("_fill_fecha_carga: 'fecha_carga' rellenada desde 'Date'") # borrar log
        return df

    ts = None
    if source_path and os.path.isfile(source_path):
        try:
            ts = pd.to_datetime(os.path.getmtime(source_path), unit="s")
            # borrar log
            logger.debug(f"_fill_fecha_carga: 'fecha_carga' rellenada desde timestamp del archivo: {ts}") # borrar log
        except Exception:
            ts = None
            # borrar log
            logger.warning("_fill_fecha_carga: Fallo al obtener timestamp del archivo") # borrar log
    if ts is None:
        ts = pd.Timestamp("now").normalize()
        # borrar log
        logger.debug("_fill_fecha_carga: Usando fecha actual para 'fecha_carga'") # borrar log

    df["fecha_carga"] = ts
    return df
# 
def load_trackman_dataframe_from_pdf(pdf_paths: Union[str, List[str]]) -> pd.DataFrame:
    """
    Extrae tablas de PDF y normaliza al esquema estándar.
    No modifica la lógica de Excel existente.
    """
    # borrar log
    logger.info(f"load_trackman_dataframe_from_pdf: Iniciando carga desde PDF(s): {pdf_paths}") # borrar log
    try:
        import pdfplumber  # type: ignore
    except Exception as e:
        # borrar log
        logger.error("load_trackman_dataframe_from_pdf: Falta pdfplumber") # borrar log
        raise ImportError("Requiere 'pdfplumber' para leer PDF.") from e

    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]

    all_chunks: List[pd.DataFrame] = []

    for path in pdf_paths:
        # borrar log
        logger.debug(f"load_trackman_dataframe_from_pdf: Procesando archivo: {path}") # borrar log
        if not os.path.isfile(path):
            logger.warning(f"PDF no encontrado: {path}")
            # borrar log
            logger.warning(f"load_trackman_dataframe_from_pdf: Archivo no encontrado: {path}") # borrar log
            continue
        try:
            with pdfplumber.open(path) as pdf:
                # borrar log
                logger.debug(f"load_trackman_dataframe_from_pdf: Abriendo PDF con {len(pdf.pages)} páginas") # borrar log
                for page in pdf.pages:
                    # intenta varias estrategias de extracción
                    tables = page.extract_tables({"horizontal_strategy": "text", "vertical_strategy": "text"}) or []
                    if not tables:
                        tables = page.extract_tables() or []
                    # borrar log
                    logger.debug(f"load_trackman_dataframe_from_pdf: Página {page.page_number} tiene {len(tables)} tablas") # borrar log

                    for table in tables:
                        if not table or len(table) < 2:
                            # borrar log
                            logger.debug("load_trackman_dataframe_from_pdf: Tabla vacía o muy pequeña, omitiendo") # borrar log
                            continue

                        # identifica posible fila de encabezados: la primera no vacía con mayor diversidad
                        candidate_headers = [row for row in table[:3] if row and any(cell for cell in row)]
                        header = max(candidate_headers, key=lambda r: len([c for c in r if c not in [None, ""]]), default=table[0])
                        rows = [r for r in table if r is not header]

                        # descarta filas vacías
                        rows = [r for r in rows if any((cell is not None and str(cell).strip() != "") for cell in r)]
                        if not rows:
                            # borrar log
                            logger.debug("load_trackman_dataframe_from_pdf: No hay filas de datos, omitiendo tabla") # borrar log
                            continue

                        # normaliza longitudes
                        max_len = max(len(header), *(len(r) for r in rows))
                        header = list(header) + [f"col_{i}" for i in range(len(header), max_len)]
                        norm_rows = [list(r) + [np.nan] * (max_len - len(r)) for r in rows]
                        # borrar log
                        logger.debug(f"load_trackman_dataframe_from_pdf: Tabla con {len(norm_rows)} filas y {len(header)} columnas") # borrar log

                        df_tbl = pd.DataFrame(norm_rows, columns=header)

                        # elimina filas que repiten el header
                        df_tbl = df_tbl[~df_tbl.apply(lambda r: all(str(r.iloc[i]).strip() == str(df_tbl.columns[i]).strip() for i in range(len(df_tbl.columns))), axis=1)]


                        # normaliza columnas y valores
                        df_tbl = _normalize_columns(df_tbl)

                        # rellenos clave para no perder filas al filtrar en los núcleos
                        df_tbl = _derive_ids_if_missing(df_tbl)
                        df_tbl = _fill_fecha_carga(df_tbl, source_path=path)

                        # quita filas totalmente vacías de nombres
                        if {"Batter", "Pitcher"} <= set(df_tbl.columns):
                            df_tbl = df_tbl[df_tbl["Batter"].notna() | df_tbl["Pitcher"].notna()]
                            # borrar log
                            logger.debug(f"load_trackman_dataframe_from_pdf: Tabla filtrada por nombre, quedan {len(df_tbl)} filas") # borrar log

                        if not df_tbl.empty:
                            all_chunks.append(df_tbl)

        except Exception as e:
            logger.warning(f"Error leyendo PDF {path}: {e}")
            # borrar log
            logger.error(f"load_trackman_dataframe_from_pdf: Fallo al leer PDF {path}: {e}") # borrar log
            continue

    if not all_chunks:
        # borrar log
        logger.warning("load_trackman_dataframe_from_pdf: No se extrajeron tablas de ningún PDF. Regresando DataFrame vacío.") # borrar log
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    df = pd.concat(all_chunks, ignore_index=True, sort=False)
    # limpieza final
    df = _normalize_columns(df)
    df = _derive_ids_if_missing(df)
    df = _fill_fecha_carga(df, source_path=None)
    
    # borrar log
    logger.info(f"load_trackman_dataframe_from_pdf: Carga desde PDF finalizada. Total de filas: {len(df)}") # borrar log
    return df

# -------------------------------
# Núcleo Batter
# -------------------------------
def _run_batter_reports_core(df: pd.DataFrame,
                             batter_filter: Optional[List[str]] = None,
                             work_dir: Optional[str] = None,
                             clean_temp: bool = True) -> Dict[str, Any]:
    """Genera reportes para bateadores, compatible con batter_tools original."""
    # borrar log
    logger.info("_run_batter_reports_core: Iniciando generación de reportes para bateadores") # borrar log
    df_games = df.copy()
    print("\n--- DEPURACIÓN: BATTER REPORTS ---")
    print("Filas totales al inicio:", len(df_games))
    # borrar log
    logger.debug(f"_run_batter_reports_core: Filas totales al inicio: {len(df_games)}") # borrar log

    if batter_filter:
        df_games = df_games[df_games.Batter.isin(batter_filter)]
        print("Tras aplicar batter_filter:", len(df_games))
        # borrar log
        logger.debug(f"_run_batter_reports_core: Filas tras aplicar filtro: {len(df_games)}") # borrar log

    df_games.dropna(subset=["BatterId"], inplace=True)
    print("Tras eliminar BatterId nulos:", len(df_games))
    # borrar log
    logger.debug(f"_run_batter_reports_core: Filas tras eliminar BatterId nulos: {len(df_games)}") # borrar log

    df_games = df_games[df_games.fecha_carga.notna() & (df_games.fecha_carga != "-")]
    print("Tras filtrar fecha_carga no nula:", len(df_games))
    # borrar log
    logger.debug(f"_run_batter_reports_core: Filas tras filtrar fecha_carga no nula: {len(df_games)}") # borrar log

    df_games["fecha_carga"] = pd.to_datetime(df_games["fecha_carga"], errors="coerce")
    df_games = df_games[df_games["fecha_carga"].notna()]
    print("Tras convertir fecha_carga a datetime:", len(df_games))
    # borrar log
    logger.debug(f"_run_batter_reports_core: Filas tras convertir fecha_carga a datetime: {len(df_games)}") # borrar log

    if df_games.empty:
        print("Resultado final: DataFrame vacío. No se generarán reportes.")
        # borrar log
        logger.warning("_run_batter_reports_core: DataFrame final vacío. No se generarán reportes") # borrar log
        if clean_temp:
            base = os.path.join(work_dir, "Batter") if work_dir else None
            clean_directory("Batter", base)
        return {"processed": 0, "generated": 0, "paths": []}

    df_stats = bt.create_stats_table(df_games)
    nombres = df_stats.index.tolist()

    print(f"Total de bateadores con estadísticas: {len(nombres)}")
    # borrar log
    logger.info(f"_run_batter_reports_core: Se encontraron {len(nombres)} bateadores para procesar") # borrar log

    generated, artefactos = 0, []
    for name in nombres:
        try:
            # borrar log
            logger.debug(f"_run_batter_reports_core: Generando reporte para bateador: {name}") # borrar log
            r = bt.create_report_full(
                batter_name=name,
                df_stats=df_stats,
                df_games=df_games,
                dict_short=dict_baseball_teams_short,
                work_dir=work_dir
            )
            if r:
                artefactos.append(r)
            generated += 1
            # borrar log
            logger.debug(f"_run_batter_reports_core: Reporte para {name} generado exitosamente") # borrar log
        except Exception as e:
            logger.warning(f"Error al generar reporte de bateador para {name}: {e}")
            # borrar log
            logger.error(f"_run_batter_reports_core: Fallo al generar reporte para {name}: {e}") # borrar log
            continue

    if clean_temp:
        base = os.path.join(work_dir, "Batter") if work_dir else None
        clean_directory("Batter", base)

    # borrar log
    logger.info(f"_run_batter_reports_core: Generación de reportes de bateadores finalizada. Procesados: {len(nombres)}, Generados: {generated}") # borrar log
    return {"processed": len(nombres), "generated": generated, "paths": artefactos}

# -------------------------------
# Núcleo Pitcher
# -------------------------------

def _run_pitcher_reports_core(df: pd.DataFrame,
                              pitcher_filter: Optional[List[str]] = None,
                              work_dir: Optional[str] = None,
                              clean_temp: bool = True) -> Dict[str, Any]:
    """Genera reportes para lanzadores, compatible con pitcher_tools original."""
    # borrar log
    logger.info("_run_pitcher_reports_core: Iniciando generación de reportes para lanzadores") # borrar log
    df_games = df.copy()
    if pitcher_filter:
        df_games = df_games[df_games.Pitcher.isin(pitcher_filter)]
    
    # borrar log
    logger.debug(f"_run_pitcher_reports_core: Filas después de aplicar filtro: {len(df_games)}") # borrar log

    df_games = df_games[df_games.BatterSide.isin(["Left", "Right"])]
    df_games.dropna(subset=["Pitcher"], inplace=True)
    df_games = df_games[df_games.fecha_carga.notna() & (df_games.fecha_carga != "-")]
    df_games["fecha_carga"] = pd.to_datetime(df_games["fecha_carga"], errors="coerce")
    df_games = df_games[df_games["fecha_carga"].notna()]
    # borrar log
    logger.debug(f"_run_pitcher_reports_core: Filas después de filtrado y limpieza: {len(df_games)}") # borrar log

    if df_games.empty:
        # borrar log
        logger.warning("_run_pitcher_reports_core: DataFrame final vacío. No se generarán reportes") # borrar log
        if clean_temp:
            base = os.path.join(work_dir, "Pitcher") if work_dir else None
            clean_directory("Pitcher", base)
        return {"processed": 0, "generated": 0, "paths": []}

    df_table = df_games.copy()

    dict_launch = {"Four-Seam": "Rectas", "Changeup": "Cambios", "Curveball": "Curva"}
    df_table["AutoPitchType"] = df_table.AutoPitchType.apply(lambda x: dict_launch.get(str(x), x))
    # borrar log
    logger.debug("_run_pitcher_reports_core: Mapeo de tipos de pitcheo realizado") # borrar log

    cond1 = df_table["PitchofPA"] == 1
    cond2 = pd.Series(True, index=df_table.index)
    cond3 = df_table["Strikes"] == 2
    dict_cond = {"1er Pitcheo": cond1, "General": cond2, "2 Strikes": cond3}

    dict_df_cond: Dict[int, pd.DataFrame] = {}
    for i, cond in enumerate(dict_cond.values(), start=1):
        df_cond = df_table[cond]
        if df_cond.empty:
            dict_df_cond[i] = pd.DataFrame()
            # borrar log
            logger.debug(f"_run_pitcher_reports_core: Condición {i} resultó en un DataFrame vacío") # borrar log
        else:
            df_temp_num = df_cond.groupby(["Pitcher", "BatterSide", "AutoPitchType"]).size()
            dict_df_cond[i] = df_temp_num.unstack(1)
            # borrar log
            logger.debug(f"_run_pitcher_reports_core: Condición {i} procesada, DataFrame con {len(df_temp_num)} filas") # borrar log

    name_pitchers = sorted(df_table.Pitcher.dropna().unique().tolist())
    generated, artefactos = 0, []
    # borrar log
    logger.info(f"_run_pitcher_reports_core: Se encontraron {len(name_pitchers)} lanzadores para procesar") # borrar log

    for name in name_pitchers:
        try:
            # borrar log
            logger.debug(f"_run_pitcher_reports_core: Generando reporte para lanzador: {name}") # borrar log
            r = pt.create_report_full(
                pitcher_name=name,
                dict_df_cond=dict_df_cond,
                dict_cond=dict_cond,
                dict_short=dict_baseball_teams_short,
                df_table=df_table,
                work_dir=work_dir
            )
            if r:
                artefactos.append(r)
            generated += 1
            # borrar log
            logger.debug(f"_run_pitcher_reports_core: Reporte para {name} generado exitosamente") # borrar log
        except Exception as e:
            logger.warning(f"Error al generar reporte de lanzador para {name}: {e}")
            # borrar log
            logger.error(f"_run_pitcher_reports_core: Fallo al generar reporte para {name}: {e}") # borrar log
            continue

    if clean_temp:
        base = os.path.join(work_dir, "Pitcher") if work_dir else None
        clean_directory("Pitcher", base)

    # borrar log
    logger.info(f"_run_pitcher_reports_core: Generación de reportes de lanzadores finalizada. Procesados: {len(name_pitchers)}, Generados: {generated}") # borrar log
    return {"processed": len(name_pitchers), "generated": generated, "paths": artefactos}

# -------------------------------
# API pública compatible con GUI
# -------------------------------

def run_batter_reports(arg1: Union[pd.DataFrame, List[str]],
                       df: Optional[pd.DataFrame] = None,
                       work_dir: Optional[str] = None,
                       clean_temp: bool = True) -> Dict[str, Any]:
    """Genera reportes de bateadores. Puede recibir un DataFrame o una lista de nombres."""
    # borrar log
    logger.info("run_batter_reports: Llamada a la API pública de reportes de bateadores") # borrar log
    if isinstance(arg1, pd.DataFrame):
        # borrar log
        logger.debug("run_batter_reports: arg1 es un DataFrame. Llamando a _run_batter_reports_core con DataFrame.") # borrar log
        return _run_batter_reports_core(arg1, batter_filter=None, work_dir=work_dir, clean_temp=clean_temp)
    nombres: List[str] = arg1 or []
    if df is None:
        # borrar log
        logger.debug("run_batter_reports: df es None. Cargando datos desde BigQuery.") # borrar log
        df = load_trackman_dataframe()
    # borrar log
    logger.debug("run_batter_reports: Llamando a _run_batter_reports_core con filtro de nombres.") # borrar log
    return _run_batter_reports_core(df, batter_filter=_normalize_person_list(nombres), work_dir=work_dir, clean_temp=clean_temp)

def run_pitcher_reports(arg1: Union[pd.DataFrame, List[str]],
                        df: Optional[pd.DataFrame] = None,
                        work_dir: Optional[str] = None,
                        clean_temp: bool = True) -> Dict[str, Any]:
    """Genera reportes de lanzadores. Puede recibir un DataFrame o una lista de nombres."""
    # borrar log
    logger.info("run_pitcher_reports: Llamada a la API pública de reportes de lanzadores") # borrar log
    if isinstance(arg1, pd.DataFrame):
        # borrar log
        logger.debug("run_pitcher_reports: arg1 es un DataFrame. Llamando a _run_pitcher_reports_core con DataFrame.") # borrar log
        return _run_pitcher_reports_core(arg1, pitcher_filter=None, work_dir=work_dir, clean_temp=clean_temp)
    nombres: List[str] = arg1 or []
    if df is None:
        # borrar log
        logger.debug("run_pitcher_reports: df es None. Cargando datos desde BigQuery.") # borrar log
        df = load_trackman_dataframe()
    # borrar log
    logger.debug("run_pitcher_reports: Llamando a _run_pitcher_reports_core con filtro de nombres.") # borrar log
    return _run_pitcher_reports_core(df, pitcher_filter=_normalize_person_list(nombres), work_dir=work_dir, clean_temp=clean_temp)

# -------------------------------
# Main (como librería)
# -------------------------------

def main(df: Optional[pd.DataFrame] = None,
         query: str = BQ_DEFAULT_QUERY,
         batter_filter: Optional[List[str]] = None,
         pitcher_filter: Optional[List[str]] = None,
         work_dir: Optional[str] = None,
         clean_temp: bool = True) -> Dict[str, Dict[str, Any]]:
    """Función principal para generar reportes de bateadores y lanzadores."""
    # borrar log
    logger.info("main: Iniciando función principal") # borrar log
    if df is None:
        # borrar log
        logger.debug("main: df es None. Cargando datos desde BigQuery.") # borrar log
        df = load_trackman_dataframe(query=query)

    batter_summary = _run_batter_reports_core(
        df, batter_filter=_normalize_person_list(batter_filter), work_dir=work_dir, clean_temp=clean_temp
    )
    # borrar log
    logger.info("main: Reportes de bateadores generados") # borrar log
    
    pitcher_summary = _run_pitcher_reports_core(
        df, pitcher_filter=_normalize_person_list(pitcher_filter), work_dir=work_dir, clean_temp=clean_temp
    )
    # borrar log
    logger.info("main: Reportes de lanzadores generados") # borrar log

    result = {
        "batter": {
            "processed": int(batter_summary.get("processed", 0)),
            "generated": int(batter_summary.get("generated", 0)),
            "paths": batter_summary.get("paths", []),
        },
        "pitcher": {
            "processed": int(pitcher_summary.get("processed", 0)),
            "generated": int(pitcher_summary.get("generated", 0)),
            "paths": pitcher_summary.get("paths", []),
        },
    }
    # borrar log
    logger.info("main: Función principal finalizada") # borrar log
    return result
# reports.py
import os
import glob
import unicodedata
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np
import logging

from google.cloud import bigquery
import google.auth
from google.cloud import bigquery_storage

import batter_tools as bt
import pitcher_tools as pt

logger = logging.getLogger(__name__)

# -------------------------------
# Utilidades
# -------------------------------

def clean_name(name: str) -> str:
    if not name:
        return "Sin_nombre"
    parts = [p.strip() for p in str(name).split(",")]
    if len(parts) >= 2:
        rearranged = f"{parts[-1]} {parts[0]}".strip()
    else:
        rearranged = parts[0]
    rearranged = " ".join(rearranged.title().split())
    normalized = unicodedata.normalize("NFKD", rearranged)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def clean_directory(base_subdir: str, base_path: Optional[str] = None) -> None:
    """
    Elimina PNG temporales generados en los reportes.
    base_subdir: 'Batter' o 'Pitcher'
    base_path: ruta base para subdirectorios; si no se da, usa 'BaseballBatterPitcherReports/<base_subdir>'
    """
    base_path = base_path or os.path.join("BaseballBatterPitcherReports", base_subdir)
    if not os.path.isdir(base_path):
        return

    for removed_dir in glob.glob(os.path.join(base_path, "*")):
        if not os.path.isdir(removed_dir):
            continue

        if base_subdir == "Pitcher":
            # Borra todos los .png y remueve carpetas vacías
            for root, _, files in os.walk(removed_dir, topdown=False):
                for file in files:
                    if file.lower().endswith(".png"):
                        try:
                            os.remove(os.path.join(root, file))
                        except OSError:
                            pass
                try:
                    if not os.listdir(root):
                        os.rmdir(root)
                except OSError:
                    pass
        else:
            # Batter: conserva spray_chart*.png
            for root, _, files in os.walk(removed_dir, topdown=False):
                for file in files:
                    if file.lower().endswith(".png") and "spray_chart" not in file:
                        try:
                            os.remove(os.path.join(root, file))
                        except OSError:
                            pass


def _normalize_person_list(names: Optional[List[str]]) -> Optional[List[str]]:
    """
    Normaliza lista de nombres para que coincida con el formato de Trackman en DF:
    Title Case + sin acentos/diacríticos.
    """
    if names is None:
        return None
    normed = [clean_name(str(n).strip()) for n in names if n]
    seen = set()
    out = []
    for n in normed:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


# -------------------------------
# Catálogos de equipos
# -------------------------------

dict_baseball_teams = {
    "SUL_MON": "Sultanes de Monterrey (Verano)",
    "GEN_MEX": "Generales de Durango",
    "ACE_MEX": "Acereros del Norte",
    "DIA_ROJ": "Diablos Rojos del México",
    "VAQ_LAG": "Algodoneros Unión Laguna",
    "AGU_VER": "El Aguila de Veracruz",
    "GUE_MEX": "Guerreros de Oaxaca",
    "MAR_GUA": "Mariachis de Guadalajara",
    "LEO_MEX": "Leones de Yucatán",
    "REI_MEX": "Rieleros de Aguascalientes",
    "PER_MEX": "Pericos de Puebla",
    "SAR_SAL": "Saraperos de Saltillo",
    "PIR_MEX": "Piratas de Campeche",
    "TIG_QUI": "Tigres de Quintana Roo",
    "TOR_TIJ": "Toros de Tijuana",
    "BRA_MEX": "Bravos de Leon",
    "OLM_MEX": "Olmecas de Tabasco",
    "ROJ_MEX": "Tecolotes de los Dos Laredos",
    "SUL_MON1": "Sultanes de Monterrey (Invierno)",
    "AGU_MEX": "Águilas de Mexicali",
    "CHA_JAL1": "Charros de Jalisco (Verano)",
    "CHA_JAL": "Charros de Jalisco (Invierno)",
    "YAQ_OBR": "Yaquis Ciudad Obregon",
    "HER": "Naranjeros de Hermosillo",
    "CAN_LOS": "Caneros Los Mochis",
    "VEN_MAZ": "Venados de Mazatlan",
    "TOM_CUL": "Tomateros de Culiacan",
    "ALG_GUA": "Algodoneros de Guasave",
    "MAY_NAV": "Mayos de Navajoa",
    "LMB_WIN6": "Pericos de Puebla",
    "DOR_CHI": "Dorados de Chihuahua",
    "CON_QUE": "Conspiradores de Queretaro",
    "MXC": "Aguilas de Mexicali",
    "RAM_ARA": "Ramón Arano",
    "NEL_BAR": "Nelson Barrera",
}

dict_baseball_teams_short = {
    "SUL_MON": "Monterrey (Verano)",
    "GEN_MEX": "Durango",
    "ACE_MEX": "Acereros_Norte",
    "DIA_ROJ": "México",
    "VAQ_LAG": "Unión_Laguna",
    "AGU_VER": "Veracruz",
    "GUE_MEX": "Oaxaca",
    "MAR_GUA": "Guadalajara",
    "LEO_MEX": "Yucatán",
    "REI_MEX": "Aguascalientes",
    "PER_MEX": "Puebla",
    "SAR_SAL": "Saltillo",
    "PIR_MEX": "Campeche",
    "TIG_QUI": "Quintana_Roo",
    "TOR_TIJ": "Tijuana",
    "BRA_MEX": "Leon",
    "OLM_MEX": "Tabasco",
    "ROJ_MEX": "Dos_Laredos",
    "SUL_MON1": "Monterrey (Invernal)",
    "AGU_MEX": "Mexicali",
    "CHA_JAL": "Jalisco (Invernal)",
    "CHA_JAL1": "Jalisco (Verano)",
    "YAQ_OBR": "Obregon",
    "HER": "Hermosillo",
    "CAN_LOS": "Los_Mochis",
    "VEN_MAZ": "Mazatlan",
    "TOM_CUL": "Culiacan",
    "ALG_GUA": "Guasave",
    "MAY_NAV": "Navajoa",
    "LMB_WIN6": "Puebla",
    "DOR_CHI": "Chihuahua",
    "CON_QUE": "Queretaro",
    "MXC": "Mexicali",
    "RAM_ARA": "Ramón Arano",
    "NEL_BAR": "Nelson Barrera",
}

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
    """
    Carga datos desde BigQuery.
    Requiere GOOGLE_APPLICATION_CREDENTIALS o entorno autenticado.
    """
    client = bigquery.Client()
    query_job = client.query(query)

    # Usar BigQuery Storage si está disponible
    try:
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=credentials)
        df = query_job.result().to_dataframe(bqstorage_client=bqstorageclient)
    except Exception:
        df = query_job.result().to_dataframe()

    if df.empty:
        raise RuntimeError("BigQuery no devolvió registros.")

    # Normalización de nombres
    if "Batter" in df.columns:
        df["Batter"] = df["Batter"].apply(clean_name)
    if "Pitcher" in df.columns:
        df["Pitcher"] = df["Pitcher"].apply(clean_name)

    return df

# -------------------------------
# Flujo Batter
# -------------------------------

def run_batter_reports(df: pd.DataFrame,
                       batter_filter: Optional[List[str]] = None,
                       work_dir: Optional[str] = None,
                       clean_temp: bool = True) -> Dict[str, Any]:
    df_games = df.copy()
    df_games.dropna(subset=["BatterId"], inplace=True)

    batter_filter = _normalize_person_list(batter_filter)
    if batter_filter:
        df_games = df_games[df_games.Batter.isin(batter_filter)]

    df_games = df_games[df_games.fecha_carga.notna() & (df_games.fecha_carga != "-")]
    df_games["fecha_carga"] = pd.to_datetime(df_games["fecha_carga"], errors="coerce")
    df_games = df_games[df_games["fecha_carga"].notna()]

    if df_games.empty:
        if clean_temp:
            base = os.path.join(work_dir, "Batter") if work_dir else None
            clean_directory("Batter", base)
        return {"processed": 0, "generated": 0, "paths": []}

    df_stats = bt.create_stats_table(df_games)

    dict_pitchtype = {
        "Four-Seam": "Rectas y sinkers",
        "Sinker": "Rectas y sinkers",
        "Cutter": "Cutters y Sliders",
        "Slider": "Cutters y Sliders",
        "Curveball": "Curvas",
        "Changeup": "Cambios y Splits",
        "Splitter": "Cambios y Splits",
    }
    df_games["auto_pitch_type_2"] = df_games.AutoPitchType.map(dict_pitchtype)
    df_games.dropna(subset=["auto_pitch_type_2"], inplace=True)

    nombres = df_stats.index.tolist()
    generated = 0
    artefactos: List[str] = []

    for nombre in nombres:
        try:
            path = bt.create_report_full(
                nombre, df_stats, df_games, dict_baseball_teams_short,
                work_dir=work_dir
            )
            if path:
                artefactos.append(path)
            generated += 1
        except TypeError:
            try:
                path = bt.create_report_full(nombre, df_stats, df_games, dict_baseball_teams_short)
                if path:
                    artefactos.append(path)
                generated += 1
            except FileNotFoundError:
                continue
        except FileNotFoundError:
            continue

    if clean_temp:
        base = os.path.join(work_dir, "Batter") if work_dir else None
        clean_directory("Batter", base)
    return {"processed": len(nombres), "generated": generated, "paths": artefactos}

# -------------------------------
# Flujo Pitcher
# -------------------------------

def run_pitcher_reports(df: pd.DataFrame,
                        pitcher_filter: Optional[List[str]] = None,
                        work_dir: Optional[str] = None,
                        clean_temp: bool = True) -> Dict[str, Any]:
    df_games = df.copy()

    pitcher_filter = _normalize_person_list(pitcher_filter)
    if pitcher_filter:
        df_games = df_games[df_games.Pitcher.isin(pitcher_filter)]

    df_games = df_games[df_games.BatterSide.isin(["Left", "Right"])]
    df_games.dropna(subset=["Pitcher"], inplace=True)
    df_games = df_games[df_games.fecha_carga.notna() & (df_games.fecha_carga != "-")]
    df_games["fecha_carga"] = pd.to_datetime(df_games["fecha_carga"], errors="coerce")
    df_games = df_games[df_games["fecha_carga"].notna()]

    if df_games.empty:
        if clean_temp:
            base = os.path.join(work_dir, "Pitcher") if work_dir else None
            clean_directory("Pitcher", base)
        return {"processed": 0, "generated": 0, "paths": []}

    df_table = df_games.copy()

    dict_launch = {"Four-Seam": "Rectas", "Changeup": "Cambios", "Curveball": "Curva"}
    df_table["AutoPitchType"] = df_table.AutoPitchType.apply(lambda x: dict_launch.get(x, x))

    cond1 = df_table["PitchofPA"] == 1
    cond2 = pd.Series(True, index=df_table.index)  # máscara general
    cond3 = df_table["Strikes"] == 2

    dict_cond = {"1er Pitcheo": cond1, "General": cond2, "2 Strikes": cond3}
    dict_df_cond: Dict[int, pd.DataFrame] = {}
    for i, cond in enumerate(dict_cond.values(), start=1):
        df_cond = df_table[cond]
        if df_cond.empty:
            dict_df_cond[i] = pd.DataFrame()
            continue
        df_temp_num = df_cond.groupby(["Pitcher", "BatterSide", "AutoPitchType"]).size()
        dict_df_cond[i] = df_temp_num.unstack(1)

    df_table["team_pitcher"] = df_table.PitcherTeam.map(dict_baseball_teams)
    dict_pitchtype = {
        "Rectas": "Rectas y sinkers",
        "Sinker": "Rectas y sinkers",
        "Cutter": "Cutters y Sliders",
        "Slider": "Cutters y Sliders",
        "Curva": "Curvas",
        "Cambios": "Cambios y Splits",
        "Splitter": "Cambios y Splits",
    }
    df_table["auto_pitch_type_2"] = df_table.AutoPitchType.map(dict_pitchtype)

    name_pitchers = sorted(df_table.Pitcher.dropna().unique().tolist())
    generated = 0
    artefactos: List[str] = []

    for name in name_pitchers:
        try:
            path = pt.create_report_full(
                df_table, name, dict_df_cond, dict_cond, dict_baseball_teams_short,
                work_dir=work_dir
            )
            if path:
                artefactos.append(path)
            generated += 1
        except TypeError:
            try:
                path = pt.create_report_full(df_table, name, dict_df_cond, dict_cond, dict_baseball_teams_short)
                if path:
                    artefactos.append(path)
                generated += 1
            except KeyError:
                continue
        except KeyError:
            continue

    if clean_temp:
        base = os.path.join(work_dir, "Pitcher") if work_dir else None
        clean_directory("Pitcher", base)
    return {"processed": len(name_pitchers), "generated": generated, "paths": artefactos}

# -------------------------------
# Main (como librería)
# -------------------------------

def main(df: Optional[pd.DataFrame] = None,
         query: str = BQ_DEFAULT_QUERY,
         batter_filter: Optional[List[str]] = None,
         pitcher_filter: Optional[List[str]] = None,
         work_dir: Optional[str] = None,
         clean_temp: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Retorna un resumen con cantidades procesadas y generadas por tipo de reporte.
    Si df es None, carga datos vía BigQuery.
    """
    if df is None:
        df = load_trackman_dataframe(query=query)

    batter_summary = run_batter_reports(df, batter_filter=batter_filter, work_dir=work_dir, clean_temp=clean_temp)
    pitcher_summary = run_pitcher_reports(df, pitcher_filter=pitcher_filter, work_dir=work_dir, clean_temp=clean_temp)

    return {
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


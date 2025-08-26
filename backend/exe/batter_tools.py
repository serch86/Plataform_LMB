import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import fpdf
from functools import reduce
from typing import Tuple, Optional
import logging # borrar log

from spray_charts_f import spray_probability_conditional
import dataframe_image as dfi


# Strike zone aprox. (en pies). Ajusta a tu criterio/ligas.
_x_low, _x_high = -0.85, 0.85
_y_low, _y_high =  1.50, 3.50

# Bins para mapas/tablas (8x8 típico)
_xbin = np.linspace(_x_low, _x_high, 9)
_ybin = np.linspace(_y_low, _y_high, 9)

# ancho “medio” de la zona (para dibujar y checks simétricos)
_x_radio = max(abs(_x_low), abs(_x_high))

# líneas auxiliares para trazar el marco en heatmaps
_x_lin = np.linspace(1, 4, 10)
_y_lin = np.linspace(1, 4, 10)

# rutas base usadas por ensure_home_plate_asset() y create_report()
BASE = getattr(sys, "_MEIPASS", os.getcwd())
DIR_HOMEPLATE = os.path.join(BASE, "BaseballBatterPitcherReports", "assets")
DIR_TEMP = os.path.join(os.path.expanduser("~"), "BaseballBatterPitcherReports", "Batter")

logger = logging.getLogger(__name__) # borrar log
logger.setLevel(logging.DEBUG) # borrar log


# --- arriba de _notify_skip ---
_gui_logger = None

def set_gui_logger(func):
    """La GUI inyecta aquí su función de log (App._log)."""
    global _gui_logger
    _gui_logger = func

# --- sustituye tu _notify_skip por este ---
def _notify_skip(graph_name: str, batter: str, side: str | None = None, reason: str = "falta de datos"):
    msg = f"LOG: No se generó '{graph_name}' para {batter}" + (f" (side={side})" if side else "") + f" — {reason}."
    if _gui_logger:
        try:
            _gui_logger(msg)  # manda el mensaje a la consola de la GUI
        except Exception:
            print(msg)
    else:
        print(msg)  # fallback si no hay GUI

    try:
        logger.warning(msg)
    except Exception:
        pass


# -------------------------------------------
# Utilidades y cálculos
# -------------------------------------------

def ensure_pitch_types(df: pd.DataFrame, col_out: str = "auto_pitch_type_2") -> pd.DataFrame:
    df = df.copy()
    if col_out not in df.columns:
        df[col_out] = None
    src = "AutoPitchType" if "AutoPitchType" in df.columns else None
    if src:
        norm = df[src].astype(str).str.strip().str.lower()
        fb = {"four-seam","four seam","ff","fourseam","four-seam fastball","fastball","fb"}
        sink = {"sinker","sink","si","two-seam","two seam","ft","twoseam","2-seam","2 seam"}
        df.loc[norm.isin(fb | sink), col_out] = "Rectas y sinkers"
        # rellena el resto con el valor original
        df.loc[df[col_out].isna(), col_out] = df.loc[df[col_out].isna(), src]
    else:
        df[col_out] = df[col_out].fillna("ALL")
    return df

def ensure_home_plate_asset() -> str:
    """Devuelve la ruta del asset de home plate; si no existe, crea un placeholder PNG."""
    p_jpg = os.path.join(DIR_HOMEPLATE, 'home_plate.jpg')
    p_png = os.path.join(DIR_HOMEPLATE, 'home_plate.png')
    if os.path.exists(p_jpg):
        return p_jpg
    if os.path.exists(p_png):
        return p_png

    print("[WARN] No se encontró el asset de home plate. Creando uno temporal.")
    try: logger.warning("No se encontró el asset de home plate. Creando uno temporal.")
    except Exception: pass

    # Crear placeholder simple
    fig = plt.figure(figsize=(1.2, 1.0), dpi=200)
    ax = plt.gca()
    ax.axis('off')
    poly = plt.Polygon([(0.3, 0.05), (0.7, 0.05), (0.9, 0.3), (0.5, 0.95), (0.1, 0.3)],
                       fill=False, linewidth=3, edgecolor='black')
    ax.add_patch(poly)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.savefig(p_png, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    return p_png


def classification_barreled(exitspeed: float, angle: float) -> int:
    if (exitspeed >= 116) and (8 < angle < 50):
        return 1
    elif 99 < exitspeed < 116:
        dif_class = exitspeed - 99
        angle_min = 25 - dif_class
        angle_max = 31 + dif_class
        return 1 if angle_min < angle < angle_max else 0
    elif (exitspeed == 99) and (25 < angle < 31):
        return 1
    elif (exitspeed == 98) and (26 < angle < 30):
        return 1
    else:
        return 0


def create_stats_table(df_game: pd.DataFrame) -> pd.DataFrame:
    df_pa = df_game[df_game.PitchofPA == 1].groupby('Batter').size().rename('PA')
    df_dhr = df_game[df_game.PlayResult == 'HomeRun'].groupby('Batter').size().rename('HR')
    df_game = df_game.copy()
    df_game['is_barreled'] = df_game.apply(
        lambda x: classification_barreled(x['ExitSpeed'], x['Angle']), axis=1
    )
    df_barrels = df_game.groupby('Batter').is_barreled.sum().rename('Barrels')
    df_team = (df_game.sort_values(['Batter', 'fecha_carga'], ascending=[True, False])
                      .drop_duplicates('Batter')
                      .groupby('Batter').BatterTeam.first())
    dfs = [df_pa, df_dhr, df_barrels, df_team]
    df_all = reduce(lambda l, r: pd.concat([l, r], axis=1), dfs)
    df_all['Barr%'] = (df_all['Barrels'] / df_all['PA']).map("{:.1%}".format)
    df_all.HR = df_all.HR.fillna(0).astype(int)
    df_all.PA = df_all.PA.fillna(0).astype(int)
    df_all = df_all[['PA', 'HR', 'Barrels', 'Barr%', 'BatterTeam']].fillna('')
    df_all.index.name = 'Nombre'
    return df_all


def get_stats_of_player(name_batter: str, df_stats: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    try:
        df = pd.DataFrame(df_stats.loc[name_batter]).T
        team = df_stats.loc[name_batter]['BatterTeam']
        return df, team
    except KeyError:
        print(f"[ERROR] Bateador '{name_batter}' no encontrado en df_stats.")
        try: logger.error(f"Bateador '{name_batter}' no encontrado en df_stats.")
        except Exception: pass
        return pd.DataFrame(), 'SinEquipo'


def create_style_batter(df_temp: pd.DataFrame):
    styles = [
        dict(selector="th", props=[("font-size", "200%"), ("text-align", "center"),
                                     ('border-top', '2px solid black'), ('border-bottom', '2px solid black'),
                                     ('border-left', '2px solid black'), ('border-right', '2px solid black')]),
        dict(selector="td", props=[("font-size", "200%"), ("text-align", "center"),
                                     ('border-left', '1px solid black'), ('border-right', '1px solid black'),
                                     ('border-bottom', '1px solid black')]),
        dict(selector="caption", props=[("caption-side", "bottom")])
    ]
    return df_temp.style.set_table_styles(styles).hide(axis='index')


def from_df_to_tablepng(batter_name: str, team: str, dir_temp: str, html_temp, name: str):
    dir_ = os.path.join(dir_temp, team, batter_name)
    os.makedirs(dir_, exist_ok=True)
    output_path = os.path.join(dir_, f"{name}.png")
    try:
        dfi.export(html_temp, output_path, table_conversion="matplotlib")
    except Exception as e:
        print(f"[ERROR] Error al exportar tabla '{name}' a PNG: {e}")
        try: logger.error(f"Error al exportar tabla '{name}' a PNG: {e}")
        except Exception: pass


def save_fig(dir_temp: str, team: str, batter_name: str, chart, chart_name: str, dpi: int = 210) -> str:
    """Guarda PNG y un JPG (para FPDF). Devuelve la ruta PNG."""
    dir_ = os.path.join(dir_temp, team, batter_name)
    os.makedirs(dir_, exist_ok=True)
    if chart_name == 'slugging_general_left':
        dpi = 150

    base = os.path.join(
        dir_,
        chart_name if not chart_name.lower().endswith(('.png', '.jpg', '.jpeg'))
        else os.path.splitext(chart_name)[0]
    )
    png_path = base + '.png'
    jpg_path = base + '.jpg'

    try:
        chart.savefig(png_path, dpi=dpi, bbox_inches='tight', pad_inches=0.2, transparent=False)
        chart.savefig(jpg_path, dpi=dpi, bbox_inches='tight', pad_inches=0.2,
                      facecolor='white', transparent=False, format='jpg')
        plt.close(chart)
    except Exception as e:
        print(f"[ERROR] Error al guardar gráfico '{chart_name}': {e}")
        try: logger.error(f"Error al guardar gráfico '{chart_name}': {e}")
        except Exception: pass
        png_path = None
    return png_path


def in_strike_zone(row) -> bool:
    h = row['PlateLocHeight']
    s = row['PlateLocSide']
    return (_y_low <= h <= _y_high) and (_x_low <= s <= _x_high)


def hilow_strike_zone(height: float) -> bool:
    return height > ((_y_low + _y_high) / 2)

def left_strike_zone(side: float) -> bool:
    return side < 0

def format_hit(num: float) -> str:
    return f"{num:.3f}"

def create_heatmap_hit(df_games: pd.DataFrame, name_batter: str, side: str):
    """Heatmap de hits por tipo de lanzamiento vs brazo (side). Maneja histórico bajo y tipos faltantes."""
    sns.set(font_scale=1.2)

    # 1) Subset por bateador
    try:
        df_temp = df_games[df_games.Batter == name_batter].copy()
    except Exception as e:
        print(f"[ERROR] Filtrando por bateador en create_heatmap_hit: {e}")
        try: logger.error(f"Filtrando por bateador en create_heatmap_hit: {e}")
        except Exception: pass
        fig = plt.figure(); plt.axis('off'); return fig

    # 2) Cobertura histórica (por juegos o, si no hay id_path, por PAs)
    MIN_GAMES = 3
    MIN_PA = 5
    try:
        num_partidos = df_temp['id_path'].nunique() if 'id_path' in df_temp.columns else None
    except Exception:
        num_partidos = None
    pa_count = int((df_temp['PitchofPA'] == 1).sum()) if 'PitchofPA' in df_temp.columns else None

    if (num_partidos is not None and num_partidos < MIN_GAMES) or \
       (num_partidos is None and (pa_count is None or pa_count < MIN_PA)):
        msg = "histórico insuficiente (partidos<3 o PA<5)"
        _notify_skip(f"kde_hit_{side.lower()}", name_batter, side, msg)
        fig = plt.figure(); plt.axis('off'); return fig

    # 3) Filtros base y columnas necesarias
    try:
        df_temp = df_temp[
            (df_temp.PitchCall == "InPlay") &
            (df_temp.PlayResult != "Undefined")
        ].dropna(subset=["PlateLocHeight", "PlateLocSide"])
    except Exception as e:
        print(f"[ERROR] Filtrando jugadas/NA en create_heatmap_hit: {e}")
        try: logger.error(f"Filtrando jugadas/NA en create_heatmap_hit: {e}")
        except Exception: pass
        fig = plt.figure(); plt.axis('off'); return fig

    # 4) Asegura columna de tipo (auto_pitch_type_2) con fallback
    try:
        if "auto_pitch_type_2" not in df_temp.columns:
            if "AutoPitchType" in df_temp.columns:
                df_temp["auto_pitch_type_2"] = df_temp["AutoPitchType"]
            else:
                df_temp["auto_pitch_type_2"] = "ALL"
        df_temp["auto_pitch_type_2"] = df_temp["auto_pitch_type_2"].fillna("ALL").astype(str)
    except Exception as e:
        print(f"[ERROR] Preparando auto_pitch_type_2: {e}")
        try: logger.error(f"Preparando auto_pitch_type_2 en create_heatmap_hit: {e}")
        except Exception: pass
        fig = plt.figure(); plt.axis('off'); return fig

    # 5) Tipos disponibles (si no hay, forzar "ALL")
    unique_launch = df_temp["auto_pitch_type_2"].dropna().unique()
    if len(unique_launch) == 0:
        df_temp["auto_pitch_type_2"] = "ALL"
        unique_launch = np.array(["ALL"])

    # 6) Plot
    try:
        plotted_any = False
        fig, _ = plt.subplots(figsize=(23, 5))
        for idx, launch in enumerate(unique_launch):
            try:
                df_plot = df_temp[(df_temp["auto_pitch_type_2"] == launch) & (df_temp.PitcherThrows == side)].copy()

                # Ordena por Date si existe (coercible), y limita a 200
                if "Date" in df_plot.columns:
                    df_plot["Date"] = pd.to_datetime(df_plot["Date"], errors="coerce")
                    df_plot = df_plot.sort_values("Date", ascending=False).head(200)
                else:
                    df_plot = df_plot.head(200)

                ax = plt.subplot(1, len(unique_launch), idx + 1)
                plt.title(f"Hit Heatmap \n{str(launch)} {side}", fontsize=23)

                if df_plot.empty:
                    plt.axis('off')
                    continue

                plotted_any = True
                sns.kdeplot(
                    data=df_plot,
                    x="PlateLocSide",
                    y="PlateLocHeight",
                    cmap="coolwarm",
                    levels=15,
                    bw_adjust=0.5,
                    cbar=False,
                    thresh=0.3,
                    fill=True,
                    alpha=0.6,
                )

                # Marco de la zona de strike
                x = np.linspace(-_x_radio, _x_radio, 10)
                y = np.linspace(_y_low, _y_high, 10)
                plt.plot(np.repeat(-_x_radio, len(y)), y, c='black')
                plt.plot(np.repeat(_x_radio, len(y)), y, c='black')
                plt.plot(x, np.repeat(_y_low, len(x)), c='black')
                plt.plot(x, np.repeat(_y_high, len(x)), c='black')
                plt.xlim(-2, 2)
                plt.ylim(_y_low - 0.7, _y_high + 0.7)
                plt.axis('off')
            except Exception as e:
                print(f"[ERROR] Procesando bucket '{launch}' en heatmap: {e}")
                try: logger.error(f"Procesando bucket '{launch}' en create_heatmap_hit: {e}")
                except Exception: pass

        if not plotted_any:
            _notify_skip(f"kde_hit_{side.lower()}", name_batter, side, "sin datos por tipo para ese brazo")
        return fig

    except Exception as e:
        print(f"[ERROR] Creando figura de heatmap: {e}")
        try: logger.error(f"Creando figura de heatmap en create_heatmap_hit: {e}")
        except Exception: pass
        fig = plt.figure(); plt.axis('off'); return fig


def avg_hit_chart(name_batter: str, side: str, df_games: pd.DataFrame):
    sns.set(font_scale=1.2)

    df_games = df_games.copy()
    if "auto_pitch_type_2" not in df_games.columns:
        df_games["auto_pitch_type_2"] = None
        print("[WARN] Columna 'auto_pitch_type_2' no encontrada. Se inicializa a None.")
        try: logger.warning("Columna 'auto_pitch_type_2' no encontrada. Se inicializa a None.")
        except Exception: pass

    # Normaliza AutoPitchType y marca FB/Sink
    try:
        type_norm = df_games.get("AutoPitchType", "").astype(str).str.strip().str.lower()
        fb_sink_set = {
            "four-seam","four seam","ff","fourseam",
            "sinker","two-seam","two seam","ft","twoseam","sink"
        }
        df_games.loc[type_norm.isin(fb_sink_set), "auto_pitch_type_2"] = "Rectas y sinkers"
    except Exception as e:
        print(f"[ERROR] Normalizando AutoPitchType: {e}")
        try: logger.error(f"Normalizando AutoPitchType en avg_hit_chart: {e}")
        except Exception: pass

    # Columnas requeridas
    req = {"Batter","PlayResult","PitcherThrows","auto_pitch_type_2","PlateLocHeight","PlateLocSide"}
    if not req.issubset(df_games.columns):
        missing = req - set(df_games.columns)
        print(f"[ERROR] Faltan columnas requeridas para avg_hit_chart: {missing}")
        try: logger.error(f"Faltan columnas requeridas para avg_hit_chart: {missing}")
        except Exception: pass
        fig = plt.figure(); plt.axis('off'); return fig
    if "KorBB" not in df_games.columns:
        df_games["KorBB"] = ""

    # --- filtro principal (FB/Sink) ---
    df_temp = df_games[
        (df_games.Batter == name_batter) &
        (df_games.PlayResult != "Undefined") &
        (df_games.PitcherThrows == side) &
        (df_games.auto_pitch_type_2 == "Rectas y sinkers")
    ].copy()
    
    # Fallback si no hay FB/Sink para este jugador/lado
    used_all = False
    if df_temp.empty:
        df_temp = df_games[
            (df_games.Batter == name_batter) &
            (df_games.PlayResult != "Undefined") &
            (df_games.PitcherThrows == side)
        ].copy()
        used_all = True
        print("[WARN] Sin FB/Sink para este jugador/lado; usando TODOS los lanzamientos para xAVG.")
        try: logger.warning("Sin FB/Sink para este jugador/lado; usando TODOS los lanzamientos para xAVG.")
        except Exception: pass
    
    print(f"[DEBUG] Registros filtrados por jugador/lado/tipo: {len(df_temp)}")

    ab_playresults = ["Single","Double","Triple","HomeRun","Out","Error","FieldersChoice"]
    df_temp["is_atbat"] = df_temp["PlayResult"].isin(ab_playresults) | (df_temp["KorBB"] == "Strikeout")
    hit_playresults = ["Single","Double","Triple","HomeRun"]
    df_temp["is_hit"] = df_temp["PlayResult"].isin(hit_playresults)

    # Zonas (tolerante a NaN)
    df_temp = df_temp.dropna(subset=["PlateLocHeight","PlateLocSide"]).copy()
    df_temp["in_strike_zone"] = df_temp[["PlateLocHeight","PlateLocSide"]].apply(in_strike_zone, axis=1)
    df_temp["in_left_strike_zone"] = df_temp["PlateLocSide"].apply(left_strike_zone)
    df_temp["in_high_strike_zone"] = df_temp["PlateLocHeight"].apply(hilow_strike_zone)

    df_temp = df_temp[df_temp["in_strike_zone"]]
    print(f"[DEBUG] Registros dentro de la zona de strike: {len(df_temp)}")
    if df_temp.empty:
        print("[WARN] DataFrame vacío tras aplicar zona de strike")
        try: logger.warning("DataFrame vacío tras aplicar zona de strike en avg_hit_chart")
        except Exception: pass
        fig = plt.figure(figsize=(4,4))
        ttl = f"xAVG vs {side} " + ("ALL Pitches" if used_all else "FB/Sink")
        plt.title(ttl, fontsize=32)
        plt.text(0.5, 0.5, "SIN DATOS", ha="center", va="center",
                 fontsize=36, color="red", fontweight="bold", transform=plt.gca().transAxes)
        plt.axis('off')
        return fig

    # 1B=lado izquierdo del plato; 3B=lado derecho
    df_1b = df_temp[df_temp.in_left_strike_zone]
    in_hits = int(df_1b["is_hit"].sum()); in_adv = int(df_1b["is_atbat"].sum())
    avg_in = format_hit(round(in_hits / in_adv, 3) if in_adv else 0)

    df_3b = df_temp[~df_temp.in_left_strike_zone]
    out_hits = int(df_3b["is_hit"].sum()); out_adv = int(df_3b["is_atbat"].sum())
    avg_out = format_hit(round(out_hits / out_adv, 3) if out_adv else 0)

    hi = df_temp[df_temp.in_high_strike_zone]
    lo = df_temp[~df_temp.in_high_strike_zone]
    avg_hi = format_hit(round(hi["is_hit"].sum() / hi["is_atbat"].sum(), 3) if hi["is_atbat"].sum() else 0)
    avg_lo = format_hit(round(lo["is_hit"].sum() / lo["is_atbat"].sum(), 3) if lo["is_atbat"].sum() else 0)

    print(f"[DEBUG] xAVG calculado -> 3B:{avg_in}, 1B:{avg_out}, HI:{avg_hi}, LO:{avg_lo}")

    fig = plt.figure(figsize=(4,4))
    ttl = f"xAVG vs {side} " + ("ALL Pitches" if used_all else "FB/Sink")
    plt.title(ttl, fontsize=40)
    color = "r" if side == "Left" else "black"
    plt.text(-0.5, 0,  f"3B:{avg_in}",  fontsize=30, color=color)
    plt.text( 0.5, 0,  f"1B:{avg_out}", fontsize=30, color=color)
    plt.text( 0.0, 0.3, f"HI:{avg_hi}",  fontsize=30, color=color)
    plt.text( 0.0,-0.3, f"LO:{avg_lo}",  fontsize=30, color=color)
    plt.axis('off')

    return fig
def create_slogging_chart_all(name_batter: str, side: str, df_games: pd.DataFrame):
    sns.set(font_scale=1.5)

    df_temp = (
        df_games[
            (df_games.Batter == name_batter) &
            (df_games.PitchCall == 'InPlay') &
            (df_games.PlayResult != 'Undefined')
        ]
        .dropna(subset=['PlateLocHeight', 'PlateLocSide'])
        .copy()
    )

    if df_temp.empty:
        _notify_skip(f"slugging_general_{side.lower()}", name_batter, side, "sin registros InPlay/definidos")
        fig = plt.figure()
        plt.axis('off')
        return fig

    df_temp['x_estoy'] = pd.cut(df_temp.PlateLocSide, bins=_xbin)
    df_temp['y_estoy'] = pd.cut(df_temp.PlateLocHeight, bins=_ybin)

    df_side = df_temp[df_temp.PitcherThrows == side]
    if df_side.empty:
        _notify_skip(f"slugging_general_{side.lower()}", name_batter, side, "sin registros para ese brazo")
        fig = plt.figure()
        plt.axis('off')
        return fig

    weights = {'Single': 1, 'Double': 2, 'Triple': 3, 'HomeRun': 4,
               'Error': 0, 'FieldersChoice': 0, 'Sacrifice': 0, 'Out': 0}

    df = df_side.groupby(['y_estoy', 'x_estoy', 'PlayResult']).size().unstack()
    for c in df.columns:
        if c in weights:
            df[c] = df[c] * weights[c]

    denom = len(df_side) or 1
    df['sum_all'] = (df.sum(axis=1) / denom) * 8

    fig = plt.figure(figsize=(6, 7))
    sns.heatmap(
        df['sum_all'].unstack().sort_index(ascending=False),
        cmap='coolwarm',
        annot=True,
        fmt='0.3f',
        vmin=0,
        vmax=0.5,
        cbar=(side != 'Left'),
        annot_kws=dict(fontsize=20)
    )
    plt.plot(np.repeat(1, len(_y_lin)), _y_lin, c='black', linewidth=4)
    plt.plot(np.repeat(4, len(_y_lin)), _y_lin, c='black', linewidth=4)
    plt.plot(_x_lin, np.repeat(1, len(_x_lin)), c='black', linewidth=4)
    plt.plot(_x_lin, np.repeat(4, len(_x_lin)), c='black', linewidth=4)
    plt.title('Slugging General ' + side, fontsize=25)
    plt.axis('off')
    plt.tight_layout()
    return fig


# -------------------------------------------
# Slugging por tipo
# -------------------------------------------
def create_slogging_chart_by_type(name_batter: str, side: str, df_games: pd.DataFrame):
    sns.set(font_scale=1.2)

    # 1) Filtro base (sin exigir AutoPitchType aún)
    try:
        df_temp = (
            df_games[
                (df_games.Batter == name_batter) &
                (df_games.PitchCall == 'InPlay') &
                (df_games.PlayResult != 'Undefined')
            ]
            .dropna(subset=['PlateLocHeight', 'PlateLocSide'])
            .copy()
        )
    except Exception as e:
        print(f"[ERROR] Filtrando df_games en create_slogging_chart_by_type: {e}")
        try: logger.error(f"Filtrando df_games en create_slogging_chart_by_type: {e}")
        except Exception: pass
        return plt.figure(), 0

    # 2) Asegura/normaliza tipos de pitcheo
    try:
        df_temp = ensure_pitch_types(df_temp, "auto_pitch_type_2")
    except Exception as e:
        print(f"[ERROR] Creando/normalizando auto_pitch_type_2: {e}")
        try: logger.error(f"Creando/normalizando auto_pitch_type_2: {e}")
        except Exception: pass
        return plt.figure(), 0

    if df_temp.empty:
        _notify_skip(f"slugging_by_launch_{side.lower()}", name_batter, side, "sin registros InPlay/definidos")
        fig = plt.figure(); plt.axis('off'); return fig, 0

    # 3) Bins de zona
    try:
        df_temp['x_estoy'] = pd.cut(df_temp.PlateLocSide, bins=_xbin)
        df_temp['y_estoy'] = pd.cut(df_temp.PlateLocHeight, bins=_ybin)
    except Exception as e:
        print(f"[ERROR] Creando bins de strike zone: {e}")
        try: logger.error(f"Creando bins de strike zone: {e}")
        except Exception: pass
        return plt.figure(), 0

    # 4) Filtra por lado y obtiene tipos
    try:
        df_side_all = df_temp[df_temp.PitcherThrows == side].copy()
        unique_launch = df_side_all['auto_pitch_type_2'].dropna().unique()
    except Exception as e:
        print(f"[ERROR] Preparando conjuntos por lado/tipo: {e}")
        try: logger.error(f"Preparando conjuntos por lado/tipo: {e}")
        except Exception: pass
        return plt.figure(), 0

    # Fallback: si no hay tipos para ese brazo, usa un bucket único "ALL"
    if len(unique_launch) == 0:
        _notify_skip(f"slugging_by_launch_{side.lower()}", name_batter, side, "sin tipos para ese brazo")
        fig = plt.figure(); plt.axis('off'); return fig, 0

    num_type_launch = len(unique_launch)
    dict_cond = {'Single': 1, 'Double': 2, 'Triple': 3, 'HomeRun': 4,
                 'Error': 0, 'FieldersChoice': 0, 'Sacrifice': 0, 'Out': 0}

    fig = plt.figure(figsize=(25, 5))
    plotted_any = False

    for idx, launch in enumerate(unique_launch):
        try:
            df_side = df_side_all[(df_side_all['auto_pitch_type_2'] == launch)]
            if df_side.empty:
                print(f"[WARN] DataFrame vacío para el lanzamiento '{launch}'. Saltando.")
                try: logger.warning(f"DataFrame vacío para el lanzamiento '{launch}' en slugging por tipo.")
                except Exception: pass
                continue

            plotted_any = True
            df_temp2 = df_side.groupby(['y_estoy', 'x_estoy', 'PlayResult']).size().unstack()
            for col in df_temp2.columns:
                if col in dict_cond:
                    df_temp2[col] = df_temp2[col] * dict_cond[col]
            denom = len(df_side) if len(df_side) else 1
            df_temp2['sum_all'] = (df_temp2.sum(axis=1) / denom) * 8

            ax = plt.subplot(1, num_type_launch, idx + 1)
            plt.title(f"{str(launch)} {side}", fontsize=25)
            cbar = (idx == num_type_launch - 1)
            sns.heatmap(
                df_temp2['sum_all'].unstack().sort_index(ascending=False),
                cmap='coolwarm', annot=True, fmt='0.3f',
                vmin=0, vmax=0.5, ax=ax, cbar=cbar, annot_kws=dict(fontsize=20)
            )
            plt.plot(np.repeat(1, len(_y_lin)), _y_lin, c='black', linewidth=4)
            plt.plot(np.repeat(4, len(_y_lin)), _y_lin, c='black', linewidth=4)
            plt.plot(_x_lin, np.repeat(1, len(_x_lin)), c='black', linewidth=4)
            plt.plot(_x_lin, np.repeat(4, len(_x_lin)), c='black', linewidth=4)
            plt.axis('off')
        except Exception as e:
            print(f"[ERROR] Procesando lanzamiento '{launch}': {e}")
            try: logger.error(f"Procesando lanzamiento '{launch}' en slugging por tipo: {e}")
            except Exception: pass

    if not plotted_any:
        _notify_skip(f"slugging_by_launch_{side.lower()}", name_batter, side, "sin datos por tipo para ese brazo")

    plt.tight_layout()
    return fig, num_type_launch


# -------------------------------------------
# Reporte PDF
# -------------------------------------------

def get_positions(n: int, chart: bool = True):
    last_val = 80 if chart else 95
    return {4: [5, 60, 110, 155], 3: [10, 70, 120], 2: [20, 80], 1: [last_val]}.get(n, [])


def create_report(batter_name: str, team: str, dir_images: str, dict_short: dict, n_left: int, n_right: int):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font('Times', 'B', 22)
    pdf.cell(0, 8, f'Batter: {batter_name}', border=0, ln=2, align='C')
    hp_path = ensure_home_plate_asset()
    hp_ok = os.path.exists(hp_path)

    def pick_image(stem: str) -> str:
        p_jpg = os.path.join(dir_images, f"{stem}.jpg")
        p_png = os.path.join(dir_images, f"{stem}.png")
        if os.path.exists(p_jpg):
            return p_jpg
        if os.path.exists(p_png):
            return p_png
        # Solo cuando falla:
        print(f"[ERROR] Imagen no encontrada: {p_jpg} ni {p_png}")
        try:
            logger.error(f"Imagen no encontrada: {p_jpg} ni {p_png}")
        except Exception:
            pass
        return ""

    # Página 1
    try: pdf.image(pick_image('table_1'), x=40, y=20, w=120, h=20)
    except Exception as e: print(f"[ERROR] table_1 en PDF: {e}"); logger.error(f"table_1 en PDF: {e}")
    try: pdf.image(pick_image('slugging_general_left'), x=1, y=50, w=92, h=60)
    except Exception as e: print(f"[ERROR] slugging_general_left en PDF: {e}"); logger.error(f"slugging_general_left en PDF: {e}")
    try:
        if hp_ok: pdf.image(hp_path, x=25, y=110, w=40, h=15)
    except Exception as e: print(f"[ERROR] home_plate izq en PDF: {e}"); logger.error(f"home_plate izq en PDF: {e}")
    try: pdf.image(pick_image('slugging_general_right'), x=98, y=50, w=92, h=60)
    except Exception as e: print(f"[ERROR] slugging_general_right en PDF: {e}"); logger.error(f"slugging_general_right en PDF: {e}")
    try:
        if hp_ok: pdf.image(hp_path, x=115, y=110, w=40, h=15)
    except Exception as e: print(f"[ERROR] home_plate der en PDF: {e}"); logger.error(f"home_plate der en PDF: {e}")

    try: pdf.image(pick_image('slugging_by_launch_left'), x=1, y=130, w=202, h=60)
    except Exception as e: print(f"[ERROR] slugging_by_launch_left en PDF: {e}"); logger.error(f"slugging_by_launch_left en PDF: {e}")
    for pos_x in get_positions(n_left):
        try:
            if hp_ok: pdf.image(hp_path, x=pos_x, y=187, w=40, h=12)
        except Exception as e: print(f"[ERROR] home_plate fila left en PDF: {e}"); logger.error(f"home_plate fila left en PDF: {e}")

    try: pdf.image(pick_image('slugging_by_launch_right'), x=1, y=210, w=202, h=60)
    except Exception as e: print(f"[ERROR] slugging_by_launch_right en PDF: {e}"); logger.error(f"slugging_by_launch_right en PDF: {e}")
    for pos_x in get_positions(n_right):
        try:
            if hp_ok: pdf.image(hp_path, x=pos_x, y=267, w=40, h=12)
        except Exception as e: print(f"[ERROR] home_plate fila right en PDF: {e}"); logger.error(f"home_plate fila right en PDF: {e}")

    # Página 2
    pdf.add_page()
    try: pdf.image(pick_image('table_hit_left'), x=20, y=5, w=60, h=60)
    except Exception as e: print(f"[ERROR] table_hit_left en PDF: {e}"); logger.error(f"table_hit_left en PDF: {e}")
    try: pdf.image(pick_image('table_hit_right'), x=120, y=5, w=60, h=60)
    except Exception as e: print(f"[ERROR] table_hit_right en PDF: {e}"); logger.error(f"table_hit_right en PDF: {e}")
    try: pdf.image(pick_image('kde_hit_left'), x=1, y=70, w=202, h=60)
    except Exception as e: print(f"[ERROR] kde_hit_left en PDF: {e}"); logger.error(f"kde_hit_left en PDF: {e}")
    for pos_x in get_positions(n_left, False):
        try:
            if hp_ok: pdf.image(hp_path, x=pos_x, y=130, w=40, h=12)
        except Exception as e: print(f"[ERROR] home_plate fila left (p2) en PDF: {e}"); logger.error(f"home_plate fila left (p2) en PDF: {e}")
    for pos_x in get_positions(n_right, False):
        try:
            if hp_ok: pdf.image(hp_path, x=pos_x, y=220, w=40, h=12)
        except Exception as e: print(f"[ERROR] home_plate fila right (p2) en PDF: {e}"); logger.error(f"home_plate fila right (p2) en PDF: {e}")

    # Página 3
    pdf.add_page(orientation='L')
    try: pdf.image(pick_image('spray_chart_general_left'), x=5, y=20, w=100, h=70)
    except Exception as e: print(f"[ERROR] spray_chart_general_left en PDF: {e}"); logger.error(f"spray_chart_general_left en PDF: {e}")
    try: pdf.image(pick_image('spray_chart_general_right'), x=140, y=20, w=100, h=70)
    except Exception as e: print(f"[ERROR] spray_chart_general_right en PDF: {e}"); logger.error(f"spray_chart_general_right en PDF: {e}")
    try: pdf.image(pick_image('spray_chart_general_left_strikes_2'), x=5, y=100, w=100, h=70)
    except Exception as e: print(f"[ERROR] spray_chart_general_left_strikes_2 en PDF: {e}"); logger.error(f"spray_chart_general_left_strikes_2 en PDF: {e}")
    try: pdf.image(pick_image('spray_chart_general_right_strikes_2'), x=140, y=100, w=100, h=70)
    except Exception as e: print(f"[ERROR] spray_chart_general_right_strikes_2 en PDF: {e}"); logger.error(f"spray_chart_general_right_strikes_2 en PDF: {e}")

    out_path = os.path.join(os.path.dirname(dir_images), f"{batter_name}.pdf")
    try:
        pdf.output(out_path, dest='F')
    except Exception as e:
        print(f"[ERROR] guardando PDF: {e}")
        try: logger.error(f"Error guardando PDF: {e}")
        except Exception: pass
        return None
    return out_path


def create_report_full(
    batter_name: str,
    df_stats: pd.DataFrame,
    df_games: pd.DataFrame,
    dict_short: dict,
    work_dir: str = None
):
    # Normalización mínima y silenciosa (solo errores)
    try:
        df_games = df_games.copy()
        if "auto_pitch_type_2" not in df_games.columns:
            df_games["auto_pitch_type_2"] = None
        type_norm = df_games.get("AutoPitchType", pd.Series([], dtype=str)).astype(str).str.strip().str.lower()
        fb_sink = {
            "four-seam","four seam","ff","fourseam","four-seam fastball","fastball","fb",
            "sinker","sink","si","two-seam","two seam","ft","twoseam","2-seam","2 seam"
        }
        df_games.loc[type_norm.isin(fb_sink), "auto_pitch_type_2"] = "Rectas y sinkers"
    except Exception as e:
        print(f"[ERROR] normalizando df_games: {e}")
        try: logger.error(f"Error normalizando df_games: {e}")
        except Exception: pass

    base_dir = work_dir if work_dir else DIR_TEMP

    # Equipo y carpeta
    try:
        table, team = get_stats_of_player(batter_name, df_stats)
        table['BatterTeam'] = table['BatterTeam'].map(lambda t: dict_short.get(t, t))
        team = table['BatterTeam'].iloc[0] if 'BatterTeam' in table.columns and not table.empty else team
        if pd.isna(team) or team is None or str(team) == 'nan':
            team = 'SinEquipo'
        team = str(team)
    except Exception as e:
        print(f"[ERROR] obteniendo equipo/tabla del bateador: {e}")
        try: logger.error(f"Error obteniendo equipo/tabla del bateador: {e}")
        except Exception: pass
        team = 'SinEquipo'
        table = pd.DataFrame()

    dir_images = os.path.join(base_dir, team, batter_name)
    try:
        os.makedirs(dir_images, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] creando carpeta de imágenes: {e}")
        try: logger.error(f"Error creando carpeta de imágenes: {e}")
        except Exception: pass

    # Tabla de perfil
    try:
        html_temp = create_style_batter(table)
        from_df_to_tablepng(batter_name, team, base_dir, html_temp, 'table_1')
    except Exception as e:
        print(f"[ERROR] generando/guardando table_1: {e}")
        try: logger.error(f"Error generando/guardando table_1: {e}")
        except Exception: pass

    # Gráficas slugging (general)
    try:
        fig1 = create_slogging_chart_all(batter_name, 'Left', df_games)
        p1 = save_fig(base_dir, team, batter_name, fig1, 'slugging_general_left')
    except Exception as e:
        print(f"[ERROR] slugging_general_left: {e}")
        logger.error(f"Error al generar/guardar slugging_general_left: {e}")
    
    try:
        fig2 = create_slogging_chart_all(batter_name, 'Right', df_games)
        p2 = save_fig(base_dir, team, batter_name, fig2, 'slugging_general_right')
    except Exception as e:
        print(f"[ERROR] slugging_general_right: {e}")
        logger.error(f"Error al generar/guardar slugging_general_right: {e}")
    
    
    # Gráficas slugging por tipo
    
    n_left, n_right = 0, 0
    try:
        fig3, n_left = create_slogging_chart_by_type(batter_name, 'Left', df_games)
        p3 = save_fig(base_dir, team, batter_name, fig3, 'slugging_by_launch_left')
    except Exception as e:
        print(f"[ERROR] slugging_by_launch_left: {e}")
        logger.error(f"Error al generar/guardar slugging_by_launch_left: {e}")

    try:
        fig4, n_right = create_slogging_chart_by_type(batter_name, 'Right', df_games)
        p4 = save_fig(base_dir, team, batter_name, fig4, 'slugging_by_launch_right')
    except Exception as e:
        print(f"[ERROR] slugging_by_launch_right: {e}")
        logger.error(f"Error al generar/guardar slugging_by_launch_right: {e}")


    # Tablas xAVG
    try:
        fig5 = avg_hit_chart(batter_name, 'Left', df_games)
        p5 = save_fig(base_dir, team, batter_name, fig5, 'table_hit_left')
    except Exception as e:
        print(f"[ERROR] table_hit_left: {e}")
        logger.error(f"Error al generar/guardar table_hit_left: {e}")

    try:
        fig6 = avg_hit_chart(batter_name, 'Right', df_games)
        p6 = save_fig(base_dir, team, batter_name, fig6, 'table_hit_right')
    except Exception as e:
        print(f"[ERROR] table_hit_right: {e}")
        logger.error(f"Error al generar/guardar table_hit_right: {e}")

    # Heatmaps
    try:
        fig7 = create_heatmap_hit(df_games, batter_name, 'Left')
        p7 = save_fig(base_dir, team, batter_name, fig7, 'kde_hit_left')
    except Exception as e:
        print(f"[ERROR] kde_hit_left: {e}")
        logger.error(f"Error al generar/guardar kde_hit_left: {e}")

    try:
        fig8 = create_heatmap_hit(df_games, batter_name, 'Right')
        p8 = save_fig(base_dir, team, batter_name, fig8, 'kde_hit_right')
    except Exception as e:
        print(f"[ERROR] kde_hit_right: {e}")
        logger.error(f"Error al generar/guardar kde_hit_right: {e}")

    # Spray charts (esta función guarda internamente)
    try:
        spray_probability_conditional(df_games, batter_name, team, side='Left', title="Addi zone probs", display_title=True)
        p_spl = os.path.join(dir_images, 'spray_chart_general_left.png')
    except Exception as e:
        print(f"[ERROR] spray_chart_general_left: {e}")
        logger.error(f"Error al generar spray_chart_general_left: {e}")

    try:
        spray_probability_conditional(df_games, batter_name, team, side='Right', title="Addi zone probs", display_title=True)
        p_spr = os.path.join(dir_images, 'spray_chart_general_right.png')
    except Exception as e:
        print(f"[ERROR] spray_chart_general_right: {e}")
        logger.error(f"Error al generar spray_chart_general_right: {e}")

    try:
        spray_probability_conditional(df_games, batter_name, team, side='Left', strikes=2, title="Strikes = 2", display_title=True)
        p_spl2 = os.path.join(dir_images, 'spray_chart_general_left_strikes_2.png')
    except Exception as e:
        print(f"[ERROR] spray_chart_general_left_strikes_2: {e}")
        logger.error(f"Error al generar spray_chart_general_left_strikes_2: {e}")

    try:
        spray_probability_conditional(df_games, batter_name, team, side='Right', strikes=2, title="Strikes = 2", display_title=True)
        p_spr2 = os.path.join(dir_images, 'spray_chart_general_right_strikes_2.png')
    except Exception as e:
        print(f"[ERROR] spray_chart_general_right_strikes_2: {e}")
        logger.error(f"Error al generar spray_chart_general_right_strikes_2: {e}")

    # Crear PDF
    try:
        out_pdf = create_report(batter_name, team, dir_images, dict_short, n_left, n_right)
        return out_pdf
    except Exception as e:
        print(f"[ERROR] PDF report: {e}")
        logger.error(f"Error al crear reporte PDF: {e}")
        return None
 
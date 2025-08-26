import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import fpdf
from functools import reduce
import dataframe_image as dfi

# === STUBS (gráficas vacías para no romper el flujo) ===
def create_slogging_chart_all(*args, **kwargs):
    fig = plt.figure()
    plt.axis('off')
    return fig

def create_slogging_chart_by_type(*args, **kwargs):
    fig = plt.figure()
    plt.axis('off')
    return fig, 0

def avg_hit_chart(*args, **kwargs):
    fig = plt.figure()
    plt.axis('off')
    return fig

def create_heatmap_hit(*args, **kwargs):
    fig = plt.figure()
    plt.axis('off')
    return fig

def spray_probability_conditional(*args, **kwargs):
    return None

# === Reporte PDF simple desde PNG existentes ===
def create_report(batter_name, team, dir_images, dict_short, n_left, n_right, dir_homeplate=None):
    from fpdf import FPDF
    out_dir = os.path.dirname(dir_images)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{batter_name}.pdf")

    if not os.path.isdir(dir_images):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 12, f"Reporte de {batter_name}", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.ln(6)
        pdf.multi_cell(0, 6, f"Equipo: {team}")
        pdf.output(out_path)
        return out_path

    imgs = sorted([f for f in os.listdir(dir_images) if f.lower().endswith(".png")])

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)

    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 12, f"Reporte de {batter_name}", ln=True, align='C')
    pdf.ln(4)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 6, f"Equipo: {team}")
    pdf.ln(4)

    for fname in imgs:
        img_path = os.path.join(dir_images, fname)
        try:
            pdf.add_page()
            pdf.image(img_path, x=10, y=10, w=190)
        except Exception:
            continue

    pdf.output(out_path)
    return out_path

# ----------------------------------------------------------------------
# BIGQUERY
# ----------------------------------------------------------------------
from google.cloud import bigquery
import google.auth
from google.cloud import bigquery_storage

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "baseballlmb-key.json"
credentials, your_project_id = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=credentials)
client = bigquery.Client()

def _external_load_batter_games():
    # Ajusta el nombre de tabla si tu dataset difiere
    query = '''
        SELECT
            Batter,
            BatterTeam,
            PitchofPA,
            PlayResult,
            ExitSpeed,
            Angle,
            fecha_carga,
            Date
        FROM baseballlmb.trackman_db.batters_stats_2025
    '''
    return client.query(query).result().to_dataframe(bqstorage_client=bqstorageclient)

# ----------------------------------------------------------------------
# CONSTANTES
# ----------------------------------------------------------------------
_DEFAULT_DIR_TEMP = os.path.join('BaseballBatterPitcherReports', 'Batter')
_DEFAULT_DIR_HOMEPLATE = os.path.join('BaseballBatterPitcherReports')
_DEFAULT_IMG_CSV = os.path.join('img', 'img_equipos.csv')

x_radio = 0.83083335
y_low, y_high = 1.5442, 3.455833
x = np.linspace(1, 4, 10)
y = np.linspace(1, 4, 10)
xbin = np.linspace(-x_radio - 0.53, x_radio + 0.53, 6)
ybin = np.linspace(y_low - 0.65, y_high + 0.65, 6)

# ----------------------------------------------------------------------
# UTILIDADES
# ----------------------------------------------------------------------
def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def classification_barreled(exitspeed, angle):
    if (exitspeed >= 116) and (8 < angle < 50):
        return 1
    elif 99 < exitspeed < 116:
        dif_class = exitspeed - 99
        angle_min = 25 - dif_class
        angle_max = 31 + dif_class
        return 1 if (angle_min < angle < angle_max) else 0
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
        lambda r: classification_barreled(r['ExitSpeed'], r['Angle']), axis=1
    )
    df_barrels = df_game.groupby('Batter').is_barreled.sum().rename('Barrels')

    df_team = (df_game.sort_values(['Batter', 'fecha_carga'], ascending=[True, False])
                     .drop_duplicates(subset='Batter', keep='first')
                     .groupby('Batter').BatterTeam.first())

    dfs = [df_pa, df_dhr, df_barrels, df_team]
    df_all = reduce(lambda l, r: pd.concat([l, r], axis=1), dfs)
    df_all['Barr%'] = (df_all['Barrels'] / df_all['PA']).map("{:.1%}".format)

    order_cols = ['PA', 'HR', 'Barrels', 'Barr%', 'BatterTeam']
    df_all['HR'] = df_all['HR'].fillna(0).astype(int)
    df_all.dropna(subset=['PA'], inplace=True)
    df_all['PA'] = df_all['PA'].fillna(0).astype(int)
    df_all = df_all[order_cols].fillna('')
    df_all.index.name = 'Nombre'
    return df_all

def get_stats_of_player(name_batter: str, df_stats: pd.DataFrame):
    return pd.DataFrame(df_stats.loc[name_batter]).T, df_stats.loc[name_batter]['BatterTeam']

# ----------------------------------------------------------------------
# ESTILOS Y EXPORTACIÓN
# ----------------------------------------------------------------------
def create_style_batter(df_temp: pd.DataFrame):
    styles = [
        dict(selector="th", props=[("font-size", "200%"),
                                   ("text-align", "center"),
                                   ('border-top', '2px solid black'),
                                   ('border-bottom', '2px solid black'),
                                   ('border-left', '2px solid black'),
                                   ('border-right', '2px solid black')]),
        dict(selector="td", props=[("font-size", "200%"),
                                   ("text-align", "center"),
                                   ('border-left', '1px solid black'),
                                   ('border-right', '1px solid black'),
                                   ('border-bottom', '1px solid black')]),
        dict(selector="caption", props=[("caption-side", "bottom")])
    ]
    return df_temp.style.set_table_styles(styles).hide(axis='index')

def from_df_to_tablepng(batter_name, team, dir_temp, html_temp, name):
    dir_team = os.path.join(dir_temp, team, batter_name)
    _ensure_dir(dir_team)
    dfi.export(html_temp, os.path.join(dir_team, f"{name}.png"), table_conversion="matplotlib")

def save_fig(dir_temp, team, batter_name, chart, chart_name, dpi=210):
    dir_team = os.path.join(dir_temp, team, batter_name)
    _ensure_dir(dir_team)
    if chart_name == 'slugging_general_left':
        dpi = 150
    out_path = os.path.join(dir_team, f"{chart_name}.png")
    chart.savefig(out_path, dpi=dpi, bbox_inches='tight', pad_inches=0.2)
    plt.close(chart)
    return out_path

# ----------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: SOLO EXTERNA
# ----------------------------------------------------------------------
def create_report_full(batter_name,
                       dict_short: dict,
                       dir_temp: str = _DEFAULT_DIR_TEMP,
                       dir_homeplate: str = _DEFAULT_DIR_HOMEPLATE,
                       img_csv_path: str = _DEFAULT_IMG_CSV):
    """
    Genera el reporte PDF del bateador usando únicamente datos de BigQuery.
    """
    # Carga externa
    df_games = _external_load_batter_games()
    df_stats = create_stats_table(df_games)

    # Tabla de stats
    table, team = get_stats_of_player(batter_name, df_stats)
    table['BatterTeam'] = table['BatterTeam'].map(lambda t: dict_short.get(t, t))

    dir_images = os.path.join(dir_temp, team, batter_name)
    _ensure_dir(dir_images)

    # Tabla 1
    html_temp = create_style_batter(table)
    from_df_to_tablepng(batter_name, team, dir_temp, html_temp, 'table_1')

    # Slugging general
    fig1 = create_slogging_chart_all(batter_name, 'Left', df_games)
    save_fig(dir_temp, team, batter_name, fig1, 'slugging_general_left')
    fig2 = create_slogging_chart_all(batter_name, 'Right', df_games)
    save_fig(dir_temp, team, batter_name, fig2, 'slugging_general_right')

    # Slugging por tipo
    fig3, n_launch_left = create_slogging_chart_by_type(batter_name, 'Left', df_games)
    save_fig(dir_temp, team, batter_name, fig3, 'slugging_by_launch_left')
    fig4, n_launch_right = create_slogging_chart_by_type(batter_name, 'Right', df_games)
    save_fig(dir_temp, team, batter_name, fig4, 'slugging_by_launch_right')

    # Tablas xAVG
    fig5 = avg_hit_chart(batter_name, 'Left', df_games)
    save_fig(dir_temp, team, batter_name, fig5, 'table_hit_left')
    fig6 = avg_hit_chart(batter_name, 'Right', df_games)
    save_fig(dir_temp, team, batter_name, fig6, 'table_hit_right')

    # KDEs
    fig7 = create_heatmap_hit(df_games, batter_name, 'Left')
    save_fig(dir_temp, team, batter_name, fig7, 'kde_hit_left')
    fig8 = create_heatmap_hit(df_games, batter_name, 'Right')
    save_fig(dir_temp, team, batter_name, fig8, 'kde_hit_right')

    # Spray charts (stubs)
    spray_probability_conditional(df_games, batter_name, team, side='Left',
                                  title="Addi zone probs", display_title=True, fig_size=(9, 8))
    spray_probability_conditional(df_games, batter_name, team, side='Right',
                                  title="Addi zone probs", display_title=True, fig_size=(9, 8))
    spray_probability_conditional(df_games, batter_name, team, side='Left', strikes=2,
                                  title="Strikes = 2", display_title=True, fig_size=(9, 8))
    spray_probability_conditional(df_games, batter_name, team, side='Right', strikes=2,
                                  title="Strikes = 2", display_title=True, fig_size=(9, 8))

    # PDF final
    out_pdf = create_report(batter_name, team, dir_images, dict_short,
                            n_launch_left, n_launch_right, dir_homeplate=dir_homeplate)
    return out_pdf

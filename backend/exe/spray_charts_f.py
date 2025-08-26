import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Union, Optional
import logging # borrar log

from spray_chart_constructors_f import (
    landing_zone_classifier,
    zone_probabilities_infield,
    zone_probabilities_outfield,
    fill_zones_infield,
    fill_zones_outfield,
    prob_renorm,
    draw_field
)

# Configuración de logs
logger = logging.getLogger(__name__) # borrar log
logger.setLevel(logging.INFO) # borrar log

# ==== Rutas base portables ====
DIR_TEMP = os.path.join('BaseballBatterPitcherReports', 'Batter')

# ================== Utilidades internas ==================
def _ensure_dir(p: str):
    logger.debug(f"Verificando y creando directorio si no existe: {p}") # borrar log
    os.makedirs(p, exist_ok=True)
    logger.info(f"Directorio asegurado: {p}") # borrar log

def _save_input_df(df: pd.DataFrame, _dir_images_ignored: str, tag: str):
    """Guarda el DataFrame original recibido en CSV en el directorio actual de ejecución."""
    out_csv = os.path.join(os.getcwd(), f"{tag}_data.csv")
    try: # borrar log
        df.to_csv(out_csv, index=False)
        logger.info(f"DataFrame de entrada guardado en: {out_csv}") # borrar log
    except Exception as e: # borrar log
        logger.error(f"Error al guardar el DataFrame de entrada como CSV: {e}") # borrar log

# ================== Funciones públicas ==================

def spray_probability_conditional(
    data: pd.DataFrame,
    playerName: str,
    team: str,
    side: str,
    strikes: Union[int, bool] = False,
    title: Optional[str] = None,
    display_title: bool = False,
    fig_size=(9, 8)
):
    logger.info(f"Generando spray chart de probabilidad para {playerName} (vs {side}). Strikes: {strikes}.") # borrar log
    dir_images = os.path.join(DIR_TEMP, team, playerName)
    _ensure_dir(dir_images)
    _save_input_df(data, dir_images, tag="spray_prob")  # guarda DF original en cwd

    playerdf = data[data.Batter == playerName]
    playerdf = playerdf[playerdf.PitcherThrows == side]
    if strikes:
        playerdf = playerdf[playerdf.Strikes == strikes]
    
    logger.debug(f"DataFrame filtrado. Número de filas: {len(playerdf)}") # borrar log
    if playerdf.empty: # borrar log
        logger.warning("El DataFrame del jugador está vacío después de aplicar los filtros.") # borrar log
        return None # borrar log

    playerdf = landing_zone_classifier(playerdf, playerName)
    probs_infield = zone_probabilities_infield(playerdf)
    probs_outfield = zone_probabilities_outfield(playerdf)
    logger.debug("Probabilidades de zona de aterrizaje calculadas.") # borrar log

    probs_text_infield = (probs_infield * 100).round(2)
    text_infield = [f'{i}%' for i in probs_text_infield]
    text_coord_infield = [(90,130),(65,155),(35,175),(10,205),(-40,205),(-65,175),(-95,155),(-120,130)]
    logger.debug(f"Texto para zonas de infield: {text_infield}") # borrar log

    probs_text_outfield = (probs_outfield * 100).round(2)
    text_outfield = [f'{i}%' for i in probs_text_outfield]
    text_coord_outfield = [(195,260),(150,330),(90,360),(20,375),(-45,375),(-110,360),(-170,330),(-215,260)]
    logger.debug(f"Texto para zonas de outfield: {text_outfield}") # borrar log

    plt.figure(figsize=fig_size)
    fig = sns.scatterplot(x=[0], y=[0], alpha=0)
    draw_field()
    logger.debug("Campo de béisbol dibujado.") # borrar log

    fill_zones_outfield(prob_renorm(probs_outfield))
    if display_title:
        plt.title(
            f'{playerName} probability by zone '
            f'{"(Left)" if side=="Left" else "(Right)"}'
            f'{" - Strikes=2" if strikes else ""}',
            size=16
        )
    for i, txt in enumerate(text_outfield):
        x, y = text_coord_outfield[i]
        fig.text(x, y, txt, backgroundcolor='gray', c='white', weight='bold', fontsize=14)

    fill_zones_infield(prob_renorm(probs_infield))
    for i, txt in enumerate(text_infield):
        x, y = text_coord_infield[i]
        fig.text(x, y, txt, backgroundcolor='gray', c='white', weight='bold', fontsize=12)

    plt.gca().axes.get_xaxis().set_visible(False)
    plt.gca().axes.get_yaxis().set_visible(False)

    suffix = '_strikes_2' if strikes else ''
    fname = f"spray_chart_general_{'left' if side=='Left' else 'right'}{suffix}.png"
    out_path = os.path.join(dir_images, fname)
    try: # borrar log
        plt.savefig(out_path, bbox_inches='tight', pad_inches=0.0)
        logger.info(f"Gráfico de probabilidad guardado en: {out_path}") # borrar log
    except Exception as e: # borrar log
        logger.error(f"Error al guardar el gráfico de probabilidad: {e}") # borrar log
    plt.close()
    return fig

def spray_scatter(
    df: pd.DataFrame,
    playerName: str,
    team: str,
    side: str,
    strikes: Union[int, bool] = False,
    title: Optional[str] = None,
    display_title: bool = False,
    fig_size=(9, 8)
):
    logger.info(f"Generando spray chart de dispersión para {playerName} (vs {side}). Strikes: {strikes}.") # borrar log
    dir_images = os.path.join(DIR_TEMP, team, playerName)
    _ensure_dir(dir_images)
    _save_input_df(df, dir_images, tag="spray_scatter")  # guarda DF original en cwd

    bat = df[(df.Batter == playerName) & (df.PitcherThrows == side)].copy()
    if strikes:
        bat = bat[bat.Strikes == strikes]
    
    logger.debug(f"DataFrame filtrado. Número de filas: {len(bat)}") # borrar log

    dt = bat[(dt := bat)[['Bearing', 'PitchCall']].notna().all(axis=1) & (dt['PitchCall'] == "InPlay")].copy()
    if dt.empty:
        logger.warning("El DataFrame para el scatter plot está vacío.") # borrar log
        fig = plt.figure()
        plt.axis('off')
        return fig

    dt["Bearing"] = pd.to_numeric(dt["Bearing"], errors='coerce').fillna(0.0)
    dt["Distance"] = pd.to_numeric(dt["Distance"], errors='coerce').fillna(0.0)
    dt["X"] = -dt["Distance"] * np.sin(np.radians(dt["Bearing"]))
    dt["Y"] =  dt["Distance"] * np.cos(np.radians(dt["Bearing"]))
    logger.debug("Coordenadas X e Y calculadas para el scatter plot.") # borrar log

    plt.figure(figsize=fig_size)
    ax = sns.scatterplot(data=dt, x="X", y="Y", hue="AutoHitType")
    plt.ylim(0, 460)
    plt.xlim(-280, 280)
    ax.set_xlabel("Horizontal")
    ax.set_ylabel("Vertical")

    if display_title:
        plt.title(f'{playerName} Scatter plot Pitcher Throws {side}', size=16)

    draw_field()
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.gca().axes.get_yaxis().set_visible(False)
    logger.debug("Gráfico de dispersión creado.") # borrar log

    suffix = '_strikes_2' if strikes else ''
    fname = f"spray_chart_scatter_general_{'left' if side=='Left' else 'right'}{suffix}.png"
    out_path = os.path.join(dir_images, fname)
    try: # borrar log
        plt.savefig(out_path, bbox_inches='tight', pad_inches=0.0)
        logger.info(f"Gráfico de dispersión guardado en: {out_path}") # borrar log
    except Exception as e: # borrar log
        logger.error(f"Error al guardar el gráfico de dispersión: {e}") # borrar log
    plt.close()
    return ax
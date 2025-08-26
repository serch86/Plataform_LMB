import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
import numpy as np
import seaborn as sns
import warnings
import logging # borrar log

warnings.filterwarnings('ignore')

# Configuración de logs
logger = logging.getLogger(__name__) # borrar log
logger.setLevel(logging.INFO) # borrar log

lcol = ['#89ACFD', '#4962D3', '#F39476', '#C53133']
mycmap = LinearSegmentedColormap.from_list('my_cmap', lcol, N=1000)

###########################################################################################
# Utilidades geométricas / dibujo de campo
###########################################################################################

def elipse_parametric(t, u, v, a, b):
    logger.debug("Calculando coordenadas de elipse paramétrica.") # borrar log
    return u + a * np.cos(t), v + b * np.sin(t)

def draw_lines():
    logger.info("Dibujando líneas de foul.") # borrar log
    x = [325 * np.cos(np.pi / 4), 0, -325 * np.cos(np.pi / 4)]
    y = [325 * 0.7071, 0, 325 * 0.7071]
    plt.plot(x, y, '-', color='black')
    x = [63, 0, -63]
    y = [63, 127, 63]
    plt.plot(x, y, '-', color='black')

def field_lines():
    logger.info("Dibujando líneas de referencia del outfield.") # borrar log
    # líneas de referencia del outfield
    x = [-100, 0, 100]; y = [382, 0, 382]; plt.plot(x, y, "-", color="k")
    x = [-185, 0, 185]; y = [305, 0, 305]; plt.plot(x, y, "-", color="k")

def draw_zones():
    logger.info("Dibujando líneas divisorias de zonas.") # borrar log
    a, b, u, v = 277, 410, 0, 0
    t1, t2 = 0.6, 2.54
    angles = np.linspace(t1, t2, 9)
    points = [elipse_parametric(t, u, v, a, b) for t in angles]
    for px, py in points:
        plt.plot([0, px], [0, py], '-', color='gray', alpha=0.5)

def draw_outfield():
    logger.info("Dibujando línea del outfield.") # borrar log
    a, b, u, v = 277, 410, 0, 0
    t = np.linspace(0.6, 2.54, 100)
    x, y = elipse_parametric(t, u, v, a, b)
    plt.plot(x, y, 'black')

def draw_infield():
    logger.info("Dibujando línea del infield.") # borrar log
    a, b, u, v = 110, 165, 0, 0
    t = np.linspace(0.6, 2.54, 200)
    x, y = elipse_parametric(t, u, v, a, b)
    plt.plot(x, y, 'black')

def draw_mound():
    logger.info("Dibujando el montículo.") # borrar log
    a, b, u, v = 8, 8, 0, 60
    t = np.linspace(0, 2 * np.pi, 100)
    x, y = elipse_parametric(t, u, v, a, b)
    plt.plot(x, y, 'black')

def draw_field():
    logger.info("Dibujando el campo completo.") # borrar log
    draw_lines()
    draw_outfield()
    draw_infield()
    draw_mound()
    draw_zones()

###########################################################################################
# Landing zone classifier
###########################################################################################

def landing_zone_classifier(df: pd.DataFrame, player_name: str) -> pd.DataFrame:
    """Clasifica cada batazo del jugador por zona (1..8) y si es infield/outfield."""
    logger.info(f"Clasificando zonas de aterrizaje para el jugador: {player_name}") # borrar log
    playerdf = df[df.Batter == player_name].copy()
    
    if playerdf.empty: # borrar log
        logger.warning(f"No se encontraron datos para el jugador {player_name}.") # borrar log
        return pd.DataFrame() # borrar log

    # Ángulo matemático en radianes
    playerdf['MathTheta'] = np.where(
        playerdf['Bearing'] >= 0,
        (np.pi / 2) - np.deg2rad(playerdf['Bearing']),
        (np.pi / 2) + np.deg2rad(np.abs(playerdf['Bearing']))
    )
    logger.debug("Ángulo matemático (MathTheta) calculado.") # borrar log

    t1, t2 = 0.6, 2.54
    angles = np.linspace(t1, t2, 9)

    def landing_zone_row(theta: float) -> int:
        # normaliza theta al rango [0, pi]
        th = theta
        if th < 0:
            th = np.pi - th
        if 0 <= th < angles[1]:
            return 1
        for i in range(1, 8):
            if angles[i] <= th < angles[i + 1]:
                return i + 1
        return 8

    playerdf['landingZone'] = playerdf['MathTheta'].apply(landing_zone_row)
    logger.debug("Zona de aterrizaje (landingZone) asignada.") # borrar log

    # Infield / Outfield por distancia euclidiana
    def infield_outfield_row(row):
        x = row['Bearing']
        y = row['Distance']
        n = np.sqrt(x ** 2 + y ** 2)
        return 'infield' if (0 <= n <= 165) else 'outfield'

    playerdf['infieldOutfield'] = playerdf.apply(infield_outfield_row, axis=1)
    logger.debug("Infield/outfield clasificado.") # borrar log

    playerdf.dropna(subset=['landingZone', 'infieldOutfield'], inplace=True)
    logger.info(f"Clasificación de zonas completada. Filas restantes: {len(playerdf)}") # borrar log
    return playerdf

###########################################################################################
# Helpers de probabilidad / normalización
###########################################################################################

def line_origin(m, x):
    logger.debug("Calculando línea desde el origen.") # borrar log
    return m * x

def prob_renorm(probs: np.ndarray) -> np.ndarray:
    """Escala a [0,1] evitando división por cero cuando a==b."""
    logger.info("Normalizando las probabilidades.") # borrar log
    a = float(np.min(probs))
    b = float(np.max(probs))
    if b - a == 0:
        logger.warning("División por cero evitada en normalización. Retornando array de ceros.") # borrar log
        return np.zeros_like(probs, dtype=float)
    return (probs - a) / (b - a)

###############################################################################################
# INFIELD
###############################################################################################

def zone_infield(t1, t2):
    logger.debug("Calculando zona de infield.") # borrar log
    a, b, u, v = 110, 165, 0, 0
    t = np.linspace(t1, t2, 50)
    return elipse_parametric(t, u, v, a, b)

def zone_probabilities_infield(playerdf: pd.DataFrame) -> np.ndarray:
    logger.info("Calculando probabilidades para las zonas de infield.") # borrar log
    p = playerdf[playerdf['infieldOutfield'] == 'infield']
    if p.empty:
        logger.warning("DataFrame de infield vacío. Retornando probabilidades de cero.") # borrar log
        return np.zeros(8)
    counts = p.groupby('landingZone').size()
    counts = (pd.Series(0, index=range(1, 9)) + counts).fillna(0)
    N = counts.sum()
    logger.debug(f"Conteo de infield por zona: {counts.to_dict()}. Total: {N}") # borrar log
    return (counts / N).to_numpy()

def fill_zones_infield(probabilities: np.ndarray):
    logger.info("Rellenando zonas de infield con colores de probabilidad.") # borrar log
    a, b, u, v = 110, 165, 0, 0
    t1, t2 = 0.6, 2.54
    angles = np.linspace(t1, t2, 9)
    points = [elipse_parametric(t, u, v, a, b) for t in angles]

    for i in range(len(angles) - 1):
        z1x, z1y = zone_infield(angles[i], angles[i + 1])
        x_down = np.linspace(0, points[i][0], 50)
        y_down = line_origin(points[i][1] / points[i][0], x_down)
        x_up = np.linspace(0, points[i + 1][0], 50)
        y_up = line_origin(points[i + 1][1] / points[i + 1][0], x_up)
        X = np.concatenate((x_down, z1x, x_up))
        Y = np.concatenate((y_down, z1y, y_up))
        plt.fill(X, Y, alpha=1, color=mycmap(probabilities[i]))
    logger.debug("Relleno de zonas de infield completado.") # borrar log

###############################################################################################
# OUTFIELD
###############################################################################################

def zone_outfield(t1, t2):
    logger.debug("Calculando zona de outfield.") # borrar log
    a, b, u, v = 277, 410, 0, 0
    t = np.linspace(t1, t2, 50)
    return elipse_parametric(t, u, v, a, b)

def zone_probabilities_outfield(playerdf: pd.DataFrame) -> np.ndarray:
    logger.info("Calculando probabilidades para las zonas de outfield.") # borrar log
    p = playerdf[playerdf['infieldOutfield'] == 'outfield']
    if p.empty:
        logger.warning("DataFrame de outfield vacío. Retornando probabilidades de cero.") # borrar log
        return np.zeros(8)
    counts = p.groupby('landingZone').size()
    counts = (pd.Series(0, index=range(1, 9)) + counts).fillna(0)
    N = counts.sum()
    logger.debug(f"Conteo de outfield por zona: {counts.to_dict()}. Total: {N}") # borrar log
    return (counts / N).to_numpy()

def fill_zones_outfield(probabilities: np.ndarray):
    logger.info("Rellenando zonas de outfield con colores de probabilidad.") # borrar log
    a, b, u, v = 277, 410, 0, 0
    t1, t2 = 0.6, 2.54
    angles = np.linspace(t1, t2, 9)
    points = [elipse_parametric(t, u, v, a, b) for t in angles]

    for i in range(len(angles) - 1):
        z1x, z1y = zone_outfield(angles[i], angles[i + 1])
        x_down = np.linspace(0, points[i][0], 50)
        y_down = line_origin(points[i][1] / points[i][0], x_down)
        x_up = np.linspace(0, points[i + 1][0], 50)
        y_up = line_origin(points[i + 1][1] / points[i + 1][0], x_up)
        X = np.concatenate((x_down, z1x, x_up))
        Y = np.concatenate((y_down, z1y, y_up))
        plt.fill(X, Y, alpha=0.5, color=mycmap(probabilities[i]))
    logger.debug("Relleno de zonas de outfield completado.") # borrar log
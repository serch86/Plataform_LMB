import pandas as pd
import numpy as np
import pickle
import glob
import datetime
from pandas.io import gbq
import pandas_gbq

from google.cloud import bigquery
import google.auth
from google.cloud import bigquery_storage

import matplotlib.pyplot as plt
import batter_tools as bt
import pitcher_tools as pt
from PyPDF2 import PdfFileMerger

from google.oauth2 import service_account
from googleapiclient import errors
from googleapiclient.discovery import build

import shutil
import unicodedata

import os
import logging

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("python_script.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Función para normalizar nombre:
# Recomiendo usar Tools.normalizar_nombre para consistencia con backend.
def clean_name(name):
    if not name:
        return 'Sin_nombre'
    rearranged_name = (name.split(',')[-1] + ' ' + name.split(',')[0]).strip().title().replace('  ', ' ')
    normalized = unicodedata.normalize('NFKD', rearranged_name)
    no_accent = ''.join([c for c in normalized if not unicodedata.combining(c)])
    return no_accent

# Función para eliminar archivos temporales .png
# Ruta fija, recomendable parametrizar y usar os.path.join para compatibilidad
def clean_directory(b_p):
    base_path = os.path.join('C://Users/serch/BaseballBatterPitcherReports', b_p)
    temporal_directories = glob.glob(os.path.join(base_path, '*'))

    for removed_dir in temporal_directories:
        if b_p == 'Pitcher':
            for root, dirs, files in os.walk(removed_dir, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file.endswith(".png"):
                        os.remove(file_path)
                if b_p == 'Pitcher' and not os.listdir(root):
                    os.rmdir(root)
        else:
            for root, dirs, files in os.walk(removed_dir):
                for file in files:
                    if file.endswith(".png") and "spray_chart" not in file:
                        os.remove(os.path.join(root, file))

# Diccionarios con nombres y abreviaturas de equipos
dict_baseball_teams = {...}
dict_baseball_teams_short = {...}

# Credenciales Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "baseballlmb-key.json"

logger.info('Lectura de datos desde BigQuery')
client = bigquery.Client()
query = '''SELECT ... FROM `baseballlmb.trackman_db.trackman_table`
           WHERE Temporada_Anio IN ("Invierno-2025","Verano-2025","Invierno-2024","Verano-2024")'''
query_job = client.query(query)

credentials, your_project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=credentials)

# Guardar resultado en DataFrame
df = query_job.result().to_dataframe(bqstorage_client=bqstorageclient)

# Aquí reemplazar clean_name por Tools.normalizar_nombre para coherencia
df['Batter'] = df['Batter'].apply(clean_name)
df['Pitcher'] = df['Pitcher'].apply(clean_name)

df_id_path = df.copy()

if not len(df):
    logger.error('No hay Suficientes Registros')
    raise Exception('No hay Suficientes Registros')

logger.info('Creando reportes Batter')

# Filtrado de datos bateadores
df_games = df.copy()
df_games.dropna(subset=['BatterId'], inplace=True)

# Reemplazar batter_news por lista extraída y normalizada usando Tools.procesar_archivo
df_games = df_games[df_games.Batter.isin(batter_news)]
df_games = df_games[df_games.fecha_carga != '-']
df_games['fecha_carga'] = pd.to_datetime(df_games['fecha_carga'])

# Crear tabla estadísticas con función externa, recibiendo datos ya normalizados
df_stats = bt.create_stats_table(df_games)

# Mapeo de tipos de lanzamiento
dict_pitchtype = {'Four-Seam':'Rectas y sinkers','Sinker':'Rectas y sinkers',
                  'Cutter':'Cutters y Sliders','Slider':'Cutters y Sliders',
                  'Curveball':'Curvas', 
                  'Changeup':'Cambios y Splits', 'Splitter':'Cambios y Splits'}

df_games['auto_pitch_type_2'] = df_games.AutoPitchType.map(dict_pitchtype)
df_games.dropna(subset='auto_pitch_type_2', inplace=True)

names = df_stats.index.tolist()
logger.info(f'numero_reportes_bateadores_por_hacer {len(names)}')

checkpoint_pos = 0
f = open("chekpoint_batter.txt","w+")

# Generar reportes bateadores
for name in names:
    try:
        r = bt.create_report_full(name, df_stats, df_games, dict_baseball_teams_short)
    except FileNotFoundError:
        logger.error(f'ERROR: Archivo no encontrado para bateador {name}')
        pass
    team_name = r.split('\\')[5]
    team_name = dict_baseball_teams_short.get(team_name, team_name)
    logger.info(f'{checkpoint_pos} {name} {team_name}')
    checkpoint_pos += 1
    f.write(f"Se quedó en el registro {checkpoint_pos}\n")

logger.info("Actualizando spray charts")
# Ejecutar script externo para gráficos
with open('create_spray_reports.py', 'r') as file:
    exec(file.read())

logger.info('Reportes terminados, hora de subirlos a Google Drive')

# Limpiar directorios temporales bateadores
clean_directory(b_p = 'Batter')

logger.info('Van los Pitchers')

dir_temp = 'Pitcher/'

# Filtrado datos pitchers
df_games = df.copy()
# Reemplazar pitcher_news por lista extraída y normalizada usando Tools.procesar_archivo
df_games = df_games[df_games.Pitcher.isin(pitcher_news)]
df_games = df_games[df_games.BatterSide.isin(['Left','Right'])]
df_games.dropna(subset=['Pitcher'],inplace=True)
df_games = df_games[df_games.fecha_carga != '-']
df_games['fecha_carga'] = pd.to_datetime(df_games['fecha_carga'])

df_table = df_games.copy()

dict_launch = {'Four-Seam':'Rectas','Changeup':'Cambios','Curveball':'Curva'}
df_table['AutoPitchType'] = df_table.AutoPitchType.apply(lambda x: dict_launch.get(x,x))

# Condiciones para filtros pitchers
cond1 = df_table['PitchofPA'] == 1
cond2 = df_table.any(axis=1)
cond3 = df_table['Strikes'] == 2

dict_cond = {'1er Pitcheo':cond1,'General':cond2,'2 Strikes':cond3}
dict_df_cond = {}
i=1
for cond in dict_cond.values():
    df_cond = df_table[cond]
    df_temp_num = df_cond.groupby(['Pitcher','BatterSide','AutoPitchType']).size()
    df_div = df_temp_num.unstack(1)
    dict_df_cond[i] = df_div
    i+=1

df_table['team_pitcher'] = df_table.PitcherTeam.map(dict_baseball_teams)

dict_pitchtype = {'Rectas':'Rectas y sinkers','Sinker':'Rectas y sinkers',
                  'Cutter':'Cutters y Sliders','Slider':'Cutters y Sliders',
                  'Curva':'Curvas', 
                  'Cambios':'Cambios y Splits', 'Splitter':'Cambios y Splits'}

df_table['auto_pitch_type_2'] = df_table.AutoPitchType.map(dict_pitchtype)

name_pitchers = sorted(df_table.Pitcher.unique())
logger.info(f'Se realizarán {len(name_pitchers)} reportes de pitchers')

checkpoint_pos = 0
# Generar reportes pitchers
for name in name_pitchers:
    logger.info(f'{checkpoint_pos} {name}')
    try:
        r = pt.create_report_full(df_table, name, dict_df_cond, dict_cond, dict_baseball_teams_short)
    except KeyError:
        logger.error(f'--ERROR-- para pitcher {name}')
        continue
    checkpoint_pos += 1

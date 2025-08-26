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

def clean_name(name):
    if not name:
        return 'Sin_nombre'
    rearranged_name = (name.split(',')[-1] + ' ' + name.split(',')[0]).strip().title().replace('  ', ' ')
    # Normalizar y eliminar acentos
    normalized = unicodedata.normalize('NFKD', rearranged_name)
    no_accent = ''.join([c for c in normalized if not unicodedata.combining(c)])
    return no_accent

def clean_directory(b_p):
    #print('Se eliminan archivos temporales')
    # Usando os.path.join para construir la ruta es más seguro y flexible
    base_path = os.path.join('C://Users/serch/BaseballBatterPitcherReports', b_p)
    temporal_directories = glob.glob(os.path.join(base_path, '*'))

    for removed_dir in temporal_directories:
        # Procesar cada directorio encontrado
        if b_p == 'Pitcher':
            for root, dirs, files in os.walk(removed_dir, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file.endswith(".png"):
                        os.remove(file_path)
                        #print(f"Eliminado: {file_path}")
                
                # Después de eliminar archivos, verifica si el directorio está vacío
                if b_p == 'Pitcher' and not os.listdir(root):
                    os.rmdir(root)
                    #print(f"Directorio eliminado: {root}")
        else:
            for root, dirs, files in os.walk(removed_dir):
                for file in files:
                    if file.endswith(".png") and "spray_chart" not in file:
                        os.remove(os.path.join(root, file))


dict_baseball_teams = {'SUL_MON':'Sultanes de Monterrey (Verano)', 
                      'GEN_MEX':'Generales de Durango',
                      'ACE_MEX':'Acereros del Norte',
                      'DIA_ROJ':'Diablos Rojos del México',
                      'VAQ_LAG':'Algodoneros Unión Laguna',
                      'AGU_VER':'El Aguila de Veracruz',
                      'GUE_MEX':'Guerreros de Oaxaca',
                      'MAR_GUA':'Mariachis de Guadalajara',
                      'LEO_MEX':'Leones de Yucatán',
                      'REI_MEX':'Rieleros de Aguascalientes',
                      'PER_MEX':'Pericos de Puebla',
                      'SAR_SAL':'Saraperos de Saltillo',
                      'PIR_MEX':'Piratas de Campeche',
                      'TIG_QUI':'Tigres de Quintana Roo',
                      'TOR_TIJ':'Toros de Tijuana',
                      'BRA_MEX':'Bravos de Leon',
                      'OLM_MEX':'Olmecas de Tabasco',
                      'ROJ_MEX':'Tecolotes de los Dos Laredos',
                      
                      'SUL_MON1':'Sultanes de Monterrey (Invierno)', 
                      'AGU_MEX':'Águilas de Mexicali',
                      'CHA_JAL1':'Charros de Jalisco (Verano)',
                      'CHA_JAL':'Charros de Jalisco (Invierno)',
                      'YAQ_OBR': 'Yaquis Ciudad Obregon',
                      'HER':'Naranjeros de Hermosillo',
                      'CAN_LOS':'Caneros Los Mochis',
                      'VEN_MAZ':'Venados de Mazatlan',
                      'TOM_CUL':'Tomateros de Culiacan',
                      'ALG_GUA':'Algodoneros de Guasave',
                      'MAY_NAV':'Mayos de Navajoa',
                      'LMB_WIN6': 'Pericos de Puebla',

                      'DOR_CHI':'Dorados de Chihuahua',
                      'CON_QUE':'Conspiradores de Queretaro',

                      'MXC': 'Aguilas de Mexicali',

                      'RAM_ARA':'Ramón Arano',
                      'NEL_BAR':'Nelson Barrera'}

plt.rcParams["font.family"] = "Times New Roman"

dict_baseball_teams_short = {'SUL_MON':'Monterrey (Verano)',
                             'GEN_MEX':'Durango',
                             'ACE_MEX':'Acereros_Norte',
                             'DIA_ROJ':'México',
                             'VAQ_LAG':'Unión_Laguna',
                             'AGU_VER':'Veracruz',
                             'GUE_MEX':'Oaxaca',
                             'MAR_GUA':'Guadalajara',
                             'LEO_MEX':'Yucatán',
                             'REI_MEX':'Aguascalientes',
                             'PER_MEX':'Puebla',
                             'SAR_SAL':'Saltillo',
                             'PIR_MEX':'Campeche',
                             'TIG_QUI':'Quintana_Roo',
                             'TOR_TIJ':'Tijuana',
                             'BRA_MEX':'Leon',
                             'OLM_MEX':'Tabasco',
                             'ROJ_MEX':'Dos_Laredos',

                             'SUL_MON1':'Monterrey (Invernal)', 
                             'AGU_MEX':'Mexicali',
                             'CHA_JAL':'Jalisco (Invernal)',
                             'CHA_JAL1':'Jalisco (Verano)',
                             'YAQ_OBR':'Obregon',
                             'HER':'Hermosillo',
                             'CAN_LOS':'Los_Mochis',
                             'VEN_MAZ':'Mazatlan',
                             'TOM_CUL':'Culiacan',
                             'ALG_GUA':'Guasave',
                             'MAY_NAV':'Navajoa',
                             'LMB_WIN6':'Puebla',
                             
                             'DOR_CHI':'Chihuahua',
                             'CON_QUE':'Queretaro',

                             'MXC': 'Mexicali',
                             'RAM_ARA':'Ramón Arano',
                             'NEL_BAR':'Nelson Barrera'}



# QUITAR ANTES DE SUBIR A INSTANCIA
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "baseballlmb-key.json"

print('Lectura de datos desde BigQuery')
# lectura tabla bigquery
client = bigquery.Client()
query = '''SELECT 
Angle,AutoHitType,AutoPitchType,AwayTeam,
BatterId,Batter,BatterSide,BatterTeam,Bearing,
CatcherTeam,Date,Distance,ExitSpeed,HomeTeam,HorzBreak,KorBB,
InducedVertBreak,PitcherId,Pitcher,PitcherTeam,PitchCall,PitcherThrows,PitchofPA,
PlateLocHeight,PlateLocSide,PlayResult,RelSpeed,SpinRate,Strikes,Temporada,
Temporada_Anio,id_path,fecha_carga 
FROM `baseballlmb.trackman_db.trackman_table` 
WHERE Temporada_Anio IN ("Invierno-2025","Verano-2025",
                         "Invierno-2024","Verano-2024")
'''
query_job = client.query(query)
# ingresar credenciales para lectura rapida
credentials, your_project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=credentials)
# se guarda en df
df = query_job.result().to_dataframe(bqstorage_client=bqstorageclient)
df['Batter'] = df['Batter'].apply(clean_name)
df['Pitcher'] = df['Pitcher'].apply(clean_name)

df_id_path = df.copy()

if not len(df):
    raise Exception('No hay Suficientes Registros')

print('Creando reportes Batter')

df_games = df.copy()
df_games.dropna(subset=['BatterId'], inplace=True)
df_games = df_games[df_games.Batter.isin(batter_news)]
df_games = df_games[df_games.fecha_carga != '-']
df_games['fecha_carga'] = pd.to_datetime(df_games['fecha_carga'])

df_stats = bt.create_stats_table(df_games)
dict_pitchtype = {'Four-Seam':'Rectas y sinkers','Sinker':'Rectas y sinkers',
                  'Cutter':'Cutters y Sliders','Slider':'Cutters y Sliders',
                  'Curveball':'Curvas', 
                  'Changeup':'Cambios y Splits', 'Splitter':'Cambios y Splits'}

df_games['auto_pitch_type_2'] = df_games.AutoPitchType.map(dict_pitchtype)
df_games.dropna(subset='auto_pitch_type_2', inplace=True)

names = df_stats.index.tolist()
print('numero_reportes_bateadores_por_hacer ', len(names))


checkpoint_pos = 0
f = open("chekpoint_batter.txt","w+")

for name in names:
    try:
        r = bt.create_report_full(name, df_stats, df_games, dict_baseball_teams_short)
    except FileNotFoundError:
        print('ERROR'*50)
        pass
    #except:
    #    print('ERROR DE ALGO'*20)
    #    pass
    team_name = r.split('\\')[5]
    team_name = dict_baseball_teams_short.get(team_name, team_name)
    print(checkpoint_pos, name, team_name)
    checkpoint_pos += 1
    f.write("Se quedo en el registro %s" % (checkpoint_pos))

print("Actualizando spray charts")
with open('create_spray_reports.py', 'r') as file:
    exec(file.read())

print('Reportes terminados, hora de subirlos a Google Drive')
# Especifica los parámetros
directory = 'Batter'  # Reemplaza con la ruta a tu directorio de PDFs
name_reports = 'batters'

# Funcion para eliminar imagenes y checkpoints una vez creadas.
clean_directory(b_p = 'Batter')

print('Van los Pitchers')

dir_temp = 'Pitcher/'

df_games = df.copy()
df_games = df_games[df_games.Pitcher.isin(pitcher_news)]
df_games = df_games[df_games.BatterSide.isin(['Left','Right'])]
df_games.dropna(subset=['Pitcher'],inplace=True)
df_games = df_games[df_games.fecha_carga != '-']
df_games['fecha_carga'] = pd.to_datetime(df_games['fecha_carga'])

df_table = df_games.copy()

dict_launch = {'Four-Seam':'Rectas','Changeup':'Cambios','Curveball':'Curva'}
df_table['AutoPitchType'] = df_table.AutoPitchType.apply(lambda x: dict_launch.get(x,x))

cond1 = df_table['PitchofPA'] == 1
cond2 = df_table.any(axis=1)
cond3 = df_table['Strikes'] == 2

dict_cond = {'1er Pitcheo':cond1,'General':cond2,'2 Strikes':cond3}
dict_df_cond = {}
i=1
for cond in dict_cond.values():
    df_cond = df_table[cond]
    df_temp_num = df_cond.groupby(
        ['Pitcher','BatterSide','AutoPitchType']).size()
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
print('Se realizaran %s' %len(name_pitchers))
checkpoint_pos = 0

for name in name_pitchers:
    print(checkpoint_pos, name)
    try:
        r = pt.create_report_full(df_table, name, dict_df_cond, dict_cond, dict_baseball_teams_short)
    except KeyError:
        print('--ERROR--'*5)
        print(name)
        print('--ERROR--'*5)
        continue
    #except FileNotFoundError:
    #    print(name,'Error por table_1.html')
    #    continue
        
    checkpoint_pos += 1


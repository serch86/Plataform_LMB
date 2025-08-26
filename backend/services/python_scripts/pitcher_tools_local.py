import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import fpdf
import dataframe_image as dfi
from html2image import Html2Image

# -------------------------------------------
# Conecta BigQuery, crea clientes para ejecutar SQL y descargar datos.
# _external_load_pitcher_stats lanza una consulta fija sobre la tabla de lanzadores 2025 
# y devuelve los resultados como DataFrame
# -------------------------------------------
'''
from google.cloud import bigquery
import google.auth
from google.cloud import bigquery_storage

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "baseballlmb-key.json"
credentials, your_project_id = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=credentials)
client = bigquery.Client()

def _external_load_pitcher_stats():
    # Query BigQuery
    query = '''
        SELECT Pitcher, AutoPitchType, RelSpeed, SpinRate, BatterSide, PlateLocSide, PlateLocHeight, Date
        FROM baseballlmb.trackman_db.pitchers_stats_2025
    '''
    df_pitch = client.query(query).result().to_dataframe(bqstorage_client=bqstorageclient)
    return df_pitch
'''
# -------------------------------------------

dir_temp = 'Pitcher\\'                    # Carpeta temporal
dir_homeplate = 'BaseballBatterPitcherReports\\'  # Carpeta imágenes home plate

def get_last_games(df_games, pitcher):
    d_t = df_games[df_games.Pitcher == pitcher].sort_index()
    last_games = sorted(d_t.id_path.unique())[-5:]
    return d_t[d_t['id_path'].isin(last_games)]

def get_perc_shot(pitcher, df_perc):
    return df_perc.loc[pitcher].dropna()

def get_range_mean(pitcher, df_range_mean_2):
    temp = df_range_mean_2.query('Pitcher == @pitcher').drop(['min','max'],axis=1)
    return temp[['rango','mean','Spin']]

def get_table_1(t1,t2):
    t3 = t2.join(t1).rename(columns={'rango':'Range','mean':'Común',t2.index[0][0]:'%Uso'})
    t3 = t3.droplevel(0)
    t3 = t3.sort_values('%Uso', ascending=False)
    t3['%Uso'] = t3['%Uso'].apply(lambda x:'{}%'.format(x))
    t3.index.name='Pitches'
    return t3

def scatter_pitcher(df_table, pitcher, auto_all, colours):
    df_pitcher_scatter = df_table[df_table.Pitcher == pitcher].dropna(
        subset=['InducedVertBreak', 'HorzBreak','AutoPitchType'])
    if len(df_pitcher_scatter) == 0:
        print('sin datos')
        return False
    fig1, ax = plt.subplots(figsize=(5,5))
    sns.scatterplot(data=df_pitcher_scatter,
                    y='InducedVertBreak', x='HorzBreak', hue='AutoPitchType',
                    alpha=0.7, palette=colours, ax=ax)
    plt.yticks(range(-30,31,10))
    plt.ylim(-10,25)
    ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    ax.legend(frameon=False, bbox_to_anchor=(1.5,0.7), ncol=1, fontsize=14)
    sns.despine(top=True, right=True, left=False, bottom=True, ax=ax)
    plt.ylabel('')
    plt.xlabel('')
    return fig1

def pie_charts(dict_df_cond, dict_cond, pitcher, side):
    dict_colors = {'Sinker': 'royalblue', 'Cambios': 'darkorange', 'Cutter': 'g', 'Slider': 'firebrick',
                   'Rectas': 'mediumpurple', 'Curva': 'saddlebrown', 'Splitter': 'grey', 'Other': 'white', np.nan:'white'}
    plt.rcParams['font.size'] = 25
    dict_side = {'Left': 'vs Zurdos', 'Right':'vs Derechos'}
    list_title = list(dict_cond.keys())
    fig = plt.figure(figsize=(20,10))
    for i in range(1,4):
        ax = plt.subplot(1,3,i)
        df_div = dict_df_cond[i]
        df_query = df_div.query('Pitcher == @pitcher').droplevel(0)
        df_plot = df_query[side].dropna()
        total = df_plot.sum()
        serie_temp = df_plot/total
        idx_drop = serie_temp[serie_temp < 0.03].index
        if serie_temp.sum() == 1:
            serie_temp.iloc[0] -= 0.0001
        df_plot = serie_temp.drop(idx_drop) if len(idx_drop) else serie_temp.copy()
        if len(df_plot) == 0:
            plt.axis('off')
            continue
        try:
            df_plot.plot.pie(autopct='%.0f%%', labels=['' for _ in df_plot.index],
                             colors=[dict_colors[key] for key in df_plot.index],
                             textprops=dict(color="w", fontsize=20),
                             wedgeprops={'linewidth':1.5, 'edgecolor':'grey'},
                             normalize=False, title=list_title[i-1])
        except ValueError:
            df_plot.plot.pie(autopct='%.0f%%', labels=['' for _ in df_plot.index],
                             colors=[dict_colors[key] for key in df_plot.index],
                             textprops=dict(color="w", fontsize=20),
                             wedgeprops={'linewidth':1.5, 'edgecolor':'grey'},
                             normalize=True, title=list_title[i-1])
        plt.ylabel(dict_side[side] if i == 1 else '', fontsize=40)
    markers = [plt.Line2D([0,0],[0,0],color=color, marker='s', linestyle='', markersize=15) for color in dict_colors.values()][:-2]
    if side == 'Left':
        plt.legend(markers, dict_colors.keys(), frameon=False, bbox_to_anchor=(1.0,1.2), ncol=10, fontsize=20)
    return fig

def pitcher_view_scatter(df_table, pitcher, side, colours):
    dict_colors = {'Rectas y sinkers':'royalblue', 'Cutters y Sliders':'g', 'Curvas':'saddlebrown', 'Cambios y Splits':'darkorange'}
    df_pitcher_scatter = df_table[(df_table.Pitcher == pitcher) & (df_table.BatterSide == side)].copy()
    df_pitcher_scatter = df_pitcher_scatter.sort_values('Date', ascending=False).head(100)
    fig, ax = plt.subplots(figsize=(10,8))
    plt.suptitle('VS '+side, fontsize=25)
    i = 0
    for pitch_type in dict_colors.keys():
        df_filtered = df_pitcher_scatter[df_pitcher_scatter["auto_pitch_type_2"] == pitch_type]
        ax = plt.subplot(1, len(dict_colors), i+1)
        i += 1
        plt.title(str(pitch_type), fontsize=18)
        x_radio = 0.83083335
        y_low, y_high = 1.5442, 3.455833
        x = np.linspace(-x_radio, x_radio, 10)
        y = np.linspace(y_low, y_high, 10)
        plt.plot(np.repeat(-x_radio, len(y)), y, c='black')
        plt.plot(np.repeat(x_radio, len(y)), y, c='black')
        plt.plot(x, np.repeat(y_low, len(x)), c='black')
        plt.plot(x, np.repeat(y_high, len(x)), c='black')
        plt.xlim(-1.7,1.7)
        plt.ylim(y_low - 0.5, y_high + 0.5)
        plt.axis('off')
        if len(df_filtered) > 0:
            sns.kdeplot(x=df_filtered["PlateLocSide"], y=df_filtered["PlateLocHeight"], fill=True,
                        cmap='coolwarm', alpha=0.6, bw_adjust=0.4, thresh=0.1, ax=ax)
            ax.tick_params(axis='both',which='both',bottom=False,top=False,left=False,right=False,
                           labelbottom=False,labelleft=False)
            sns.despine(top=True, right=True, left=True, bottom=True, ax=ax)
        plt.tight_layout()
    return fig

def create_style_launcherbyteam(df_temp):
    styles = [dict(selector="th", props=[("font-size","200%"),("text-align","center"),
                                         ('border-top','2px solid black'),('border-left','2px solid black'),
                                         ('border-right','2px solid black')]),
              dict(selector="td", props=[("font-size","200%"),("text-align","center"),
                                         ('border-left','1px solid black'),('border-right','1px solid black'),
                                         ('border-bottom','1px solid black')]),
              dict(selector="caption", props=[("caption-side","bottom")]),
              dict(selector="table", props=[('border-collapse','collapse'),('width','100%')])]
    df_temp = df_temp.reset_index().rename(columns={'index': 'Pitches'})
    return df_temp.style.set_table_styles(styles).applymap(lambda v: 'font-weight: bold', subset=['Pitches'])

def from_df_to_tablepng(pitcher_name, dir_temp, df_temp, name):
    os.makedirs(dir_temp, exist_ok=True)
    output_path = os.path.join(dir_temp, name + ".png")
    df_temp = df_temp.hide(axis='index')
    dfi.export(df_temp, output_path, table_conversion="html2image", fontsize=14)

def save_fig(dir_temp, pitcher_name, chart, chart_name, dpi=200):
    dir_ = os.path.join(dir_temp, pitcher_name)
    os.makedirs(dir_, exist_ok=True)
    chart.savefig(os.path.join(dir_, chart_name), dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close(chart)

def get_img_team(team_name):
    df_temp = pd.read_csv('img/img_equipos.csv')
    if len(team_name) > 7:
        return df_temp[df_temp.equipo == team_name]['ruta'].iloc[0]
    else:
        return df_temp[df_temp.equipo_abreviado == team_name]['ruta'].iloc[0]

def create_report(pitcher_name, team, dir_images, output_path, tt, dict_short):
    team_temp = dict_short.get(team, team)
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font('Times', 'B', 22)
    pdf.cell(0, 8, 'Pitcher: '+pitcher_name+', '+team_temp, border=0, ln=2, align='C')
    pdf.image(os.path.join(dir_images,'table_1.png'), x=0.1, y=20, w=90, h=140-tt)
    pdf.image(os.path.join(dir_images,'pie_right.png'), x=5, y=139, w=180, h=40)
    pdf.image(os.path.join(dir_images,'pie_left.png'),  x=5, y=100, w=180, h=42)
    pdf.image(os.path.join(dir_images,'scatter_mov.png'), x=90, y=20, w=110, h=80)
    pdf.image(os.path.join(dir_images,'scatter_left.png'), x=1, y=185, w=210, h=45)
    pdf.image(os.path.join(dir_homeplate,'home_plate.jpg'), x=90, y=235, w=40, h=12)
    pdf.image(os.path.join(dir_images,'scatter_right.png'), x=1, y=250, w=210, h=45)
    dir_output = os.path.dirname(dir_images)
    pdf.output(os.path.join(dir_output, pitcher_name+'.pdf'), dest='F')
    return os.path.join(output_path, pitcher_name+'.pdf')

def create_report_full(df_table, pitcher_name, dict_df_cond, dict_cond, dict_short):
    df_table = get_last_games(df_table, pitcher_name)
    df_team = df_table.sort_values(['Pitcher', 'fecha_carga'], ascending=[True, False]).drop_duplicates(subset='Pitcher', keep='first')
    team = df_team.loc[df_team['Pitcher'] == pitcher_name, 'PitcherTeam'].values[0]
    df_perc = (df_table.groupby('Pitcher').AutoPitchType.value_counts()/df_table.groupby('Pitcher').size()*100).round(2).unstack()
    t1 = get_perc_shot(pitcher_name, df_perc)
    df_range_mean_2 = df_table.groupby(['Pitcher','AutoPitchType']).agg({'RelSpeed':[lambda x: np.quantile(x,0.1),
                                                                                     lambda x: np.quantile(x,0.9),
                                                                                     'mean'],
                                                                         'SpinRate':'median'}).fillna(0).round().astype(int)
    df_range_mean_2.columns = ['min','max','mean','Spin']
    df_range_mean_2['rango'] = df_range_mean_2['min'].astype(str)+'-'+df_range_mean_2['max'].astype(str)
    t2 = get_range_mean(pitcher_name, df_range_mean_2)
    html_temp = create_style_launcherbyteam(get_table_1(t1,t2))
    from_df_to_tablepng(pitcher_name, os.path.join(dir_temp, team, pitcher_name), html_temp, 'table_1')
    auto_all = df_table.AutoPitchType.unique().tolist()
    colours = dict(zip(auto_all, plt.cm.tab10.colors[:len(auto_all)]))
    save_fig(os.path.join(dir_temp, team), pitcher_name, scatter_pitcher(df_table,pitcher_name,auto_all,colours), 'scatter_mov')
    save_fig(os.path.join(dir_temp, team), pitcher_name, pie_charts(dict_df_cond,dict_cond,pitcher_name,'Left'), 'pie_left')
    save_fig(os.path.join(dir_temp, team), pitcher_name, pie_charts(dict_df_cond,dict_cond,pitcher_name,'Right'), 'pie_right')
    save_fig(os.path.join(dir_temp, team), pitcher_name, pitcher_view_scatter(df_table,pitcher_name,'Left',colours), 'scatter_left')
    save_fig(os.path.join(dir_temp, team), pitcher_name, pitcher_view_scatter(df_table,pitcher_name,'Right',colours), 'scatter_right')
    num_pitches = df_table[df_table.Pitcher == pitcher_name].AutoPitchType.nunique()
    tt = 60 if num_pitches <= 4 else num_pitches*12
    dir_images = os.path.join(dir_temp, team, pitcher_name)
    return create_report(pitcher_name, team, dir_images, dir_images, tt, dict_short)

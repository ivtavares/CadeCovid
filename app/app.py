# -*- coding: utf-8 -*-

import requests
import pandas as pd
import numpy as np
import json
import os
import datetime
from datetime import timedelta

from flask import Flask, request, render_template, redirect, url_for, flash
from flask_cors import CORS, cross_origin

brasil_io = 'https://data.brasil.io/dataset/covid19/'
google = 'https://www.gstatic.com/covid19/mobility/'

json_state = 'state.json'
cases = 'caso.csv.gz'
cases_full = 'caso_full.csv.gz'
mobility = 'Global_Mobility_Report.csv'

mm_window = 14
trend_window = 15

def download_file(fname,origin):
    url = str(origin) + str(fname)
    result = requests.get(url)
    return open(fname , 'wb').write(result.content)

def load_file_to_df(fname,origin):
    download_file(fname,origin)
    df = pd.read_csv(fname, compression='gzip', header=0, sep=',', quotechar='"', error_bad_lines=False)
    return df

def state_map(df):
    with open(json_state) as json_file:
        state = json.load(json_file) 
    df['state'] = df['uf'].map(state)
    return df

def add_country(df_state):
    df_country = df_state.groupby(['date'], as_index=False).sum()
    df_country['state'] = 'BR'
    df_country['death_rate'] = df_country['deaths']/df_country['confirmed']
    return pd.concat([df_state, df_country])

def clean_df(df):
    df = df[df.place_type.eq('state')][['date','state','confirmed','deaths','is_last','estimated_population_2019','death_rate']]
    df = add_country(df)
    df['uf'] = df['state']
    df = state_map(df)
    return df[['uf', 'state', 'date', 'confirmed','deaths','is_last','estimated_population_2019','death_rate']]

def search_cases(uf):
  df_result = df_covid[df_covid.uf.eq(uf)] 
  last = df_result[df_result.date.eq(df_result.date.max())].to_json(orient='records')
  detail = df_result[['date','confirmed','deaths']].to_json(orient='records')
  result = {}
  result['last'] = json.loads(last)[0]
  result['detail'] = json.loads(detail)
  return result

def load_cases(file,origin):
    df = load_file_to_df(file,origin)
    df['date'] = pd.to_datetime(df.date)
    df['city_ibge_code'] = pd.to_numeric(df.city_ibge_code, downcast='unsigned')
    return df[['city_ibge_code', 'state', 'place_type', 'date', 'last_available_confirmed', 'new_confirmed']] \
        .sort_values('date')

def remove_cities(df):
    df = df[df.place_type == 'state'].rename(columns={'city_ibge_code': 'state_ibge_code'})
    df_new = df.groupby(['date'], as_index=False).sum()
    df_new['state'] = 'BR'
    df_new['state_ibge_code'] = 00
    return pd.concat([df, df_new])

def add_new_confirmed_mm(df, window):
    new_confirmed_df = (df[['date', 'state', 'state_ibge_code', 'new_confirmed']].set_index('date').groupby('state_ibge_code')
                        .new_confirmed.rolling(window).mean())

    return df.join(new_confirmed_df, on=['state_ibge_code', 'date'], rsuffix='_mm')

def add_new_trend_is_decreasing(df, window):
    is_decreasing_df = (df[['date', 'state', 'state_ibge_code', 'new_confirmed_mm']].set_index('date').groupby('state_ibge_code')
                        .new_confirmed_mm.rolling(window).apply(lambda x: x.iloc[0] > x.iloc[-1])
                        .replace({0: False, 1: True}).rename('is_decreasing'))

    return df.join(is_decreasing_df, on=['state_ibge_code', 'date'], rsuffix='_is_dec')

def convert_to_dict(df):
    last_cases = df.groupby(['state_ibge_code', 'state']).last()

    return last_cases[['date', 'is_decreasing']].reset_index().set_index('state').to_dict('index')

def state_status(file=cases_full, mm_window=mm_window, trend_window=trend_window):
    return (load_cases(file,brasil_io).pipe(remove_cities)
            .pipe(add_new_confirmed_mm, mm_window)
            .pipe(add_new_trend_is_decreasing, trend_window)
            .reset_index().pipe(convert_to_dict))

def search_trend(uf):
    return last_cases_dict[uf]  
    
def tratamento_dados_mobilidade(df):
    cd_pais = ['BR']  
  
    # Selecionando Dados do Brasil
    dados_brasil = df[df['country_region_code'].isin(cd_pais)]

    dados_brasil= dados_brasil[['country_region', 'iso_3166_2_code' , 'date' , 'retail_and_recreation_percent_change_from_baseline', 'grocery_and_pharmacy_percent_change_from_baseline' , 'parks_percent_change_from_baseline', 'transit_stations_percent_change_from_baseline' , 'workplaces_percent_change_from_baseline' , 'residential_percent_change_from_baseline'	]]

    dados_brasil.rename(columns={'country_region':'pais',
                            'iso_3166_2_code':'estado',
                            'date':'data',
                             'retail_and_recreation_percent_change_from_baseline':'varejo_lazer',
                             'grocery_and_pharmacy_percent_change_from_baseline':'mercados_farmacia',
                             'parks_percent_change_from_baseline':'parques',
                             'transit_stations_percent_change_from_baseline':'estacoes_transp_publico',
                             'workplaces_percent_change_from_baseline':'locais_de_trabalho',
                             'residential_percent_change_from_baseline':'residencias'}, 
                 inplace=True)


    dados_brasil['estado'] = dados_brasil['estado'].str[3:]   # Pegando Sigla da UF
 
    dados_brasil['estado'].fillna('BR', inplace = True)   # Substituindo valores nulos, por 'BR' - Dados Média do Brazil

    return (dados_brasil)

def dados_mobilidade(uf):
   
    result = {}
  
    # Última data relatório
    last_date = np.max(dados_brasil['data'])
    result['date'] = last_date

    # Dados últimos 7 dias date.today()
    data_ref = datetime.datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=-7)
    data_ref = data_ref.strftime('%Y-%m-%d')
    dados_7_dias = dados_brasil[(dados_brasil['estado']== uf) & (dados_brasil['data'] >= data_ref)]
           
    avg_7_ult_dias = np.mean(dados_7_dias['residencias'])
    result['avg'] = avg_7_ult_dias
    # Máxima tx. isolamento 2020-04-01
    dados_gerais = dados_brasil[(dados_brasil['estado']== uf) & (dados_brasil['data'] >= '2020-04-01')]
    max_tx_isol = np.max(dados_gerais['residencias'])
    result['max'] = max_tx_isol
    # Mínima tx. isolamento 2020-04-01
    min_tx_isol = np.min(dados_gerais['residencias'])
    result['min'] = min_tx_isol

    # list > json
    #result = json.dumps(result)
    return (result)

def search_mobility(uf):
    return dados_mobilidade(uf)
    
def search_uf(uf):
  result = {}
  r1 = search_cases(uf)
  r2 = search_trend(uf)
  r3 = search_mobility(uf)
  result['cases'] = r1
  result['is_decreasing'] = r2['is_decreasing']
  result['mobility'] = r3
  #return result
  return json.dumps(result)
  
#RUN LOAD DATA
df = load_file_to_df(cases,brasil_io)
df_covid = clean_df(df)
last_cases_dict = state_status()
download_file(mobility,google)
df = pd.read_csv(mobility)
dados_brasil = tratamento_dados_mobilidade(df)

#RUN FLASK API
app = Flask(__name__, static_url_path = "/assets", static_folder = "assets")
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/")
def home():
    return render_template('index.html')

@app.route('/api/v1/', methods=['GET'])
@cross_origin()
def apiteste():
    uf = request.args.get('uf')
    return search_uf(uf)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8080)

# -*- coding: utf-8 -*-

import requests
import pandas as pd

fname = 'caso.csv.gz'
url = 'https://data.brasil.io/dataset/covid19/' + fname
result = requests.get(url)
open(fname , 'wb').write(result.content)

df = pd.read_csv(fname, compression='gzip', header=0, sep=',', quotechar='"', error_bad_lines=False)
df_state = df[df.place_type.eq('state')][['date','state','confirmed','deaths','is_last','estimated_population_2019','death_rate']]
df_state = df_state[['date','state','confirmed','deaths','estimated_population_2019','death_rate']]

df_country = df_state.groupby(['date'], as_index=False).sum()
df_country['state'] = 'BR'
df_country['death_rate'] = df_country['deaths']/df_country['confirmed']

df_covid = pd.concat([df_state, df_country])

state = {}
state["BR"] = "Brasil"
state["AC"] = "Acre"
state["AL"] = "Alagoas"
state["AM"] = "Amazonas"
state["AP"] = "Amapá"
state["BA"] = "Bahia"
state["CE"] = "Ceará"
state["DF"] = "Distrito Federal"
state["ES"] = "Espírito Santo"
state["GO"] = "Goiás"
state["MA"] = "Maranhão"
state["MG"] = "Minas Gerais"
state["MS"] = "Mato Grosso do Sul"
state["MT"] = "Mato Grosso"
state["PA"] = "Pará"
state["PB"] = "Paraíba"
state["PE"] = "Pernambuco"
state["PI"] = "Piauí"
state["PR"] = "Paraná"
state["RJ"] = "Rio de Janeiro"
state["RN"] = "Rio Grande do Norte"
state["RO"] = "Rondônia"
state["RR"] = "Roraima"
state["RS"] = "Rio Grande do Sul"
state["SC"] = "Santa Catarina"
state["SE"] = "Sergipe"
state["SP"] = "São Paulo"
state["TO"] = "Tocantins"

df_covid['uf'] = df_covid['state']
df_covid['state'] = df_covid['state'].map(state)

import numpy as np
import json

from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from flask_cors import CORS, cross_origin

from sklearn.externals import joblib

app = Flask(__name__, static_url_path = "/assets", static_folder = "assets")
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

model = joblib.load('model.pkl')

@app.route("/")
def home():
    return render_template('index.html')

@app.route('/api/v1/', methods=['POST'])
def apiv1():
    data = request.get_json()
    prediction = np.array2string(model.predict(data))
    return jsonify(prediction)

@app.route('/api/teste/', methods=['GET'])
@cross_origin()
def apiteste():
    uf = request.args.get('uf')
    df_result = df_covid[df_covid.uf.eq(uf)] 
    last = df_result[df_result.date.eq(df_result.date.max())].to_json(orient='records')
    detail = df_result[['date','confirmed','deaths']].to_json(orient='records')
    result = {}
    result['last'] = json.loads(last)[0]
    result['detail'] = json.loads(detail)
    return json.dumps(result)

app.run()
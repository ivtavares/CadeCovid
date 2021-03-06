# -*- coding: utf-8 -*-
"""API_COVID_FINAL.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17XmxSm-7q8HWH3VDoGj8QBgQZZt2IaY8

# Curso Ciência de Dados e Big Data Puc Minas - Oferta 6 2019

# Disciplina: 
# PROJETO INTEGRADO – CONSTRUÇÃO APLICAÇÃO BIG DATA E ANALYTICS
Julho/2020

## Projeto: "Cadê Covid"

# API Dataset covid19 no Brasil.IO

site: https://github.com/turicas/covid19-br/blob/master/api.md#caso_full

Licença: Creative Commons Attribution ShareAlike

Fonte: Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen e colaboradores/Brasil.IO.
"""

import requests
import pandas as pd

# Realiza um loop pelas páginas da API, consolida em um DataFrame e exporta os dados em um arquivo csv

def crawn_brasil_io_dados_full():
    pagina = 1
    status = True
    df = ''
    urlMain = "https://brasil.io/api/dataset/covid19/caso_full/data/?page="
    compl = "&page_size=10000"
    while status:
        url = urlMain + str(pagina) + compl
        response = requests.get(url)
        status = response.status_code
        if status == 200:
            lst = response.json()
            df = pd.DataFrame(lst['results'])
            if pagina>1:
                df_concat = pd.concat([df_ant, df])
                print ('pagina '+str(pagina), "ok", 'total de dados: ', len(df_concat))
            else:
                df_concat = df
                print ('pagina '+str(pagina), "ok", 'total de dados: ', len(df))
        else:
            status = False
        pagina +=1
        df_ant =  df_concat

    # para utilização no google colab

    arquivo = '../data_source/brasil_io_caso_full.csv'
    df_concat.to_csv(arquivo, index=False, header=True)


    # Para testes

    # url = "https://brasil.io/api/dataset/covid19/caso/data" -> Versão simples da API
    # url = "https://brasil.io/api/dataset/covid19/caso_full/data" -> Versão Full da API
    # url = "https://brasil.io/api/dataset/covid19/caso_full/data/?page=1&page_size=10000"
    # response = requests.get(url)
    # print(response.status_code)

if __name__ == '__main__':
    crawn_brasil_io_dados_full()
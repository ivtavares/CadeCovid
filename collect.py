
import requests
def return_estados():
    ibge_estados = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
    resposta_estados = requests.get(ibge_estados)
    estados = resposta_estados.text
    print(estados)
    ibge_populacao = "https://servicodados.ibge.gov.br/api/v1/projecoes/populacao/"



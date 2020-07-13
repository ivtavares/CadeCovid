import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np

def crawl_ibge_states_density():
    with open('./config/ibge_states_density.json') as json_file:
        config = json.load(json_file)

    url = config['url']
    url_response = requests.get(url)

    if url_response.status_code == 200:
        # Extract data
        ibge_states_df = pd.read_html(url_response.text)[0]
        ibge_code_df = pd.read_csv(config["igbe_code_file"])

        # Transform data
        ibge_states_df.drop("Região", axis=1, inplace=True)
        ibge_states_df.columns = config["column_names"]
        null_values = ibge_states_df == "..."
        ibge_states_df[null_values] = np.nan
        ibge_states_df_mod = ibge_code_df.join(ibge_states_df.set_index("LOCALIDADE"), how="inner", on="LOCALIDADE")

        # Load data
        ibge_states_df_mod.to_csv(config["file_destination"], index=False)
        print("File downloaded")
    else:
        print("No connection")

        return url_response.status_code


if __name__ == "__main__":
    crawl_ibge_states_density()

import pandas as pd
from pyhocon import ConfigFactory


def load_cases(file):
    df = pd.read_csv(file)
    df['date'] = pd.to_datetime(df.date)

    return df.sort_values('date')


def remove_cities(df):
    df = df[df.place_type == 'state'].drop('city', axis=1).rename(columns={'city_ibge_code': 'state_ibge_code'})
    df['state_ibge_code'] = pd.to_numeric(df.state_ibge_code, downcast='unsigned')
    return df


def add_state_density(df, state_density_file, ano):
    state_density_df = pd.read_csv(state_density_file)[['CODIGO_IBGE', ano]].rename(columns={ano: 'population_density'})
    df = df.join(state_density_df.set_index('CODIGO_IBGE'), how='left', on='state_ibge_code')

    return df[['state_ibge_code', 'state', 'population_density', 'date', 'epidemiological_week',
               'estimated_population_2019', 'is_last', 'is_repeated', 'last_available_confirmed',
               'last_available_confirmed_per_100k_inhabitants', 'last_available_date',
               'last_available_death_rate', 'last_available_deaths', 'new_confirmed', 'new_deaths',
               'order_for_place', 'place_type']]


def add_new_confirmed_mm(df, window):
    new_confirmed_df = (df[['date', 'state_ibge_code', 'new_confirmed']].set_index('date').groupby('state_ibge_code')
                        .new_confirmed.rolling(window).mean())

    return df.join(new_confirmed_df, on=['state_ibge_code', 'date'], rsuffix='_mm')


def add_new_trend_is_decreasing(df, window):
    is_decreasing_df = (df[['date', 'state_ibge_code', 'new_confirmed_mm']].set_index('date').groupby('state_ibge_code')
                        .new_confirmed_mm.rolling(window).apply(lambda x: x.iloc[0] > x.iloc[-1])
                        .replace({0: False, 1: True}).rename('is_decreasing'))

    return df.join(is_decreasing_df, on=['state_ibge_code', 'date'], rsuffix='_is_dec')


def convert_to_dict(df):
    last_cases = df.groupby(['state_ibge_code', 'state']).last()

    return last_cases[['date', 'is_decreasing']].reset_index().set_index('state_ibge_code').to_dict('index')


def state_status(ibge_code):
    config = ConfigFactory.parse_file('config/state_status.conf')
    cases_csv = config.cases_csv
    state_density_csv = config.state_density_csv
    ano = config.ano
    mm_window = config.mm_window
    trend_window = config.trend_window

    last_cases_dict = (load_cases(cases_csv).pipe(remove_cities).pipe(add_state_density, state_density_csv, ano)
                       .pipe(add_new_confirmed_mm, mm_window).pipe(add_new_trend_is_decreasing, trend_window)
                       .reset_index().pipe(convert_to_dict))

    return last_cases_dict[ibge_code]


state_status(11)

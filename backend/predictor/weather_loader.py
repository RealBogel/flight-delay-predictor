import pandas as pd

def load_weather_data(weather_csv_path):
    weather = pd.read_csv(weather_csv_path, parse_dates=['time'])
    return weather

def load_and_merge_weather(flights_df, weather_csv_path):
    weather = load_weather_data(weather_csv_path)

    # Make sure FL_DATE is datetime
    flights_df['FL_DATE'] = pd.to_datetime(flights_df['FL_DATE'])

    flights = flights_df.copy()

    # Prepare weather for origin
    weather_origin = weather.rename(columns={
        'time': 'FL_DATE',
        'airport': 'ORIGIN',
        'tavg': 'ORIGIN_tavg',
        'tmin': 'ORIGIN_tmin',
        'tmax': 'ORIGIN_tmax',
        'prcp': 'ORIGIN_prcp',
        'snow': 'ORIGIN_snow',
        'wdir': 'ORIGIN_wdir',
        'wspd': 'ORIGIN_wspd',
        'wpgt': 'ORIGIN_wpgt',
        'pres': 'ORIGIN_pres',
        'tsun': 'ORIGIN_tsun'
    })[['FL_DATE', 'ORIGIN', 'ORIGIN_tavg', 'ORIGIN_tmin', 'ORIGIN_tmax', 'ORIGIN_prcp', 'ORIGIN_snow',
        'ORIGIN_wdir', 'ORIGIN_wspd', 'ORIGIN_wpgt', 'ORIGIN_pres', 'ORIGIN_tsun']]

    # Prepare weather for destination
    weather_dest = weather.rename(columns={
        'time': 'FL_DATE',
        'airport': 'DEST',
        'tavg': 'DEST_tavg',
        'tmin': 'DEST_tmin',
        'tmax': 'DEST_tmax',
        'prcp': 'DEST_prcp',
        'snow': 'DEST_snow',
        'wdir': 'DEST_wdir',
        'wspd': 'DEST_wspd',
        'wpgt': 'DEST_wpgt',
        'pres': 'DEST_pres',
        'tsun': 'DEST_tsun'
    })[['FL_DATE', 'DEST', 'DEST_tavg', 'DEST_tmin', 'DEST_tmax', 'DEST_prcp', 'DEST_snow',
        'DEST_wdir', 'DEST_wspd', 'DEST_wpgt', 'DEST_pres', 'DEST_tsun']]

    # Merge with origin weather
    flights = flights.merge(weather_origin, on=['FL_DATE', 'ORIGIN'], how='left')

    # Merge with destination weather
    flights = flights.merge(weather_dest, on=['FL_DATE', 'DEST'], how='left')

    return flights
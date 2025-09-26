import pandas as pd
import time
import logging
import os
from datetime import datetime
from meteostat import Stations, Point, Daily

# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Set up file paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # goes up to predictor/
AIRPORT_META_PATH = os.path.join(BASE_DIR, 'data', 'airports_meta.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'weather_airport_2019-2023.csv')

# --- Load airport metadata ---
airports_meta = pd.read_csv(AIRPORT_META_PATH)

# --- Set date range ---
start = datetime(2019, 1, 1)
end = datetime(2023, 12, 31)

weather_dfs = []

# Keep only necessary columns
airports_meta = airports_meta[['iata_code', 'latitude_deg', 'longitude_deg', 'iso_country']]

# Drop rows with missing IATA codes or coordinates
airports_meta = airports_meta.dropna(subset=['iata_code', 'latitude_deg', 'longitude_deg'])

# Drop duplicate airports by IATA code
airports_meta = airports_meta.drop_duplicates(subset='iata_code').reset_index(drop=True)

for idx, row in airports_meta.iterrows():
    code = row['iata_code']
    lat = row['latitude_deg']
    lon = row['longitude_deg']

    logging.info(f'Fetching weather for {code} ({lat}, {lon})...')
    location = Point(lat, lon)

    stations = Stations().nearby(lat, lon)
    station = stations.fetch(1)

    if station.empty:
        logging.warning(f"No station found near {code}, skipping.")
        continue

    station_id = station.index[0]
    logging.info(f"Using station {station_id} for {code}")

    data = Daily(station_id, start, end).fetch()

    if data.empty:
        logging.warning(f"No weather data for station {station_id} near {code}, skipping.")
        continue

    data['airport'] = code
    weather_dfs.append(data)
    time.sleep(1)  # Be kind to the API

# --- Save to CSV ---
if weather_dfs:
    weather_all = pd.concat(weather_dfs).reset_index()
    weather_all.to_csv(OUTPUT_PATH, index=False)
    logging.info(f'Saved combined weather data to {OUTPUT_PATH}')
else:
    logging.error("No weather data collected.")

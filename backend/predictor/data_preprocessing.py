import os

# data_preprocessing.py
import pandas as pd
import holidays
from .weather_loader import load_and_merge_weather
from .utils.time_features import time_of_day


def preprocess_flight_data(filepath: str, weather_csv_path: str):
    flights = pd.read_csv(filepath, parse_dates=["FL_DATE"])
    flights = flights.dropna(subset=["FL_DATE"])
    flights = load_and_merge_weather(flights, weather_csv_path)

    # Weather features
    weather_features = [col for col in flights.columns if col.startswith('ORIGIN_') or col.startswith('DEST_')]
    weather_numeric_cols = flights[weather_features].select_dtypes(include='number').columns
    flights[weather_numeric_cols] = flights[weather_numeric_cols].fillna(flights[weather_numeric_cols].median())

    # Label
    flights['ARR_DELAYED'] = (flights['ARR_DELAY'] > 15).astype(int)

    # Feature engineering
    flights['DAY_OF_WEEK'] = flights['FL_DATE'].dt.dayofweek
    flights['DEP_HOUR'] = flights['CRS_DEP_TIME'] // 100
    flights['MONTH'] = flights['FL_DATE'].dt.month
    flights['IS_WEEKEND'] = flights['DAY_OF_WEEK'].isin([5, 6]).astype(int)

    flights['DEP_AIRPORT_TRAFFIC'] = flights.groupby(['FL_DATE', 'ORIGIN'])['FL_DATE'].transform('count')
    flights['ARR_AIRPORT_TRAFFIC'] = flights.groupby(['FL_DATE', 'DEST'])['FL_DATE'].transform('count')

    flights['ROUTE'] = flights['ORIGIN'] + '-' + flights['DEST']
    flights['ROUTE_POPULARITY'] = flights.groupby('ROUTE')['ROUTE'].transform('count')

    flights['TIME_OF_DAY'] = flights['DEP_HOUR'].apply(time_of_day)
    flights['IS_MORNING'] = (flights['TIME_OF_DAY'] == 'morning').astype(int)
    flights['IS_AFTERNOON'] = (flights['TIME_OF_DAY'] == 'afternoon').astype(int)
    flights['IS_EVENING'] = (flights['TIME_OF_DAY'] == 'evening').astype(int)
    flights['IS_NIGHT'] = (flights['TIME_OF_DAY'] == 'night').astype(int)

    # Weather flags
    flights['ORIGIN_HEAVY_WIND'] = (flights['ORIGIN_wspd'] > 20).astype(int)
    flights['ORIGIN_PRECIP'] = (flights['ORIGIN_prcp'] > 0.1).astype(int)
    flights['ORIGIN_SNOW'] = (flights['ORIGIN_snow'] > 0).astype(int)

    flights['DEST_HEAVY_WIND'] = (flights['DEST_wspd'] > 20).astype(int)
    flights['DEST_PRECIP'] = (flights['DEST_prcp'] > 0.1).astype(int)
    flights['DEST_SNOW'] = (flights['DEST_snow'] > 0).astype(int)
    flights['TEMP_DIFF'] = (flights['ORIGIN_tavg'] - flights['DEST_tavg']).abs()

    us_holidays = holidays.UnitedStates(years=range(2019, 2024))
    flights['HOLIDAY_FLAG'] = flights['FL_DATE'].dt.date.isin(us_holidays).astype(int)

    flights.drop(columns=['CRS_DEP_TIME'], inplace=True)
    flights["AIRLINE_CODE"] = flights["AIRLINE"].astype("category").cat.codes
    flights["ORIGIN_CODE"] = flights["ORIGIN"].astype("category").cat.codes
    flights["DEST_CODE"] = flights["DEST"].astype("category").cat.codes

    return flights
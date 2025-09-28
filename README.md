# Flight Delay Predictor
Flight Delay Predictor is a full-stack web application that predicts the probability of a commercial flight being delayed.
- Frontend: React + Vite with a custom gauge visualization and responsive UI.
- Backend: Django REST API served on Render.
- Machine Learning: Trained XGBoost pipeline with scikit-learn preprocessing.
- APIs: AviationStack (flight info) and WeatherStack (real-time weather) integrated with fallback/simulated modes for development.
- Deployment: React frontend hosted on GitHub Pages, Django backend on Render.

## Users can enter a flight number and date, and the app returns:
- Probability of delay (visualized via an interactive gauge)
- Binary classification (On time / Delayed)
- Model version metadata

This project demonstrates end-to-end ML model deployment, including data preprocessing, model training, API integration, backend serving, and frontend visualization.

## Datasets used:

- Flight Delay and Cancellation Dataset (2019–2023)

- Airline Delay Dataset

- Custom dataset created by merging flight delay data with historical weather data from the Meteostat API.

These datasets were cleaned, merged, and engineered into features (time of day, weather conditions, airport codes, etc.) to train an XGBoost model for binary classification (Delayed vs. On time).

## Note on usage⚠️:
The backend is deployed on Render’s free tier, which “sleeps” after inactivity. The first request may take 10–20 seconds to wake the server.

import requests
import pandas as pd
import joblib
from datetime import datetime
import os


from dotenv import load_dotenv
from pathlib import Path

# Load backend/predictor/store.env explicitly (since manage.py is elsewhere)
load_dotenv((Path(__file__).resolve().parent / "store.env"))

# Feature switches (dev-friendly)
ALLOW_FALLBACK = os.getenv("PREDICTOR_ALLOW_FALLBACK") == "1"   # use a dummy flight row if API returns nothing
SIMULATE       = os.getenv("PREDICTOR_SIMULATE") == "1"         # skip real APIs entirely (always dummy)

print(f"[predictor] SIMULATE={SIMULATE}  ALLOW_FALLBACK={ALLOW_FALLBACK}")

# Read env vars (loaded in settings.py via load_dotenv)
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
WEATHERSTACK_API_KEY  = os.getenv("WEATHERSTACK_API_KEY")
MODEL_PATH = os.getenv(
    "MODEL_ARTIFACT",
    os.path.join(os.path.dirname(__file__), "models", "flight_delay_pipeline.joblib"),
)

# ---- Flight + Weather helpers (yours, unchanged) ----
def get_flight_details(api_key, flight_number, flight_date):

    """
    Free-plan friendly:
      - Use http:// (HTTPS is paid on Aviationstack free)
      - Do NOT filter by flight_date (free tier = live/near-real-time only)
    """

    if SIMULATE:
        dep_hour = 12
        airline_code = (flight_number[:2].upper()
                        if len(flight_number) >= 2 and flight_number[:2].isalpha()
                        else "UA")
        return {
            "AIRLINE_CODE": airline_code,
            "ORIGIN_CODE":  "SFO",
            "DEST_CODE":    "LAX",
            "DEP_HOUR":     dep_hour,
            "FL_DATE":      flight_date,
            "DAY_OF_WEEK":  datetime.strptime(flight_date, "%Y-%m-%d").weekday(),
            "MONTH":        int(flight_date.split("-")[1]),
        }
    
    base_url = "http://api.aviationstack.com/v1/flights"

    # Try a couple of free-tier-safe shapes
    attempts = [
        {"flight_iata": flight_number, "limit": 1},  # no date on free plan
    ]

    # Also try split airline + numeric number if pattern fits (UA245 -> UA + 245)
    if len(flight_number) >= 3 and flight_number[:2].isalpha() and flight_number[2:].isdigit():
        attempts.append({"airline_iata": flight_number[:2].upper(),
                         "flight_number": flight_number[2:],
                         "limit": 1})

    for params in attempts:
        try:
            q = {"access_key": api_key}
            q.update(params)
            r = requests.get(base_url, params=q, timeout=10)
            try:
                r.raise_for_status()
            except requests.HTTPError as e:
                # Surface the exact reason if free plan rejects something
                print("[Aviationstack HTTPError]", e, "URL:", r.url, "BODY:", r.text)
                continue

            data = r.json()
            if "error" in data:
                print("[Aviationstack ERROR]", data["error"], "Params:", params)
                continue

            if data.get("data"):
                flight = data["data"][0]
                dep = (flight.get("departure") or {})
                arr = (flight.get("arrival") or {})
                airline = (flight.get("airline") or {})

                # scheduled may be missing on free; try estimated/actual; default noon
                ts = dep.get("scheduled") or dep.get("estimated") or dep.get("actual")
                try:
                    dep_hour = int(ts.split("T")[1][:2]) if ts else 12
                except Exception:
                    dep_hour = 12

                return {
                    "AIRLINE_CODE": airline.get("iata") or flight_number[:2].upper(),
                    "ORIGIN_CODE":  dep.get("iata") or "SFO",
                    "DEST_CODE":    arr.get("iata") or "LAX",
                    "DEP_HOUR":     dep_hour,
                    "FL_DATE":      flight_date,  # keep incoming date for feature calc
                    "DAY_OF_WEEK":  datetime.strptime(flight_date, "%Y-%m-%d").weekday(),
                    "MONTH":        int(flight_date.split("-")[1]),
                }
            else:
                print(f"[WARN] No data for params {params}. URL:", r.url, "BODY:", r.text)
        except requests.RequestException as e:
            print(f"[ERROR] Aviationstack request failed for params {params}: {e}")

    if ALLOW_FALLBACK:
        print("[FALLBACK] Using dummy flight data because API returned no matching row.")
        airline_code = (flight_number[:2].upper()
                        if len(flight_number) >= 2 and flight_number[:2].isalpha()
                        else "UA")
        return {
            "AIRLINE_CODE": airline_code,
            "ORIGIN_CODE":  "SFO",
            "DEST_CODE":    "LAX",
            "DEP_HOUR":     12,
            "FL_DATE":      flight_date,
            "DAY_OF_WEEK":  datetime.strptime(flight_date, "%Y-%m-%d").weekday(),
            "MONTH":        int(flight_date.split("-")[1]),
        }

    return None
    
def get_weather_data(api_key, city_name, date):
    if SIMULATE:
        return {"TEMP_DIFF": 2, "PRECIP": 0, "SNOW": 0, "HEAVY_WIND": 0}
    """
    Free-plan friendly Weatherstack: use /current (historical is paid).
    We ignore 'date' on free and build simple features from current weather.
    """
    url = "http://api.weatherstack.com/current"
    params = {"access_key": api_key, "query": city_name}
    try:
        response = requests.get(url, params=params, timeout=10)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print("[Weatherstack HTTPError]", e, "URL:", response.url, "BODY:", response.text)
            return default_weather()
        data = response.json()
    except requests.RequestException as e:
        print(f"[ERROR] WeatherStack API request failed: {e}")
        return default_weather()

    cur = data.get("current") or {}
    # build minimal, robust features
    try:
        descs = cur.get("weather_descriptions") or []
        desc = " ".join([d.lower() for d in descs]) if isinstance(descs, list) else str(descs).lower()
        return {
            "TEMP_DIFF": abs((cur.get("temperature") or 20) - 20),
            "PRECIP":    float(cur.get("precip") or 0),
            "SNOW":      1 if ("snow" in desc) else 0,
            "HEAVY_WIND": 1 if (cur.get("wind_speed") or 0) > 25 else 0,
        }
    except Exception as e:
        print(f"[ERROR] Failed to parse Weatherstack current data: {e}")
        return default_weather()
    
def default_weather():
    return {"TEMP_DIFF": 0, "PRECIP": 0, "SNOW": 0, "HEAVY_WIND": 0}

_bundle = None
def _get_bundle():
    import joblib as _joblib
    global _bundle
    if _bundle is None:
        _bundle = _joblib.load(MODEL_PATH)  # {"pipeline","feature_order","version"}
    return _bundle

def _build_feature_row(flight_num: str, flight_date: str, aviation_key=None, weather_key=None):
    flight = get_flight_details(aviation_key, flight_num, flight_date)
    if not flight:
        return None, "Flight not found or failed to retrieve flight data."

    w_origin = get_weather_data(weather_key, flight["ORIGIN_CODE"], flight_date) or default_weather()
    w_dest   = get_weather_data(weather_key, flight["DEST_CODE"],  flight_date) or default_weather()

    row = {
        **flight,
        "IS_MORNING":   int(5  <= flight["DEP_HOUR"] < 12),
        "IS_AFTERNOON": int(12 <= flight["DEP_HOUR"] < 17),
        "IS_EVENING":   int(17 <= flight["DEP_HOUR"] < 21),
        "IS_NIGHT":     int(flight["DEP_HOUR"] >= 21 or flight["DEP_HOUR"] < 5),
        "ORIGIN_PRECIP":     w_origin["PRECIP"],
        "DEST_PRECIP":       w_dest["PRECIP"],
        "ORIGIN_SNOW":       w_origin["SNOW"],
        "DEST_SNOW":         w_dest["SNOW"],
        "ORIGIN_HEAVY_WIND": w_origin["HEAVY_WIND"],
        "DEST_HEAVY_WIND":   w_dest["HEAVY_WIND"],
        "TEMP_DIFF":         abs(w_origin["TEMP_DIFF"] - w_dest["TEMP_DIFF"]),
    }
    return row, None

# ---------- Public API ----------
def predict_flight_delay(
    flight_num, flight_date,
    aviation_key=os.getenv("AVIATIONSTACK_API_KEY"),
    weather_key=os.getenv("WEATHERSTACK_API_KEY")
):
    bundle = _get_bundle()
    cols = bundle["feature_order"]

    row, err = _build_feature_row(flight_num, flight_date, aviation_key, weather_key)
    if err:
        return {"error": err}

    import pandas as _pd
    X = _pd.DataFrame([{c: row.get(c) for c in cols}], columns=cols)
    proba = float(bundle["pipeline"].predict_proba(X)[0][1])
    label = int(proba >= 0.5)
    return {
        "delayed_probability": proba,
        "delayed_label": label,
        "model_version": bundle.get("version", "unknown"),
    }
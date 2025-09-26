from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime
import json

from backend.predictor.predictor import predict_flight_delay


@csrf_exempt
@require_POST
def predict_view(request):
    # 1) Parse JSON safely
    try:
        body = request.body.decode("utf-8") or "{}"
        data = json.loads(body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    # 2) Read & validate required fields
    flight_number = data.get("flight_number")
    flight_date   = data.get("flight_date")
    if not flight_number or not flight_date:
        return JsonResponse({"error": "Missing flight_number or flight_date"}, status=400)

    # 3) Validate date format
    try:
        datetime.strptime(flight_date, "%Y-%m-%d")
    except ValueError:
        return JsonResponse({"error": "flight_date must be YYYY-MM-DD"}, status=400)

    # 4) Call predictor and return result as-is
    try:
        result = predict_flight_delay(flight_number, flight_date)
        # predictor returns a dict on success, or {"error": "..."} on failure
        return JsonResponse(result, status=200 if "error" not in result else 400)
    except Exception as e:
        return JsonResponse({"error": f"Prediction failed: {e}"}, status=500)
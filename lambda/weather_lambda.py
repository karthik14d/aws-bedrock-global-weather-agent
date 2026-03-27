import json
import urllib.parse
import urllib.request

GEOCODING_BASE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_BASE = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm"
}

def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "weather-agent"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_param(event, name, default=None):
    for p in event.get("parameters", []):
        if p.get("name") == name:
            return p.get("value")
    return default

def lambda_handler(event, context):
    location = get_param(event, "location")
    unit = get_param(event, "unit", "F")  # default now Fahrenheit

    if not location:
        raise Exception("Location is required")

    geo_url = f"{GEOCODING_BASE}?name={urllib.parse.quote(location)}&count=1&language=en&format=json"
    geo = http_get_json(geo_url)

    if not geo.get("results"):
        raise Exception("Location not found")

    result = geo["results"][0]
    lat = result["latitude"]
    lon = result["longitude"]

    temp_unit = "fahrenheit" if unit == "F" else "celsius"
    wind_unit = "mph" if unit == "F" else "kmh"

    weather_url = (
        f"{FORECAST_BASE}?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m"
        f"&temperature_unit={temp_unit}"
        f"&wind_speed_unit={wind_unit}"
    )

    weather = http_get_json(weather_url)
    current = weather["current"]
    code = current.get("weather_code")

    body = {
        "location": result.get("name", location),
        "country": result.get("country"),
        "condition": WEATHER_CODE_MAP.get(code, str(code)),
        "temperature": current.get("temperature_2m"),
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind": current.get("wind_speed_10m"),
        "unit": unit
    }

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event["actionGroup"],
            "apiPath": event["apiPath"],
            "httpMethod": event["httpMethod"],
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body)
                }
            }
        }
    }
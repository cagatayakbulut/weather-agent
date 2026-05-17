import os
import requests

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_weather(lat, lon, name):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "tr"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "main" not in data:
        raise Exception(f"Hava durumu alınamadı: {data}")

    return {
        "name": name,
        "temp": data["main"]["temp"],
        "desc": data["weather"][0]["description"],
        "wind": data["wind"]["speed"]
    }

kadikoy = get_weather(40.9919, 29.0252, "Kadıköy")
sakarya = get_weather(40.7731, 30.3948, "Sakarya")
izmit = get_weather(40.7654, 29.9408, "İzmit / Kocaeli")

risk_words = ["yağmur", "sağanak", "kar", "fırtına", "dolu", "gök gürültülü

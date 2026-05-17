import os
import requests

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_weather(city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "tr"
    }

    response = requests.get(url, params=params)
    data = response.json()

    return {
        "temp": data["main"]["temp"],
        "desc": data["weather"][0]["description"]
    }

kadikoy = get_weather("Kadikoy,TR")
sakarya = get_weather("Sakarya,TR")

message = f"""
Günaydın Çağatay ☀️

Kadıköy:
{kadikoy['temp']:.0f}°C - {kadikoy['desc']}

Sakarya:
{sakarya['temp']:.0f}°C - {sakarya['desc']}

Şemsiye durumunu kontrol etmeyi unutma ☔
"""

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": message
}

requests.post(url, json=payload)
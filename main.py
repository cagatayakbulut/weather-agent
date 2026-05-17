import os
import requests
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

locations = [
    ("Kadıköy", 40.9919, 29.0252),
    ("Gebze", 40.8028, 29.4307),
    ("İzmit", 40.7654, 29.9408),
    ("Sapanca", 40.6913, 30.2674),
    ("Sakarya", 40.7731, 30.3948)
]

def get_weather(name, lat, lon):
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

    return {
        "name": name,
        "temp": round(data["main"]["temp"]),
        "desc": data["weather"][0]["description"],
        "wind": data["wind"]["speed"]
    }

def get_traffic():
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    params = {
        "origins": "Kadikoy",
        "destinations": "Sakarya",
        "departure_time": "now",
        "key": GOOGLE_MAPS_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    element = data["rows"][0]["elements"][0]

    normal_duration = element["duration"]["text"]
    traffic_duration = element["duration_in_traffic"]["text"]

    return normal_duration, traffic_duration

weather_data = []

for loc in locations:
    weather_data.append(get_weather(*loc))

normal_time, traffic_time = get_traffic()

weather_summary = ""

for item in weather_data:
    weather_summary += (
        f"{item['name']}: "
        f"{item['temp']}°C, "
        f"{item['desc']}, "
        f"rüzgar {item['wind']} m/s\n"
    )

prompt = f"""
Sen kişisel bir günlük sürüş ve kıyafet asistanısın.

Kullanıcı:
- Kadıköy'de yaşıyor
- Her gün araç ile Sakarya'ya gidiyor

Aşağıdaki hava durumuna göre:
- ne giymesi gerektiğini söyle
- şemsiye gerekip gerekmediğini söyle
- rota risklerini değerlendir
- sürüş tavsiyesi ver
- kısa ve doğal konuş

Hava Durumu:
{weather_summary}

Trafik:
Normal süre: {normal_time}
Anlık süre: {traffic_time}
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": "Kısa, doğal ve pratik konuş."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
)

ai_message = response.choices[0].message.content

telegram_url = (
    f"https://api.telegram.org/bot"
    f"{TELEGRAM_BOT_TOKEN}/sendMessage"
)

payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": ai_message
}

requests.post(telegram_url, json=payload)

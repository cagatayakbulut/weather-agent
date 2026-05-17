import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

locations = [
    ("Kadıköy", 40.9919, 29.0252),
    ("Gebze", 40.8028, 29.4307),
    ("İzmit", 40.7654, 29.9408),
    ("Sapanca", 40.6913, 30.2674),
    ("Sakarya", 40.7731, 30.3948)
]

def get_route():
    hour = datetime.now().hour

    if hour < 12:
        return {
            "route_text": "İstanbul → Sakarya işe gidiş",
            "origin": "Kadikoy",
            "destination": "Sakarya",
            "greeting": "Günaydın Çağatay ☀️"
        }
    else:
        return {
            "route_text": "Sakarya → İstanbul dönüş",
            "origin": "Sakarya",
            "destination": "Kadikoy",
            "greeting": "İyi akşamlar Çağatay 🌙"
        }

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

    if "main" not in data:
        raise Exception(f"Hava durumu alınamadı: {data}")

    return {
        "name": name,
        "temp": round(data["main"]["temp"]),
        "desc": data["weather"][0]["description"],
        "wind": data["wind"]["speed"]
    }

def get_traffic(origin, destination):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    params = {
        "origins": origin,
        "destinations": destination,
        "departure_time": "now",
        "key": GOOGLE_MAPS_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    element = data["rows"][0]["elements"][0]

    if element.get("status") != "OK":
        return "Alınamadı", "Alınamadı"

    normal_duration = element["duration"]["text"]
    traffic_duration = element.get("duration_in_traffic", {}).get("text", normal_duration)

    return normal_duration, traffic_duration

def send_telegram(message):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    response = requests.post(telegram_url, json=payload)
    print(response.text)

route = get_route()

weather_data = []
for loc in locations:
    weather_data.append(get_weather(*loc))

normal_time, traffic_time = get_traffic(route["origin"], route["destination"])

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
- Her gün araç ile Sakarya'ya gidip geliyor
- Sabah İstanbul'dan Sakarya'ya gider
- Akşam Sakarya'dan İstanbul'a döner
- Şu anki rota: {route['route_text']}

Aşağıdaki hava ve trafik durumuna göre:
- ne giymesi gerektiğini söyle
- şemsiye gerekip gerekmediğini söyle
- rota risklerini değerlendir
- yağmur, kar, dolu, rüzgar, sis gibi riskleri belirt
- sürüş tavsiyesi ver
- asla hız yapmayı veya daha hızlı gitmeyi önermeyin
- trafik iyi olsa bile hız sınırlarına uymayı söyle
- kısa, doğal ve pratik konuş

Hava Durumu:
{weather_summary}

Trafik:
Normal süre: {normal_time}
Anlık süre: {traffic_time}
"""

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Kısa, doğal, güvenli ve pratik konuş. Asla hız yapmayı önerme."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    ai_message = response.choices[0].message.content

except Exception as e:
    ai_message = f"""{route['greeting']}

{route['route_text']} 🚗

Hava durumu:
{weather_summary}

Trafik:
Normal süre: {normal_time}
Anlık süre: {traffic_time}

Not: AI yorumu alınamadı ama hava ve trafik bilgileri yukarıda.
"""

final_message = f"""{route['greeting']}

{route['route_text']} 🚗

{ai_message}
"""

send_telegram(final_message)

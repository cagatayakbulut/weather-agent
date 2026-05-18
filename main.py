import os
import requests
from openai import OpenAI

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

HOME_ADDRESS = os.getenv("HOME_ADDRESS", "Kadikoy, Istanbul")
WORK_ADDRESS = os.getenv("WORK_ADDRESS", "Sakarya")

client = OpenAI(api_key=OPENAI_API_KEY)

locations = [
    ("Kadıköy", 40.9919, 29.0252),
    ("Gebze", 40.8028, 29.4307),
    ("İzmit", 40.7654, 29.9408),
    ("Sapanca", 40.6913, 30.2674),
    ("Sakarya", 40.7731, 30.3948)
]

def get_route():
    route_mode = os.getenv("ROUTE_MODE", "morning")

    if route_mode == "morning":
        return {
            "route_text": "İstanbul → Sakarya işe gidiş",
            "origin": HOME_ADDRESS,
            "destination": WORK_ADDRESS,
            "greeting": "Günaydın Çağatay ☀️"
        }

    return {
        "route_text": "Sakarya → İstanbul dönüş",
        "origin": WORK_ADDRESS,
        "destination": HOME_ADDRESS,
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
        "language": "tr",
        "region": "tr",
        "key": GOOGLE_MAPS_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    try:
        element = data["rows"][0]["elements"][0]

        if element.get("status") != "OK":
            return "Alınamadı", "Alınamadı", "Alınamadı"

        normal_duration = element["duration"]["text"]
        traffic_duration = element.get("duration_in_traffic", {}).get(
            "text",
            normal_duration
        )

        normal_seconds = element["duration"]["value"]
        traffic_seconds = element.get("duration_in_traffic", {}).get(
            "value",
            normal_seconds
        )

        diff_minutes = round((traffic_seconds - normal_seconds) / 60)

        if diff_minutes > 0:
            traffic_difference = f"+{diff_minutes} dk"
        elif diff_minutes < 0:
            traffic_difference = f"-{abs(diff_minutes)} dk"
        else:
            traffic_difference = "0 dk"

        return normal_duration, traffic_duration, traffic_difference

    except Exception:
        return "Alınamadı", "Alınamadı", "Alınamadı"

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

normal_time, traffic_time, traffic_difference = get_traffic(
    route["origin"],
    route["destination"]
)

temperatures = [item["temp"] for item in weather_data]
min_temp = min(temperatures)
max_temp = max(temperatures)

weather_summary = ""
for item in weather_data:
    weather_summary += (
        f"{item['name']}: "
        f"{item['temp']}°C, "
        f"{item['desc']}, "
        f"rüzgar {item['wind']} m/s\n"
    )

prompt = f"""
Sen premium seviyede profesyonel sürüş, rota ve hava asistanısın.

Kullanıcı:
- Kadıköy'de yaşıyor
- Her gün araç ile Sakarya'ya gidip geliyor
- Sabah İstanbul → Sakarya
- Akşam Sakarya → İstanbul

Şu anki rota:
{route['route_text']}

Başlangıç:
{route['origin']}

Varış:
{route['destination']}

Hava verileri:
{weather_summary}

Sıcaklık:
En düşük: {min_temp}°C
En yüksek: {max_temp}°C

Trafik:
Normal süre: {normal_time}
Anlık süre: {traffic_time}
Fark: {traffic_difference}

AŞAĞIDAKİ FORMATA MUTLAKA UY:

Genel:
Rota boyunca sıcaklık [en düşük]-[en yüksek]°C aralığında. Hava durumunu net özetle.

Risk:
Yağmur, kar, dolu, sis veya rüzgar riski varsa belirt. Yoksa açıkça risk görünmediğini söyle.

Kıyafet:
Somut kıyafet önerisi ver.

Şemsiye:
Gerekli / gerekli değil kararını net söyle.

Trafik:
Normal süre: {normal_time}
Anlık süre: {traffic_time}
Fark: {traffic_difference}

Sürüş:
Güvenli sürüş tavsiyesi ver. Hız sınırlarına uyulmasını mutlaka belirt.

Kurallar:
- Yukarıdaki başlıkları aynen kullan
- Trafik süresini MUTLAKA belirt
- Sıcaklık aralığını MUTLAKA belirt
- Somut veri kullan
- Devrik cümle kurma
- Gereksiz samimiyet kullanma
- Asla hız yapmayı önerme
- Maksimum 12 satır yaz
"""

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
Sen profesyonel seviyede operasyonel sürüş asistanısın.

Kurallar:
- Başlık kullan
- Trafik süresini MUTLAKA belirt
- Sıcaklık aralığını MUTLAKA belirt
- Somut veri kullan
- Kısa ama metrik odaklı yaz
- Devrik cümle kullanma
- Gereksiz samimiyet kullanma
- Asla hız yapmayı önerme
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    ai_message = response.choices[0].message.content

except Exception:
    ai_message = f"""
Genel:
Rota boyunca sıcaklık {min_temp}°C - {max_temp}°C aralığında.

Risk:
Hava verileri aşağıdadır:
{weather_summary}

Kıyafet:
Sıcaklık aralığına göre ince ceket veya hafif mont tercih edilebilir.

Şemsiye:
Yağış görünüyorsa şemsiye alınmalıdır.

Trafik:
Normal süre: {normal_time}
Anlık süre: {traffic_time}
Fark: {traffic_difference}

Sürüş:
Hız sınırlarına uyarak ve takip mesafesini koruyarak ilerle.
"""

final_message = f"""{route['greeting']}

{route['route_text']} 🚗

{ai_message}
"""

send_telegram(final_message)

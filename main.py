import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
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

def should_run_today():
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    return now.weekday() < 5

def get_route():
    route_mode = os.getenv("ROUTE_MODE", "morning")

    if route_mode == "morning":
        return {
            "route_text": "İstanbul → Sakarya işe gidiş",
            "origin": HOME_ADDRESS,
            "destination": WORK_ADDRESS,
            "greeting": "Günaydın Çağatay ☀️",
            "target_time": "06:00"
        }

    return {
        "route_text": "Sakarya → İstanbul dönüş",
        "origin": WORK_ADDRESS,
        "destination": HOME_ADDRESS,
        "greeting": "İyi akşamlar Çağatay 🌙",
        "target_time": "17:15"
    }

def get_current_weather(name, lat, lon):
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "tr"
    }

    data = requests.get(url, params=params).json()

    if "main" not in data:
        raise Exception(f"Hava durumu alınamadı: {data}")

    return {
        "name": name,
        "temp": round(data["main"]["temp"]),
        "desc": data["weather"][0]["description"],
        "wind": data["wind"]["speed"],
        "visibility": data.get("visibility", 10000)
    }

def get_forecast_risk(name, lat, lon):
    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "tr"
    }

    data = requests.get(url, params=params).json()

    items = data.get("list", [])[:3]

    max_pop = 0
    risky_desc = []
    max_wind = 0

    for item in items:
        pop = item.get("pop", 0)
        max_pop = max(max_pop, pop)
        max_wind = max(max_wind, item.get("wind", {}).get("speed", 0))
        risky_desc.append(item["weather"][0]["description"])

    rain_probability = round(max_pop * 100)

    if rain_probability >= 60 or max_wind >= 8:
        risk_level = "Yüksek"
    elif rain_probability >= 30 or max_wind >= 5:
        risk_level = "Orta"
    else:
        risk_level = "Düşük"

    return {
        "name": name,
        "rain_probability": rain_probability,
        "max_wind": round(max_wind, 1),
        "risk_level": risk_level,
        "forecast_desc": ", ".join(set(risky_desc))
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

    data = requests.get(url, params=params).json()

    try:
        element = data["rows"][0]["elements"][0]

        if element.get("status") != "OK":
            return "Alınamadı", "Alınamadı", "Alınamadı", 0

        normal_duration = element["duration"]["text"]
        traffic_duration = element.get("duration_in_traffic", {}).get("text", normal_duration)

        normal_seconds = element["duration"]["value"]
        traffic_seconds = element.get("duration_in_traffic", {}).get("value", normal_seconds)

        diff_minutes = round((traffic_seconds - normal_seconds) / 60)

        if diff_minutes > 0:
            traffic_difference = f"+{diff_minutes} dk"
        elif diff_minutes < 0:
            traffic_difference = f"-{abs(diff_minutes)} dk"
        else:
            traffic_difference = "0 dk"

        return normal_duration, traffic_duration, traffic_difference, diff_minutes

    except Exception:
        return "Alınamadı", "Alınamadı", "Alınamadı", 0

def suggest_departure(route, diff_minutes, max_risk):
    base_time = route["target_time"]

    try:
        hour, minute = map(int, base_time.split(":"))
        base_dt = datetime.now(ZoneInfo("Europe/Istanbul")).replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

        extra = 0

        if diff_minutes >= 20:
            extra += 20
        elif diff_minutes >= 10:
            extra += 10

        if max_risk == "Yüksek":
            extra += 10

        suggested = base_dt - timedelta(minutes=extra)

        if extra == 0:
            return f"{base_time} çıkış saati uygun görünüyor."

        return f"{suggested.strftime('%H:%M')} civarı çıkmak daha rahat olabilir."

    except Exception:
        return "Çıkış saati önerisi hesaplanamadı."

def create_maps_link(origin, destination):
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={quote(origin)}"
        f"&destination={quote(destination)}"
        "&travelmode=driving"
    )

def send_telegram(message):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }

    response = requests.post(telegram_url, json=payload)
    print(response.text)

if not should_run_today():
    print("Hafta sonu olduğu için mesaj gönderilmedi.")
    exit()

route = get_route()

weather_data = []
forecast_data = []

for loc in locations:
    weather_data.append(get_current_weather(*loc))
    forecast_data.append(get_forecast_risk(*loc))

normal_time, traffic_time, traffic_difference, diff_minutes = get_traffic(
    route["origin"],
    route["destination"]
)

temperatures = [item["temp"] for item in weather_data]
min_temp = min(temperatures)
max_temp = max(temperatures)

risk_order = {"Düşük": 1, "Orta": 2, "Yüksek": 3}
max_risk = max(forecast_data, key=lambda x: risk_order[x["risk_level"]])["risk_level"]

departure_suggestion = suggest_departure(route, diff_minutes, max_risk)
maps_link = create_maps_link(route["origin"], route["destination"])

weather_summary = ""
for item in weather_data:
    weather_summary += (
        f"{item['name']}: {item['temp']}°C, "
        f"{item['desc']}, rüzgar {item['wind']} m/s\n"
    )

risk_summary = ""
for item in forecast_data:
    risk_summary += (
        f"{item['name']}: risk {item['risk_level']}, "
        f"yağış ihtimali %{item['rain_probability']}, "
        f"maks. rüzgar {item['max_wind']} m/s\n"
    )

prompt = f"""
Sen premium seviyede profesyonel sürüş, rota ve hava asistanısın.

Şu anki rota:
{route['route_text']}

Başlangıç:
{route['origin']}

Varış:
{route['destination']}

Hava verileri:
{weather_summary}

Risk verileri:
{risk_summary}

Sıcaklık:
En düşük: {min_temp}°C
En yüksek: {max_temp}°C

Trafik:
Normal süre: {normal_time}
Anlık süre: {traffic_time}
Fark: {traffic_difference}

Çıkış önerisi:
{departure_suggestion}

Cevabı MUTLAKA şu formatta yaz:

Genel:
Sıcaklık aralığını ve genel hava durumunu yaz.

Risk:
En kritik rota segmentini, yağış ihtimalini ve rüzgar riskini yaz.

Kıyafet:
Somut kıyafet önerisi ver.

Şemsiye:
Gerekli / gerekli değil kararını net ver.

Trafik:
Normal süre, anlık süre ve farkı mutlaka yaz.

Çıkış:
Çıkış saati önerisini yaz.

Sürüş:
Hız sınırlarına uyulmasını ve takip mesafesini belirt.

Kurallar:
- Devrik cümle kurma
- Gereksiz samimiyet kullanma
- Somut metrik kullan
- Asla hız yapmayı önerme
- Maksimum 14 satır yaz
"""

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Profesyonel, veri odaklı ve güvenli sürüş asistanısın. "
                    "Metrik kullan. Devrik cümle kurma. Asla hız yapmayı önerme."
                )
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
{risk_summary}

Kıyafet:
Sıcaklık aralığına göre ince ceket veya hafif mont tercih edilebilir.

Şemsiye:
Yağış ihtimali yüksek segment varsa şemsiye alınmalıdır.

Trafik:
Normal süre: {normal_time}
Anlık süre: {traffic_time}
Fark: {traffic_difference}

Çıkış:
{departure_suggestion}

Sürüş:
Hız sınırlarına uyarak ve takip mesafesini koruyarak ilerle.
"""

final_message = f"""{route['greeting']}

{route['route_text']} 🚗

{ai_message}

Rota:
{maps_link}
"""

send_telegram(final_message)

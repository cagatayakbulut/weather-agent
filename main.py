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

risk_words = ["yağmur", "sağanak", "kar", "fırtına", "dolu", "gök gürültülü"]
all_desc = f"{kadikoy['desc']} {sakarya['desc']} {izmit['desc']}".lower()
risk = any(word in all_desc for word in risk_words)

if min(kadikoy["temp"], sakarya["temp"], izmit["temp"]) <= 8:
    outfit = "Kalın mont iyi olur."
elif min(kadikoy["temp"], sakarya["temp"], izmit["temp"]) <= 15:
    outfit = "İnce mont veya ceket uygun olur."
else:
    outfit = "Hafif kıyafet yeterli; yanında ince bir üst bulundurabilirsin."

umbrella = "Şemsiye almanı öneririm. ☔" if risk else "Şemsiye şart görünmüyor."

drive = (
    "Rota uyarısı: İstanbul–Sakarya hattında yağış/kötü hava riski var. Takip mesafeni artır."
    if risk else
    "Rota uyarısı: Belirgin yağış riski görünmüyor."
)

message = f"""Günaydın Çağatay ☀️

Kadıköy:
{kadikoy['temp']:.0f}°C - {kadikoy['desc']} - rüzgar {kadikoy['wind']} m/s

İzmit / Kocaeli:
{izmit['temp']:.0f}°C - {izmit['desc']} - rüzgar {izmit['wind']} m/s

Sakarya:
{sakarya['temp']:.0f}°C - {sakarya['desc']} - rüzgar {sakarya['wind']} m/s

Bugün ne giyilir?
{outfit}

Şemsiye:
{umbrella}

{drive}
"""

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": message
}

response = requests.post(url, json=payload)
print(response.text)

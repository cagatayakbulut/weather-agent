import os
import requests

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
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

weather_data = []

for loc in locations:
    weather_data.append(get_weather(*loc))

all_desc = " ".join([x["desc"] for x in weather_data]).lower()

risk_words = [
    "yağmur",
    "sağanak",
    "kar",
    "fırtına",
    "gök gürültülü"
]

risk = any(word in all_desc for word in risk_words)

coldest = min([x["temp"] for x in weather_data])

if coldest <= 8:
    outfit = "Kalın mont önerilir."
elif coldest <= 15:
    outfit = "İnce mont veya ceket uygun olur."
else:
    outfit = "Hafif kıyafet yeterli görünüyor."

umbrella = (
    "Şemsiye almanı öneririm ☔"
    if risk else
    "Şemsiye gerekli görünmüyor."
)

if risk:
    traffic = "Yağış nedeniyle yol süresi uzayabilir. Takip mesafeni artır."
else:
    traffic = "Belirgin hava riski görünmüyor."

message = "Günaydın Çağatay ☀️\n\n"

for item in weather_data:
    message += (
        f"{item['name']}:\n"
        f"{item['temp']}°C - {item['desc']} "
        f"(rüzgar {item['wind']} m/s)\n\n"
    )

message += f"""Bugün ne giyilir?
{outfit}

Şemsiye:
{umbrella}

Rota değerlendirmesi:
{traffic}
"""

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": message
}

requests.post(telegram_url, json=payload)

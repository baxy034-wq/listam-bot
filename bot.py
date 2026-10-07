import os
import time
import json
import threading
import urllib.request
from flask import Flask

# Настройки Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

# Токены и параметры
TOKEN = "ТВОЙ_ТОКЕН_БОТА"
CHAT_ID = "ТВОЙ_CHAT_ID"
SLEEP_INTERVAL = 120  # 2 минуты для теста

def send_to_telegram(text):
    print("Пробую отправить сообщение в Telegram...")
    tele_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({'chat_id': CHAT_ID, 'text': text}).encode('utf-8')
    req = urllib.request.Request(tele_url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_text = response.read().decode('utf-8')
            print(f"Ответ Telegram: {response.status} -> {res_text}")
    except Exception as e:
        print(f"ОШИБКА Telegram: {e}")

def check_list_am():
    # Твой код проверки list.am
    pass

def bot_loop():
    print("Бот успешно запущен на Render!")
    send_to_telegram("🚀 ТЕСТ: Бот на Render работает и на связи!")
    while True:
        try:
            print("Проверяю list.am на наличие новых квартир...")
            check_list_am()
        except Exception as e:
            print(f"Ошибка в боте: {e}")
        print(f"Ожидаю {SLEEP_INTERVAL} секунд...")
        time.sleep(SLEEP_INTERVAL)

print("Инициализация запуска бота...")
t = threading.Thread(target=bot_loop, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

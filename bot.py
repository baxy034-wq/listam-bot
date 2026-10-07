import os
import time
import threading
import requests
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
    tele_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        res = requests.post(tele_url, json={'chat_id': CHAT_ID, 'text': text}, timeout=10)
        print(f"Ответ Telegram: {res.status_code} -> {res.text}")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def check_list_am():
    # Твой код проверки list.am
    pass

def bot_loop():
    print("Бот успешно запущен на Render!")
    send_to_telegram("🚀 ТЕСТ: Бот на Render работает и на связи!")
    while True:
        try:
            print("Проверяю list.am на наличие новых квартир...")
            check_list_am()  # или точное имя твоей функции
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

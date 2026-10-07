import os
import time
import json
import threading
import urllib.request
from flask import Flask
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

# Настройки Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

# === ВСТАВЬ СВОИ ДАННЫЕ СЮДА ===
TOKEN = "8385026193:AAEpR5RpPd-W6_OErkJmI4JdVaSTiI2wrQ8"
CHAT_ID = "-5549861681"
SLEEP_INTERVAL = 43200  # 12 часов (43200 секунд)

# Множество для хранения ID проверенных объявлений, чтобы не спамить дублями
SEEN_IDS = set()

def send_to_telegram(text):
    print("Отправляю сообщение в Telegram...")
    tele_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({'chat_id': CHAT_ID, 'text': text}).encode('utf-8')
    req = urllib.request.Request(tele_url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_text = response.read().decode('utf-8')
            print(f"Ответ Telegram: {response.status}")
    except Exception as e:
        print(f"ОШИБКА Telegram: {e}")

def check_list_am():
    print("Запрашиваю список квартир с list.am...")
    # Ссылка на квартиры от 85 кв.м в Ереване
    url = "https://www.list.am/ru/category/60?n=1&cmtype=1&type=1&po=2&s85=85"
    
    try:
        # Запрос с маскировкой под браузер Chrome
        response = cffi_requests.get(url, impersonate="chrome110", timeout=15)
        if response.status_code != 200:
            print(f"Ошибка загрузки страницы list.am: статус {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        # Находим все блоки объявлений
        items = soup.find_all('a', href=True)
        
        count_new = 0
        for item in items:
            href = item['href']
            # Проверяем, что это ссылка на конкретное объявление (/item/...)
            if '/item/' in href:
                item_id = href.split('/item/')[1].split('?')[0]
                
                if item_id not in SEEN_IDS:
                    SEEN_IDS.add(item_id)
                    count_new += 1
                    
                    full_url = f"https://www.list.am{href}"
                    # Берём текст объявления (заголовок/цена)
                    title = item.get_text(strip=True, separator=' ')
                    
                    # Формируем сообщение
                    msg = f"🏠 **Новое объявление на list.am!**\n\n{title}\n\n🔗 {full_url}"
                    send_to_telegram(msg)
                    time.sleep(1) # небольшая пауза между сообщениями
                    
        print(f"Проверка завершена. Найдено новых объявлений: {count_new}")

    except Exception as e:
        print(f"Ошибка при парсинге list.am: {e}")

def bot_loop():
    print("Бот успешно запущен на Render!")
    send_to_telegram("🚀 Бот запущен и начинает отслеживать квартиры на list.am!")
    while True:
        try:
            print("Начинаю цикл проверки...")
            check_list_am()
        except Exception as e:
            print(f"Ошибка в основном цикле бота: {e}")
        print(f"Следующая проверка через {SLEEP_INTERVAL} секунд...")
        time.sleep(SLEEP_INTERVAL)

# Запуск фонового потока
print("Инициализация запуска бота...")
t = threading.Thread(target=bot_loop, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

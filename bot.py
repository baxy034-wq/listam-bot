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
SLEEP_INTERVAL = 43200  # Проверка каждые 12 часов

# Набор для хранения ID уже отправленных объявлений
SEEN_IDS = set()
IS_FIRST_RUN = True  # Флаг первого запуска

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
    global IS_FIRST_RUN
    print("Запрашиваю список квартир с list.am по твоим критериям...")
    url = (
        "https://www.list.am/ru/category/60"
        "?n=11_12_13_14_15"
        "&cmtype=0"
        "&type=1"
        "&s90=90&s130=130"
        "&crc=1"
        "&p90000=90000&p140000=140000"
    )
    
    # Полная маскировка под реальный браузер Chrome на Windows
    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        response = cffi_requests.get(
            url, 
            headers=custom_headers, 
            impersonate="chrome120", 
            timeout=20, 
            verify=False
        )
        
        if response.status_code != 200:
            print(f"Ошибка загрузки страницы list.am: статус {response.status_code}")
            send_to_telegram(f"⚠️ Ошибка доступа к list.am: код {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('a', href=True)
        
        count_sent = 0
        total_found = 0
        
        for item in items:
            href = item['href']
            if '/item/' in href:
                total_found += 1
                item_id = href.split('/item/')[1].split('?')[0]
                
                # При первом запуске отправляем первые 5 объявлений для проверки
                if IS_FIRST_RUN:
                    if count_sent < 5:
                        SEEN_IDS.add(item_id)
                        full_url = f"https://www.list.am{href}"
                        title = item.get_text(strip=True, separator=' ')
                        msg = f"🏠 **[Тест выдачи] Актуальное объявление:**\n\n{title}\n\n🔗 {full_url}"
                        send_to_telegram(msg)
                        count_sent += 1
                        time.sleep(1)
                    else:
                        SEEN_IDS.add(item_id)
                else:
                    # При обычных циклах отправляем только НОВЫЕ
                    if item_id not in SEEN_IDS:
                        SEEN_IDS.add(item_id)
                        count_sent += 1
                        full_url = f"https://www.list.am{href}"
                        title = item.get_text(strip=True, separator=' ')
                        msg = f"🏠 **Новая квартира по фильтрам!**\n\n{title}\n\n🔗 {full_url}"
                        send_to_telegram(msg)
                        time.sleep(1)
                        
        print(f"Проверка завершена. Всего на странице: {total_found}, отправлено: {count_sent}")
        
        if IS_FIRST_RUN:
            IS_FIRST_RUN = False
            send_to_telegram(f"✅ Первичная проверка завершена! Всего подходящих квартир на сайте сейчас: {total_found}. Выслал 5 штук для примера.")
        elif count_sent == 0:
            send_to_telegram(f"🔍 Проверка завершена. Всего квартир по фильтрам: {total_found}. Новых объявлений за последнее время не появлялось.")

    except Exception as e:
        print(f"Ошибка при парсинге list.am: {e}")
        send_to_telegram(f"⚠️ Ошибка при парсинге: {e}")

def bot_loop():
    print("Бот успешно запущен на Render!")
    send_to_telegram("🚀 Перезапуск бота с обходом блокировки...")
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

import time
import re
import os
import threading
from bs4 import BeautifulSoup
from curl_cffi import requests
from flask import Flask

# --- Flask сервер для Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

TOKEN = '8385026193:AAEpR5RpPd-W6_OErkJmI4JdVaSTiI2wrQ8'
URL = 'https://www.list.am/category/60?n=2%2C3%2C5%2C8%2C11&sname=&s=&cmtype=&crc=1&price1=60000&price2=140000&sq_price1=85&sq_price2=&_a5=&_a39=&_a40=&_a85=&_a73=&_a3_1=&_a3_2=&_a4=3%2C4&_a4%5B%5D=3&_a4%5B%5D=4&_a37=&_a36=&_a11_1=&_a11_2=&_a47=&_a78=&_a38=&_a82=&_a77=&s27=9&e27=16'
CHAT_ID = '-5549861681'

MIN_AREA = 85
MIN_FLOORS = 9
MAX_FLOORS = 16
DB_FILE = 'seen.txt'
SLEEP_INTERVAL = 10800  # 3 часа

def load_seen_apartments():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen_apartment(item_id):
    with open(DB_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{item_id}\n")

def parse_apartment_details(item_url):
    try:
        response = requests.get(item_url, impersonate="chrome")
        if response.status_code == 200:
            inner_soup = BeautifulSoup(response.text, 'html.parser')
            area = None
            total_floors = None
            
            attrs = inner_soup.find_all('div', class_='attr') or inner_soup.find_all('div', class_='c')
            for attr in attrs:
                text = attr.get_text()
                if any(k in text.lower() for k in ['общая площадь', 'մակերես', 'total area']):
                    match = re.search(r'(\d+)', text)
                    if match:
                        area = int(match.group(1))
                        
                if any(k in text.lower() for k in ['этажей в доме', 'этажность', 'շենքի հարկերը', 'building storeys', 'floors']):
                    match = re.search(r'(\d+)', text)
                    if match:
                        total_floors = int(match.group(1))

            if area is None:
                text_inside = inner_soup.get_text()
                area_match = re.search(r'(?:общая площадь|площадь|մակերես)\s*[:\ \-]*\s*(\d+)', text_inside, re.IGNORECASE)
                if area_match:
                    area = int(area_match.group(1))

            return area, total_floors
    except Exception as e:
        print(f"Ошибка при чтении карточки {item_url}: {e}")
    return None, None

def check_list_am():
    print("Проверяю list.am на наличие новых квартир...")
    seen_apartments = load_seen_apartments()
    
    try:
        response = requests.get(URL, impersonate="chrome")
        print(f"Статус ответа от сайта: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('a', href=True)
        
        counter = 0
        for item in items:
            href = item['href']
            if '/item/' in href:
                item_id = href.split('/')[-1]
                
                if item_id not in seen_apartments:
                    full_url = f"https://www.list.am{href}"
                    area, total_floors = parse_apartment_details(full_url)
                    
                    if area is not None and area < MIN_AREA:
                        save_seen_apartment(item_id)
                        seen_apartments.add(item_id)
                        continue

                    if total_floors is not None and (total_floors < MIN_FLOORS or total_floors > MAX_FLOORS):
                        save_seen_apartment(item_id)
                        seen_apartments.add(item_id)
                        continue

                    title_text = "Новое объявление"
                    price_text = "Цена не указана"
                    
                    l_div = item.find('div', class_='l')
                    p_div = item.find('div', class_='p')
                    
                    if l_div:
                        title_text = l_div.text.strip()
                    elif item.text:
                        title_text = item.text.strip().split('\n')[0]
                        
                    if p_div:
                        price_text = p_div.text.strip()
                    
                    floors_str = f" ({total_floors} эт. дом)" if total_floors else ""
                    
                    message = (
                        f"💰 **{price_text}**\n"
                        f"📍 {title_text}\n"
                        f"📐 Точная площадь: {area if area else 'Уточняйте'} кв.м.{floors_str}\n\n"
                        f"🔗 Ссылка: {full_url}"
                    )
                    
                    send_to_telegram(message)
                    save_seen_apartment(item_id)
                    seen_apartments.add(item_id)
                    counter += 1
                    
        print(f"Проверка завершена. Отправлено новых объявлений: {counter}")
    except Exception as e:
        print(f"Ошибка при проверке: {e}")

def send_to_telegram(text):
    tele_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    import requests as regular_requests
    regular_requests.post(tele_url, json={'chat_id': CHAT_ID, 'text': text}, timeout=10)

def bot_loop():
    print("Бот успешно запущен на Render!")
    while True:
        check_list_am()
        print(f"Ожидаю {SLEEP_INTERVAL} секунд...")
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    # Запуск логики бота в отдельном потоке
    threading.Thread(target=bot_loop, daemon=True).start()
    # Запуск веб-сервера на порту, который просит Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

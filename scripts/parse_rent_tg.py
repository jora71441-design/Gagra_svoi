import urllib.request
import re
import html
import json
import os

URL = "https://t.me/s/arenda_abkhazia_svoi"

def fetch_html():
    req = urllib.request.Request(
        URL, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode('utf-8')

def parse_posts(raw_html):
    message_blocks = re.findall(r'<div class="tgme_widget_message_wrap.*?(?=<div class="tgme_widget_message_wrap|\Z)', raw_html, re.S)
    items = []

    for block in message_blocks:
        link_match = re.search(r'class="tgme_widget_message_date"\s+href="([^"]+)"', block)
        post_link = link_match.group(1) if link_match else "https://t.me/arenda_abkhazia_svoi"

        text_match = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
        if not text_match:
            continue
        
        raw_text = text_match.group(1)
        clean_text = html.unescape(re.sub(r'<br\s*/?>', '\n', raw_text))
        clean_text = re.sub(r'<[^>]+>', '', clean_text).strip()
        if not clean_text or len(clean_text) < 25:
            continue

        text_lower = clean_text.lower()

        # 1. Отсекаем мемы, юмор и объявления администратора
        stop_words = [
            "пятничное настроение", "посмеяться", "юмор", "мем", "анекдот",
            "если вы ищете жильё", "если вы ищите жилье", "пишите мне в личку",
            "помогу с оформлением", "правила канала", "подписывайтесь"
        ]
        if any(sw in text_lower for sw in stop_words):
            continue

        # Маркеры реального объявления о сдаче
        listing_markers = [
            "сдаёт", "сдает", "сдаю", "аренд", "квартир", "студи",
            "комнат", "коттедж", "таунхаус", "номер", "этаж"
        ]
        if not any(m in text_lower for m in listing_markers):
            continue

        # 2. Извлечение CDN-фотографий Telegram
        photo_urls = re.findall(r"background-image:url\('([^']+)'\)", block)
        photos = list(dict.fromkeys(photo_urls))[:5]

        # 3. Извлечение цены
        price_match = re.search(r'(\d[\d\s]{2,}\d|\d{2,})\s*(?:₽|руб|тыс|\.000)', clean_text, re.I)
        price = price_match.group(0).strip() if price_match else "Цена по запросу"
        if "₽" not in price and "руб" not in price and price != "Цена по запросу":
            price += " ₽ / мес"

        # 4. Привязка к 9 официальным городам
        city = "Гагра"
        city_variants = {
            "Цандрипш": ["цандрипш", "цандрыпш", "гантиади"],
            "Пицунда": ["пицунд", "литфонд", "рыбзавод", "лдзаа"],
            "Гудаута": ["гудаут", "бамбора"],
            "Новый Афон": ["новый афон", "афон"],
            "Сухум": ["сухум", "синоп", "турбаза", "маяк", "келасур"],
            "Очамчыра": ["очамчыр", "очамчир"],
            "Ткуарчал": ["ткуарчал", "ткварчел"],
            "Гал": ["гал ", "гал,", "гал.", "г. гал", " гал"]
        }
        for target_city, patterns in city_variants.items():
            if any(p in text_lower for p in patterns):
                city = target_city
                break

        # 5. Район
        district = "Центр"
        for d in ["Кемпинг", "Новая Гагра", "Старая Гагра", "Павильон", "Абаата", "Рынок", "Ущелье", "Маяк"]:
            if d.lower() in text_lower:
                district = d
                break

        # 6. Определение: Квартира vs Дом (с защитой от 'рядом' и 'под домом')
        is_flat = bool(re.search(r'\b(?:квартир\w*|студи\w*|\d+[- ]*к\b|\d+[- ]*комн\w*|апартамент\w*)', text_lower))
        is_house = bool(re.search(r'\b(?:коттедж\w*|таунхаус\w*|частн\w+\s+дом\w*|отдельн\w+\s+дом\w*|этаж\s+(?:в\s+)?доме?|дача|дачн\w*|дом\s+под\s+ключ|сда[её]тся\s+дом|домик\w*)\b', text_lower))

        if is_house and not is_flat:
            category = "house"
        else:
            category = "flat"

        # 7. Определение срока
        is_season = any(w in text_lower for w in ["до мая", "до июня", "до лета", "помесячн", "на 1 мес", "на 2 мес", "на месяц", "на зим"])
        is_year = any(w in text_lower for w in ["на год", "круглый год", "круглогодичн", "без выселения", "без поднятия", "на длительн"])

        if is_season and not is_year:
            period = "season"
            badge = "⏳ До лета"
        else:
            period = "year"
            badge = "🔒 На год+"

        lines = [l.strip() for l in clean_text.split('\n') if l.strip()]
        title = lines[0][:50] if lines else "Аренда жилья"

        items.append({
            "id": 0,
            "title": title,
            "price": price,
            "city": city,
            "district": district,
            "category": category, # 'flat' | 'house'
            "period": period,     # 'year' | 'season'
            "type": category,
            "badge": badge,
            "desc": clean_text[:220] + "..." if len(clean_text) > 220 else clean_text,
            "photos": photos,
            "status": "Свободно к заселению",
            "tg_link": post_link
        })

    items.reverse()
    for idx, item in enumerate(items, 1):
        item["id"] = idx

    return items

def main():
    os.makedirs("data", exist_ok=True)
    html_data = fetch_html()
    data = parse_posts(html_data)
    
    with open("data/rent.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Готово! Спарсено объявлений: {len(data)}")

if __name__ == "__main__":
    main()

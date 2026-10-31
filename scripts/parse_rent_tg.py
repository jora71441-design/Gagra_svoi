import urllib.request
import re
import html
import json
import os

URL = "https://t.me/s/arenda_abkhazia_svoi"
SUPABASE_URL = "https://yzbochrahmuhvryinajr.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl6Ym9jaHJhaG11aHZyeWluYWpyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMyNzYyODcsImV4cCI6MjEwODg1MjI4N30.dTjerKbrcLuTEr5xPKXkR43Df4ECaGA-ztCrGD_SO-A"

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

        # Фильтр юмора и админских объявлений
        stop_words = [
            "пятничное настроение", "посмеяться", "юмор", "мем", "анекдот",
            "если вы ищете жильё", "если вы ищите жилье", "пишите мне в личку",
            "помогу с оформлением", "правила канала", "подписывайтесь"
        ]
        if any(sw in text_lower for sw in stop_words):
            continue

        listing_markers = [
            "сдаёт", "сдает", "сдаю", "аренд", "квартир", "студи",
            "комнат", "коттедж", "таунхаус", "номер", "этаж", "домик"
        ]
        if not any(m in text_lower for m in listing_markers):
            continue

        photo_urls = re.findall(r"background-image:url\('([^']+)'\)", block)
        photos = list(dict.fromkeys(photo_urls))[:5]

        price_match = re.search(r'(\d[\d\s]{2,}\d|\d{2,})\s*(?:₽|руб|тыс|\.000)', clean_text, re.I)
        price = price_match.group(0).strip() if price_match else "Цена по запросу"
        if "₽" not in price and "руб" not in price and price != "Цена по запросу":
            price += " ₽ / мес"

        # Город
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

        # Район
        district = "Центр"
        for d in ["Кемпинг", "Новая Гагра", "Старая Гагра", "Павильон", "Абаата", "Рынок", "Ущелье", "Маяк"]:
            if d.lower() in text_lower:
                district = d
                break

        # Категория: Квартира vs Дом
        is_house = bool(re.search(r'\b(?:домик\w*|коттедж\w*|таунхаус\w*|частн\w+\s+дом\w*|отдельн\w+\s+дом\w*|этаж\s+(?:в\s+)?доме?|дача|дачн\w*|дом\s+под\s+ключ|сда[её]тся\s+(?:отдельный\s+)?дом\w*)\b', text_lower))
        is_flat = bool(re.search(r'\b(?:квартир\w*|студи\w*|\d+[- ]*к\b|\d+[- ]*комн\w*|апартамент\w*)', text_lower))

        category = "house" if (is_house and not is_flat) else "flat"

        # Срок аренды
        is_season = any(w in text_lower for w in ["до мая", "до июня", "до лета", "помесячн", "на 1 мес", "на 2 мес", "на месяц", "на зим"])
        is_year = any(w in text_lower for w in ["на год", "круглый год", "круглогодичн", "без выселения", "без поднятия", "на длительн"])

        period = "season" if (is_season and not is_year) else "year"
        badge = "⏳ До лета" if period == "season" else "🔒 На год+"

        lines = [l.strip() for l in clean_text.split('\n') if l.strip()]
        title = lines[0][:50] if lines else "Аренда жилья"

        items.append({
            "title": title,
            "price": price,
            "city": city,
            "district": district,
            "category": category,
            "period": period,
            "type": category,
            "badge": badge,
            "desc": clean_text[:250] + "..." if len(clean_text) > 250 else clean_text,
            "photos": photos,
            "status": "Свободно к заселению",
            "tg_link": post_link,
            "is_approved": True,
            "is_active": True
        })

    items.reverse()
    return items

def sync_to_supabase(items):
    if not items:
        return
    
    # Отправляем пачкой с директивой игнорировать дубли по tg_link
    url = f"{SUPABASE_URL}/rest/v1/rent?on_conflict=tg_link"
    data_bytes = json.dumps(items).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=ignore-duplicates'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Синхронизация с Supabase выполнена успешно!")
    except Exception as e:
        print(f"Ошибка при синхронизации с Supabase: {e}")

def main():
    os.makedirs("data", exist_ok=True)
    html_data = fetch_html()
    data = parse_posts(html_data)

    # 1. Запись в локальный json (как резерв)
    for idx, item in enumerate(data, 1):
        item["id"] = idx
    with open("data/rent.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 2. Синхронизация с Supabase (для кабинета модератора)
    # Удаляем числовые id перед отправкой в БД, чтобы Supabase использовал свои автоинкрементные id
    db_items = []
    for it in data:
        row = dict(it)
        row.pop("id", None)
        db_items.append(row)
        
    sync_to_supabase(db_items)
    print(f"Готово! Обработано объектов: {len(data)}")

if __name__ == "__main__":
    main()

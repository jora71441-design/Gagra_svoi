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
    # Разбиваем поток страницы на отдельные блоки постов
    message_blocks = re.findall(r'<div class="tgme_widget_message_wrap.*?(?=<div class="tgme_widget_message_wrap|\Z)', raw_html, re.S)
    items = []

    for block in message_blocks:
        # Извлекаем прямую ссылку на оригинальный пост в канале
        link_match = re.search(r'class="tgme_widget_message_date"\s+href="([^"]+)"', block)
        post_link = link_match.group(1) if link_match else "https://t.me/arenda_abkhazia_svoi"

        # Извлекаем текст сообщения
        text_match = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
        if not text_match:
            continue
        
        # Очищаем HTML-разметку, переносы строк и спецсимволы
        raw_text = text_match.group(1)
        clean_text = html.unescape(re.sub(r'<br\s*/?>', '\n', raw_text))
        clean_text = re.sub(r'<[^>]+>', '', clean_text).strip()
        if not clean_text or len(clean_text) < 15:
            continue

        # Извлекаем прямые CDN-ссылки на фото из стилей Telegram
        photo_urls = re.findall(r"background-image:url\('([^']+)'\)", block)
        # Убираем дубликаты с сохранением порядка и ограничиваем до 5 штук для слайдера
        photos = list(dict.fromkeys(photo_urls))[:5]

        # Определяем стоимость аренды
        price_match = re.search(r'(\d[\d\s]{2,}\d|\d{2,})\s*(?:₽|руб|тыс|\.000)', clean_text, re.I)
        price = price_match.group(0).strip() if price_match else "Цена по запросу"
        if "₽" not in price and "руб" not in price and price != "Цена по запросу":
            price += " ₽ / мес"

        # Привязка к 9 официальным городам Абхазии
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
            if any(p in clean_text.lower() for p in patterns):
                city = target_city
                break

        # Определение района
        district = "Центр"
        for d in ["Кемпинг", "Новая Гагра", "Старая Гагра", "Павильон", "Абаата", "Рынок", "Ущелье", "Маяк"]:
            if d.lower() in clean_text.lower():
                district = d
                break

        # Определение срока и типа жилья для фильтрации
        text_lower = clean_text.lower()
        if any(w in text_lower for w in ["дом", "коттедж", "этаж в доме", "таунхаус", "дача", "частный дом"]):
            item_type = "house"
            badge = "🏡 Дом / Коттедж"
        elif any(w in text_lower for w in ["до мая", "до июня", "до лета", "помесячн", "на месяц", "на 1 мес", "на 2 мес"]):
            item_type = "season"
            badge = "⏳ До лета"
        else:
            item_type = "year"
            badge = "🔒 На год+"

        # Заголовок объекта (первая строка описания)
        lines = [l.strip() for l in clean_text.split('\n') if l.strip()]
        title = lines[0][:50] if lines else "Аренда жилья"

        items.append({
            "id": 0,
            "title": title,
            "price": price,
            "city": city,
            "district": district,
            "type": item_type,
            "badge": badge,
            "desc": clean_text[:220] + "..." if len(clean_text) > 220 else clean_text,
            "photos": photos,
            "status": "Свободно к заселению",
            "tg_link": post_link
        })

    # Свежие посты из канала должны быть сверху списка на сайте
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

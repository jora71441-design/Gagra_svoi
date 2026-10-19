import re
import json
import os

# Категории и сопоставление
CAT_ALIASES = {
    "СТРОИТЕЛЬСТВО": ("construction", "Строительство и каркас"),
    "КАРКАС": ("construction", "Строительство и каркас"),
    "ОТДЕЛКА": ("finish", "Отделка и ремонт"),
    "ИНТЕРЬЕР": ("finish", "Отделка и ремонт"),
    "ИНЖЕНЕРНЫЕ": ("engineering", "Сантехника и электрика"),
    "ОКНА": ("doors", "Окна и двери"),
    "ДВЕРИ": ("doors", "Окна и двери"),
    "РЕМОНТ И ОБСЛУЖИВАНИЕ": ("appliances", "Бытовая техника"),
    "БЫТОВАЯ ТЕХНИКА": ("appliances", "Бытовая техника"),
    "АВТО": ("auto", "Авто и транспорт"),
    "КРАСОТА": ("beauty", "Красота и здоровье"),
    "ЗДОРОВЬЕ": ("beauty", "Красота и здоровье"),
    "ДОМ": ("home", "Дом, дача, еда"),
    "ЕДА": ("home", "Дом, дача, еда"),
    "ПОЛЕЗНЫЕ МЕСТА": ("places", "Полезные места и сервисы"),
    "ЮВЕЛИР": ("places", "Полезные места и сервисы")
}

def clean_phone(p: str) -> str:
    p = p.strip()
    digits = re.sub(r'\D', '', p)
    if digits.startswith('89') and len(digits) == 11:
        digits = '7' + digits[1:]
    elif len(digits) == 10 and digits.startswith('9'):
        digits = '7' + digits
    elif len(digits) == 7: # Местный абхазский городской
        return "+7940" + digits
    if len(digits) == 11:
        return "+" + digits
    return p

def detect_category_by_text(text: str):
    t = text.lower()
    if any(k in t for k in ["окн", "двер", "москит", "стекл", "замок"]):
        return "doors", "Окна и двери"
    if any(k in t for k in ["стирал", "холодильн", "кондиционер", "техник", "плит", "духовк", "бытов"]):
        return "appliances", "Бытовая техника"
    if any(k in t for k in ["обои", "потолок", "плитк", "кафел", "паркет", "маляр", "штукатур", "столяр", "мебел"]):
        return "finish", "Отделка и ремонт"
    if any(k in t for k in ["сантехн", "электрик", "отоплен", "водоснабжен", "кран", "котел", "сифон"]):
        return "engineering", "Сантехника и электрика"
    if any(k in t for k in ["стройк", "сварк", "сварщ", "альпинист", "навес", "мусор"]):
        return "construction", "Строительство и каркас"
    if any(k in t for k in ["авто", "акпп", "диагност", "машин", "велосипед"]):
        return "auto", "Авто и транспорт"
    if any(k in t for k in ["массаж", "макияж", "лор", "врач", "психолог", "терапевт", "художник", "кормлени"]):
        return "beauty", "Красота и здоровье"
    if any(k in t for k in ["покос", "еда", "штор", "торт", "аджик", "доставк"]):
        return "home", "Дом, дача, еда"
    return "places", "Полезные места и сервисы"

def parse_chat():
    chat_file = "_chat.txt"
    if not os.path.exists(chat_file):
        print("Файл _chat.txt не найден")
        return

    with open(chat_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Удаляем скрытые юникод-символы WhatsApp
    content = re.sub(r'[\u200e\u200f\u202a-\u202e\u202f\ufeff]', '', content)

    # Делим на сообщения
    raw_messages = re.split(r'\n(?=\d{1,2}\.\d{1,2}\.\d{2,4})', content)

    masters = {}
    master_counter = 1

    # Регулярка телефона
    phone_pattern = r'(?:\+?7|8)?[\s\-]?(?:\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\b[79]\d{2}[\s\-]?\d{2}[\s\-]?\d{2}\b'

    for msg in raw_messages:
        lines = [line.strip() for line in msg.split('\n') if line.strip()]
        if not lines:
            continue

        header = lines[0]
        # Пропускаем системные сообщения (добавления списков номеров, выходы)
        if any(skip in msg for skip in ["покинул(-а)", "присоединился", "добавил(-а) контакт", "Сообщения и звонки защищены", "ОПРОС:"]):
            continue

        # Ветка 1: Дайджест Ринаты "ПОЛЕЗНЫЕ КОНТАКТЫ ГАГРА"
        if "ПОЛЕЗНЫЕ КОНТАКТЫ ГАГРА" in msg:
            current_cat_key = "construction"
            current_cat_title = "Строительство и каркас"

            for line in lines[1:]:
                # Определение категории по заголовкам дайджеста
                upper_line = line.upper()
                for alias, (ck, ct) in CAT_ALIASES.items():
                    if alias in upper_line:
                        current_cat_key = ck
                        current_cat_title = ct
                        break

                # Строка мастера: ✅⭐ +7 940 926-40-99, Федор - стройка...
                if any(line.startswith(prefix) for prefix in ["✅", "⭐", "📍", "•", "-"]):
                    # Поиск телефона
                    ph_match = re.search(phone_pattern, line)
                    if not ph_match:
                        continue
                    
                    raw_phone = ph_match.group(0)
                    phone = clean_phone(raw_phone)
                    if len(re.sub(r'\D', '', phone)) < 7:
                        continue

                    is_starred = "⭐" in line
                    
                    # Очищаем строку от маркеров и телефона
                    info = line
                    for ch in ["✅", "⭐", "📍", "•"]:
                        info = info.replace(ch, "")
                    info = info.replace(raw_phone, "").strip(" ,-–")

                    # Разделяем имя и услугу
                    if " - " in info:
                        parts = info.split(" - ", 1)
                        name = parts[0].strip(" ,")
                        service = parts[1].strip()
                    elif "," in info:
                        parts = info.split(",", 1)
                        name = parts[0].strip()
                        service = parts[1].strip()
                    else:
                        name = info if info else "Специалист"
                        service = f"Услуги по направлению: {current_cat_title}"

                    if not name or len(name) > 30:
                        name = current_cat_title

                    masters[phone] = {
                        "id": master_counter,
                        "name": name,
                        "category": current_cat_key,
                        "category_title": current_cat_title,
                        "service": service[:140],
                        "phone": phone,
                        "recommended_by": "Подборка чата (Гагра)",
                        "verified": True,
                        "starred": is_starred
                    }
                    master_counter += 1
            continue

        # Ветка 2: Индивидуальные объявления с хэштегами #услуга, #еда, #рекомендую
        text_lower = msg.lower()
        if any(tag in text_lower for tag in ["#услуга", "#рекомендую", "#еда", "сварочные, работы", "доставка посылок", "поклейкой обоев"]):
            if "#ищу" in text_lower and not "#услуга" in text_lower:
                continue

            ph_match = re.search(phone_pattern, msg)
            if not ph_match:
                continue

            phone = clean_phone(ph_match.group(0))
            if len(re.sub(r'\D', '', phone)) < 7:
                continue

            cat_key, cat_title = detect_category_by_text(msg)
            
            # Попытка вытащить имя
            name = "Специалист"
            for line in lines[1:]:
                for kw in ["меня зовут", "мастер", "я ", "аскар", "вячеслав", "владимир", "сергей", "михаил"]:
                    if kw in line.lower() and len(line) < 35:
                        name = line.replace("#", "").strip()
                        break

            # Очищенный текст услуги
            clean_body = re.sub(r'https?://\S+', '', msg)
            clean_body = re.sub(phone_pattern, '', clean_body)
            clean_body = " ".join([l for l in clean_body.split('\n')[1:] if not l.startswith('#') and len(l) > 4])
            if not clean_body:
                clean_body = f"Услуги по направлению: {cat_title}"

            if phone not in masters:
                masters[phone] = {
                    "id": master_counter,
                    "name": name[:30],
                    "category": cat_key,
                    "category_title": cat_title,
                    "service": clean_body[:140].strip(),
                    "phone": phone,
                    "recommended_by": "Участник чата",
                    "verified": True,
                    "starred": "#рекомендую" in text_lower
                }
                master_counter += 1

    masters_list = list(masters.values())
    # Сортируем: сначала рекомендуемые (со звездочкой)
    masters_list.sort(key=lambda x: not x.get("starred", False))

    os.makedirs("data", exist_ok=True)
    with open("data/masters.json", "w", encoding="utf-8") as out:
        json.dump(masters_list, out, ensure_ascii=False, indent=2)

    print(f"Успешно обработано: {len(masters_list)} специалистов.")

if __name__ == "__main__":
    parse_chat()

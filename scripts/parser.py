import re
import json
import os

CATEGORIES_MAP = {
    "doors": {
        "title": "Окна и двери",
        "keywords": ["двер", "окн", "стекл", "петл", "замок", "наличник"]
    },
    "appliances": {
        "title": "Бытовая техника",
        "keywords": ["стирал", "холодильн", "кондиционер", "плит", "посудомой", "техник", "бойлер", "котел"]
    },
    "finish": {
        "title": "Отделочные работы",
        "keywords": ["обои", "потолок", "маляр", "штукатур", "плитк", "шпаклев", "покраск", "ремонт квартир"]
    },
    "plumbing": {
        "title": "Сантехника",
        "keywords": ["сантехник", "кран", "труб", "унитаз", "протечк", "смесител", "засор", "канализаци"]
    },
    "electric": {
        "title": "Электрика",
        "keywords": ["электрик", "проводк", "свет", "розетк", "щиток", "автомат", "люстр"]
    },
    "auto": {
        "title": "Автоуслуги",
        "keywords": ["авто", "эвакуатор", "машин", "колес", "шиномонтаж", "аккумулятор", "мотор"]
    }
}

# Регулярка строки WhatsApp с очищенным форматом
MSG_REGEX = re.compile(
    r'^(\d{1,2}\.\d{1,2}\.\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*([^:]+?):\s*(.*)$'
)

def find_abkhaz_phones(text: str):
    # Ищем последовательности с 940 и последующими 7 цифрами
    pattern = r'(?:\+?7|8)?[\s\-\(\.]*940[\s\-\)\.]*(?:\d[\s\-\.]*){7}'
    matches = re.findall(pattern, text)
    cleaned = []
    for m in matches:
        digits = re.sub(r'\D', '', m)
        if digits.startswith('8940'):
            digits = '7940' + digits[4:]
        elif digits.startswith('940'):
            digits = '7940' + digits[3:]
        if len(digits) == 11 and digits.startswith('7940'):
            cleaned.append('+' + digits)
    return cleaned

def detect_category(text: str):
    text_lower = text.lower()
    for cat_key, cat_data in CATEGORIES_MAP.items():
        if any(kw in text_lower for kw in cat_data["keywords"]):
            return cat_key, cat_data["title"]
    return "other", "Разное и прочие услуги"

def extract_name(text: str, sender: str) -> str:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines:
        if any(w in line.lower() for w in ["номер", "попробуй", "звони", "мастер"]):
            continue
        words = line.split()
        if 1 <= len(words) <= 3 and not re.search(r'\d{5,}', line):
            return line.replace("~", "").strip()
    return f"Специалист ({sender})"

def run():
    chat_file = "_chat.txt"
    if not os.path.exists(chat_file):
        print("Файл _chat.txt не найден.")
        return

    with open(chat_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # ВАЖНО: Удаляем все невидимые служебные Unicode-метки WhatsApp
    content = re.sub(r'[\u200e\u200f\u202a-\u202e\u202f\ufeff]', '', content)

    # Делим по датам сообщений
    raw_messages = re.split(r'\n(?=\d{1,2}\.\d{1,2}\.\d{2,4})', content)

    masters = []
    seen_phones = set()
    master_id = 1

    for msg in raw_messages:
        match = MSG_REGEX.match(msg.strip())
        if not match:
            continue

        _, _, sender, text = match.groups()
        phones = find_abkhaz_phones(text)
        if not phones:
            continue

        for phone in phones:
            if phone in seen_phones:
                continue

            seen_phones.add(phone)
            cat_key, cat_title = detect_category(text)
            name = extract_name(text, sender)

            service_desc = re.sub(r'(?:\+?7|8)?[\s\-\(\.]*940[\s\-\)\.]*(?:\d[\s\-\.]*){7}', '', text)
            service_desc = service_desc.replace('\n', ' ').strip()
            if not service_desc or len(service_desc) < 5:
                service_desc = f"Услуги по направлению: {cat_title}"

            masters.append({
                "id": master_id,
                "name": name,
                "category": cat_key,
                "category_title": cat_title,
                "service": service_desc[:120],
                "phone": phone,
                "recommended_by": sender.strip(),
                "verified": True
            })
            master_id += 1

    os.makedirs("data", exist_ok=True)
    with open("data/masters.json", "w", encoding="utf-8") as out:
        json.dump(masters, out, ensure_ascii=False, indent=2)

    print(f"Готово! Собрано мастеров: {len(masters)}")

if __name__ == "__main__":
    run()

import re
import json
import os

# Справочник макро- и подкатегорий (синхронизирован с js/app.js)
TAXONOMY = {
    "appliances": {
        "title": "🧺 Техника",
        "subs": {
            "washers": "Стиральные машины",
            "fridges": "Холодильники",
            "aircon": "Кондиционеры",
            "gadgets": "Телефоны и ТВ",
            "small_appliances": "Мелкая техника"
        }
    },
    "engineering": {
        "title": "🔧 Сантехника / Свет",
        "subs": {
            "plumbing": "Сантехника и вода",
            "heating": "Котлы и отопление",
            "electric": "Электрика и свет",
            "underfloor": "Тёплые полы"
        }
    },
    "finish": {
        "title": "🎨 Отделка / Ремонт",
        "subs": {
            "wallpaper": "Обои и покраска",
            "ceilings": "Натяжные потолки",
            "tiles": "Плитка и кафель",
            "flooring": "Ламинат и полы",
            "doors": "Окна и двери",
            "furniture": "Мебель и сборка"
        }
    },
    "construction": {
        "title": "🏗 Стройка / Сварка",
        "subs": {
            "building": "Стройка под ключ",
            "welding": "Сварка и навесы",
            "climbing": "Пром. альпинизм",
            "waste": "Вывоз мусора"
        }
    },
    "auto": {
        "title": "🚗 Авто / Доставка",
        "subs": {
            "autodiag": "Диагностика и автоэлектрик",
            "gearbox": "Ремонт АКПП",
            "bike": "Велосипеды",
            "delivery": "Доставка и грузы"
        }
    },
    "home_care": {
        "title": "🧹 Дом и быт",
        "subs": {
            "cleaning": "Уборка и клининг",
            "garden": "Покос и сад",
            "sewing": "Шторы и шитьё"
        }
    },
    "lifestyle": {
        "title": "🌿 Здоровье и красота",
        "subs": {
            "medical": "Врачи (все категории)",
            "massage": "Массаж и тело",
            "psychology": "Психология и душа",
            "beauty": "Красота и уход"
        }
    },
    "education": {
        "title": "🎓 Обучение и хобби",
        "subs": {
            "tutors": "Репетиторы и курсы",
            "hobby": "Хобби и саморазвитие"
        }
    },
    "events": {
        "title": "🎉 Праздники",
        "subs": {
            "photo_video": "Фото и видео",
            "decor": "Декор и оформление",
            "org": "Организация и ведущие"
        }
    },
    "places": {
        "title": "📍 Полезные места",
        "subs": {
            "business": "Торговля / Бизнес",
            "other": "Разное"
        }
    }
}

# Семантическая база синонимов для умного поиска
SYNONYMS = {
    "стирал": ["стиралка", "стиральная машина", "автомат", "подшипник", "слив", "не сливает", "насос"],
    "холодильн": ["холодос", "морозилка", "компрессор", "фреон", "не морозит"],
    "кондиционер": ["сплит", "климат", "кондей", "дозаправка", "чистка кондиционера"],
    "обои": ["поклейка обоев", "шпаклевка", "шпатлевка", "маляр", "покраска стен"],
    "двер": ["замки", "ручки", "мдф", "петли", "наличники", "установка дверей", "межкомнатные двери"],
    "окн": ["стеклопакет", "москитка", "москитные сетки", "регулировка окон", "пластиковые окна"],
    "сантехн": ["кран", "сифон", "смеситель", "трубы", "пайка", "засор", "канализация", "протечка", "унитаз", "бойлер", "котел", "отопление"],
    "электрик": ["проводка", "люстра", "свет", "розетка", "выключатель", "автомат", "щиток", "теплый пол"],
    "свар": ["сварщик", "каркас", "навес", "козырек", "перила", "решетки", "ворота", "калитка"],
    "альпинист": ["высотные работы", "фасад", "герметизация", "швы"],
    "потол": ["натяжные потолки", "люстры", "слив воды"],
    "плитк": ["кафель", "керамогранит", "санузел", "фартук"],
    "паркет": ["ламинат", "кварцвинил", "полы", "плинтус"],
    "мебел": ["сборка мебели", "кухня", "шкаф", "купе"],
    "авто": ["акпп", "диагностика", "электрик", "коробка", "мотор"],
    "уборк": ["клининг", "генеральная уборка", "мытье окон", "химчистка"],
    "массаж": ["спина", "шея", "лечебный", "выезд", "лимфодренаж", "остеопат"],
    "лор": ["ухо", "горло", "нос", "слух", "врач", "доктор"],
    "психолог": ["терапия", "консультация", "психотерапевт", "коуч"],
    "репетитор": ["английский", "математика", "курсы", "уроки", "обучение", "логопед"],
    "фотограф": ["фотосессия", "видеосъемка", "видеограф", "свадьба", "праздник"]
}

def clean_phone(p: str) -> str:
    digits = re.sub(r'\D', '', p)
    if digits.startswith('89') and len(digits) == 11:
        digits = '7' + digits[1:]
    elif len(digits) == 10 and digits.startswith('9'):
        digits = '7' + digits
    elif len(digits) == 7:
        return "+7940" + digits
    if len(digits) == 11:
        return "+" + digits
    return p

def classify_service(text: str):
    t = text.lower()

    # 1. Техника (проверяем без конфликтного корня "плит")
    if any(k in t for k in ["стирал"]):
        return "appliances", "washers"
    if any(k in t for k in ["холодильн", "морозил"]):
        return "appliances", "fridges"
    if any(k in t for k in ["кондиционер", "сплит"]):
        return "appliances", "aircon"
    if any(k in t for k in ["телефон", "смартфон", "компьютер", "ноутбук", "телевизор", "proxima", "fabmobile", "t-mobile"]):
        return "appliances", "gadgets"
    if any(k in t for k in ["духовк", "варочн", "электроплит", "газов", "микроволнов", "пылесос", "кофемашин", "бытов"]):
        return "appliances", "small_appliances"

    # 2. Сантехника и свет
    if any(k in t for k in ["теплый пол", "теплые полы", "тёплый пол", "тёплые полы"]):
        return "engineering", "underfloor"
    if any(k in t for k in ["котел", "котёл", "котлы", "отоплен", "бойлер"]):
        return "engineering", "heating"
    if any(k in t for k in ["электрик", "проводк", "свет", "люстр", "розетк"]):
        return "engineering", "electric"
    if any(k in t for k in ["сантехн", "кран", "сифон", "водоснабжен", "канализаци"]):
        return "engineering", "plumbing"

    # 3. Отделка и ремонт
    if any(k in t for k in ["плитк", "кафел", "керамогранит"]):
        return "finish", "tiles"
    if any(k in t for k in ["обои", "маляр", "покраск", "шпаклев", "шпатлев", "штукатур"]):
        return "finish", "wallpaper"
    if any(k in t for k in ["потолок", "потолки", "skyline"]):
        return "finish", "ceilings"
    if any(k in t for k in ["паркет", "ламинат", "кварцвинил", "пол "]):
        return "finish", "flooring"
    if any(k in t for k in ["двер", "окн", "москит", "стекл", "замок"]):
        return "finish", "doors"
    if any(k in t for k in ["мебел", "сборк", "столяр", "дерев"]):
        return "finish", "furniture"

    # 4. Стройка и сварка
    if any(k in t for k in ["альпинист", "высотн"]):
        return "construction", "climbing"
    if any(k in t for k in ["свар", "навес", "кованы", "козырек", "ворот"]):
        return "construction", "welding"
    if any(k in t for k in ["мусор"]):
        return "construction", "waste"
    if any(k in t for k in ["стройк", "каркас", "фундамент", "кровл", "крыш"]):
        return "construction", "building"

    # 5. Авто / Доставка
    if any(k in t for k in ["акпп", "коробк"]):
        return "auto", "gearbox"
    if any(k in t for k in ["автоэлектрик", "диагност", "автосервис", "шиномонтаж"]):
        return "auto", "autodiag"
    if any(k in t for k in ["велосипед", "вело"]):
        return "auto", "bike"
    if any(k in t for k in ["доставк", "посылок", "груз", "перевоз", "эвакуатор", "такси", "трансфер"]):
        return "auto", "delivery"

    # 6. Дом и быт
    if any(k in t for k in ["уборк", "клининг", "химчистк", "мытье окон", "мытьё окон"]):
        return "home_care", "cleaning"
    if any(k in t for k in ["покос", "трав", "сад", "огород", "спил дерев", "обрезк"]):
        return "home_care", "garden"
    if any(k in t for k in ["штор", "пошив", "шить", "ателье", "одежд"]):
        return "home_care", "sewing"

    # 7. Здоровье и красота
    if any(k in t for k in ["психолог", "психотерап", "коуч", "астролог", "таро"]):
        return "lifestyle", "psychology"
    if any(k in t for k in ["массаж", "остеопат", "мануальн", "реабилитолог"]):
        return "lifestyle", "massage"
    if any(k in t for k in ["лор", "врач", "терапевт", "педиатр", "стоматолог", "медсестр", "укол", "капельниц", "анализ", "кормлени"]):
        return "lifestyle", "medical"
    if any(k in t for k in ["макияж", "перманент", "маникюр", "педикюр", "брови", "ресниц", "парикмахер", "стрижк", "косметолог", "эпиляц", "шугаринг", "волос"]):
        return "lifestyle", "beauty"

    # 8. Обучение и хобби
    if any(k in t for k in ["репетитор", "английск", "математик", "логопед", "курс", "обучен", "подготовк", "школа", "урок"]):
        return "education", "tutors"
    if any(k in t for k in ["йог", "фитнес", "тренер", "танц", "рисован", "художник", "арт", "музык", "вокал", "хобби", "мастер-класс"]):
        return "education", "hobby"

    # 9. Праздники
    if any(k in t for k in ["фотограф", "видеограф", "фотосесси", "видеосъемк", "видеосъёмк"]):
        return "events", "photo_video"
    if any(k in t for k in ["декор", "шары", "шарик", "флорист", "букет", "оформлен", "торт", "кондитер"]):
        return "events", "decor"
    if any(k in t for k in ["ведущ", "аниматор", "праздник", "диджей", "dj", "тамада"]):
        return "events", "org"

    # 10. Полезные места
    if any(k in t for k in ["магазин", "кафе", "ресторан", "пекарн", "база", "склад", "аджик", "сыр", "мёд", "мед", "рынок", "сервис"]):
        return "places", "business"

    return "places", "other"

def generate_keywords(text: str, cat_title: str, sub_title: str) -> list:
    tokens = set()
    t = text.lower()
    words = re.findall(r'\b[а-яa-z]{3,}\b', t)
    tokens.update(words)
    tokens.add(cat_title.lower())
    tokens.add(sub_title.lower())

    for root, syn_list in SYNONYMS.items():
        if root in t:
            tokens.update(syn_list)
    return list(tokens)

def parse_chat():
    chat_file = "_chat.txt"
    if not os.path.exists(chat_file):
        print("Файл _chat.txt не найден")
        return

    with open(chat_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    content = re.sub(r'[\u200e\u200f\u202a-\u202e\u202f\ufeff]', '', content)
    raw_messages = re.split(r'\n(?=\d{1,2}\.\d{1,2}\.\d{2,4})', content)

    masters = {}
    master_counter = 1
    phone_pattern = r'(?:\+?7|8)?[\s\-]?(?:\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\b[79]\d{2}[\s\-]?\d{2}[\s\-]?\d{2}\b'

    # Черный список тестовых / фейковых номеров и маркеров
    STOP_PHONES = {"+79405555555", "+79400000000", "+79409999999"}

    for msg in raw_messages:
        # Полная фильтрация обучающих сообщений, опросов и правил
        if any(stop_word in msg.lower() for stop_word in [
            "как пользоваться чатом", "нужен фотограф на свадьбу", "пример:",
            "покинул(-а)", "присоединился", "добавил(-а) контакт",
            "сообщения и звонки защищены", "опрос:", "правила чата"
        ]):
            continue

        lines = [line.strip() for line in msg.split('\n') if line.strip()]
        if not lines:
            continue

        # Ветка 1: Еженедельные дайджесты Ринаты
        if "ПОЛЕЗНЫЕ КОНТАКТЫ ГАГРА" in msg:
            for line in lines[1:]:
                if any(line.startswith(prefix) for prefix in ["✅", "⭐", "📍", "•", "-"]):
                    ph_match = re.search(phone_pattern, line)
                    if not ph_match:
                        continue

                    phone = clean_phone(ph_match.group(0))
                    if phone in STOP_PHONES or len(re.sub(r'\D', '', phone)) < 7:
                        continue

                    is_starred = "⭐" in line
                    info = line
                    for ch in ["✅", "⭐", "📍", "•"]:
                        info = info.replace(ch, "")
                    info = info.replace(ph_match.group(0), "").strip(" ,-–")

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
                        service = "Услуги специалистов в Гагре"

                    cat_key, sub_key = classify_service(name + " " + service)
                    cat_title = TAXONOMY[cat_key]["title"]
                    sub_title = TAXONOMY[cat_key]["subs"][sub_key]
                    keywords = generate_keywords(name + " " + service, cat_title, sub_title)

                    # Проверяем, является ли мастер лидером недели
                    is_leader = "Владимир" in name or "самым полезным участником" in msg

                    masters[phone] = {
                        "id": master_counter,
                        "name": name[:30],
                        "category": cat_key,
                        "category_title": cat_title,
                        "subcategory": sub_key,
                        "subcategory_title": sub_title,
                        "service": service[:140],
                        "phone": phone,
                        "recommended_by": "Подборка чата (Гагра)",
                        "verified": True,
                        "starred": is_starred,
                        "is_leader": is_leader,
                        "keywords": keywords
                    }
                    master_counter += 1
            continue

        # Ветка 2: Индивидуальные посты участников
        text_lower = msg.lower()
        if any(tag in text_lower for tag in ["#услуга", "#рекомендую", "#еда", "сварочные, работы", "доставка посылок", "поклейкой обоев"]):
            if "#ищу" in text_lower and "#услуга" not in text_lower:
                continue

            ph_match = re.search(phone_pattern, msg)
            if not ph_match:
                continue

            phone = clean_phone(ph_match.group(0))
            if phone in STOP_PHONES or len(re.sub(r'\D', '', phone)) < 7:
                continue

            name = "Специалист"
            for line in lines[1:]:
                for kw in ["меня зовут", "мастер", "аскар", "вячеслав", "владимир", "сергей", "михаил"]:
                    if kw in line.lower() and len(line) < 35:
                        name = line.replace("#", "").strip()
                        break

            clean_body = re.sub(r'https?://\S+', '', msg)
            clean_body = re.sub(phone_pattern, '', clean_body)
            clean_body = " ".join([l for l in clean_body.split('\n')[1:] if not l.startswith('#') and len(l) > 4])
            if not clean_body:
                clean_body = "Услуги специалистов в Гагре"

            cat_key, sub_key = classify_service(name + " " + clean_body)
            cat_title = TAXONOMY[cat_key]["title"]
            sub_title = TAXONOMY[cat_key]["subs"][sub_key]
            keywords = generate_keywords(name + " " + clean_body, cat_title, sub_title)

            if phone not in masters:
                masters[phone] = {
                    "id": master_counter,
                    "name": name[:30],
                    "category": cat_key,
                    "category_title": cat_title,
                    "subcategory": sub_key,
                    "subcategory_title": sub_title,
                    "service": clean_body[:140].strip(),
                    "phone": phone,
                    "recommended_by": "Участник чата",
                    "verified": True,
                    "starred": "#рекомендую" in text_lower,
                    "keywords": keywords
                }
                master_counter += 1

    masters_list = list(masters.values())
    masters_list.sort(key=lambda x: not x.get("starred", False))

    os.makedirs("data", exist_ok=True)
    with open("data/masters.json", "w", encoding="utf-8") as out:
        json.dump(masters_list, out, ensure_ascii=False, indent=2)

    print(f"Готово! Очищено от спама и структурировано {len(masters_list)} специалистов.")

if __name__ == "__main__":
    parse_chat()

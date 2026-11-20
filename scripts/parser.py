import re
import json
import os
import glob
import quopri

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
    "стирал": ["стиралка", "стиральная машина", "автомат", "подшипник", "слив", "насос"],
    "холодильн": ["холодос", "морозилка", "компрессор", "фреон"],
    "кондиционер": ["сплит", "климат", "кондей", "дозаправка", "чистка кондиционера"],
    "триколор": ["трикалор", "тарелка", "приставка", "телевизор", "тв"],
    "обои": ["поклейка обоев", "шпаклевка", "шпатлевка", "маляр", "малярка", "венецианка", "покраска"],
    "двер": ["замки", "слесарь", "ручки", "мдф", "петли", "наличники", "откосы"],
    "окн": ["стеклопакет", "москитка", "жалюзи", "рольставни", "регулировка окон"],
    "сантехн": ["кран", "сифон", "смеситель", "трубы", "засор", "унитаз", "бойлер", "котел", "отопление", "ванна"],
    "электрик": ["проводка", "люстра", "свет", "розетка", "автомат", "щиток", "теплый пол", "видеонаблюдение"],
    "свар": ["сварщик", "каркас", "навес", "козырек", "перила", "ворота", "калитка", "качели"],
    "альпинист": ["высотные работы", "фасад", "герметизация", "швы"],
    "потол": ["натяжные потолки", "потолочник", "паталог"],
    "плитк": ["кафель", "керамогранит", "санузел", "фартук", "брусчатка"],
    "паркет": ["ламинат", "кварцвинил", "полы", "стяжка", "плинтус"],
    "мебел": ["сборка мебели", "кухня", "шкаф", "перешив", "реставрация", "столяр"],
    "авто": ["акпп", "диагностика", "электрик", "коробка", "шиномонтаж"],
    "уборк": ["клининг", "мойка ковров", "химчистка"],
    "массаж": ["спина", "шея", "лечебный", "тайский", "спа", "остеопат"],
    "врач": ["стоматолог", "зубной", "лор", "доктор", "анализы", "гемотест"],
    "психолог": ["терапия", "консультация", "психотерапевт", "коуч"],
    "репетитор": ["автошкола", "курсы", "уроки", "обучение", "пианино", "фортепиано"],
    "фотограф": ["фотосессия", "видеосъемка", "видеограф", "ведущая", "декоратор", "праздник"]
}

STOP_PHONES = {"+79405555555", "+79400000000", "+79409999999"}
PHONE_PATTERN = r'(?:\+?7|8)?[\s\-]?(?:\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\b[79]\d{2}[\s\-]?\d{2}[\s\-]?\d{2}\b'

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

    # 1. Техника
    if any(k in t for k in ["стирал", "стирмаш"]):
        return "appliances", "washers"
    if any(k in t for k in ["холодильн", "морозил"]):
        return "appliances", "fridges"
    if any(k in t for k in ["кондиционер", "сплит", "кондей"]):
        return "appliances", "aircon"
    if any(k in t for k in ["телефон", "смартфон", "компьютер", "ноутбук", "оргтехн", "принтер", "телевизор", "триколор", "трикалор", "приставк", "видеонаблюден", "камер", "proxima", "fabmobile", "t-mobile"]):
        return "appliances", "gadgets"
    if any(k in t for k in ["духовк", "варочн", "электроплит", "газов", "микроволнов", "пылесос", "кофемашин", "швейн", "dayson", "бытов", "3d", "3д"]):
        return "appliances", "small_appliances"

    # 2. Сантехника и свет
    if any(k in t for k in ["теплый пол", "теплые полы", "тёплый пол", "тёплые полы", "теплым полам", "тёплым полам"]):
        return "engineering", "underfloor"
    if any(k in t for k in ["котел", "котёл", "котлы", "отоплен", "бойлер", "насос"]):
        return "engineering", "heating"
    if any(k in t for k in ["электрик", "электромонтаж", "проводк", "свет", "люстр", "розетк"]):
        return "engineering", "electric"
    if any(k in t for k in ["сантехн", "кран", "сифон", "водоснабжен", "канализаци", "ванн"]):
        return "engineering", "plumbing"

    # 3. Отделка и ремонт
    if any(k in t for k in ["плитк", "кафел", "керамогранит", "брусчатк"]):
        return "finish", "tiles"
    if any(k in t for k in ["обои", "маляр", "покраск", "шпаклев", "шпатлев", "штукатур", "венецианк", "барельеф", "откос", "дизайнер интер"]):
        return "finish", "wallpaper"
    if any(k in t for k in ["потолок", "потолки", "потолочн", "паталог", "skyline"]):
        return "finish", "ceilings"
    if any(k in t for k in ["паркет", "ламинат", "кварцвинил", "стяжк", "пол "]):
        return "finish", "flooring"
    if any(k in t for k in ["двер", "окн", "москит", "стекл", "замок", "замк", "слесар", "жалюз", "рольставн"]):
        return "finish", "doors"
    if any(k in t for k in ["мебел", "сборк", "столяр", "дерев", "перешив"]):
        return "finish", "furniture"

    # 4. Стройка и сварка
    if any(k in t for k in ["альпинист", "высотн"]):
        return "construction", "climbing"
    if any(k in t for k in ["свар", "навес", "кованы", "козырек", "ворот", "качел"]):
        return "construction", "welding"
    if any(k in t for k in ["мусор"]):
        return "construction", "waste"
    if any(k in t for k in ["стройк", "постройк", "каркас", "фундамент", "кровл", "крыш", "гидроизоляц", "камин", "барбекю", "дагестанск", "дикого камня"]):
        return "construction", "building"

    # 5. Авто / Доставка
    if any(k in t for k in ["акпп", "коробк"]):
        return "auto", "gearbox"
    if any(k in t for k in ["автоэлектрик", "диагност", "автосервис", "шиномонтаж"]):
        return "auto", "autodiag"
    if any(k in t for k in ["велосипед", "вело", "самокат"]):
        return "auto", "bike"
    if any(k in t for k in ["доставк", "курьер", "посылок", "груз", "перевоз", "газел", "минивен", "спецтехник", "автокран", "экскаватор", "эвакуатор", "такси", "трансфер"]):
        return "auto", "delivery"

    # 6. Дом и быт
    if any(k in t for k in ["уборк", "клининг", "химчистк", "мойка ковр", "мытье окон", "мытьё окон"]):
        return "home_care", "cleaning"
    if any(k in t for k in ["покос", "трав", "сад", "участк", "огород", "спил дерев", "обрезк", "фазенд"]):
        return "home_care", "garden"
    if any(k in t for k in ["штор", "пошив", "шить", "швея", "портн", "ателье", "одежд", "мехов"]):
        return "home_care", "sewing"

    # 7. Здоровье и красота
    if any(k in t for k in ["психолог", "психотерап", "коуч", "целител", "ясновидящ", "ченнелер"]):
        return "lifestyle", "psychology"
    if any(k in t for k in ["массаж", "остеопат", "мануальн", "реабилитолог", "спа"]):
        return "lifestyle", "massage"
    if any(k in t for k in ["лор", "врач", "терапевт", "педиатр", "стоматолог", "зубн", "медсестр", "гемотест", "анализ", "кормлени"]):
        return "lifestyle", "medical"
    if any(k in t for k in ["макияж", "перманент", "маникюр", "педикюр", "брови", "ресниц", "парикмахер", "барбершоп", "стрижк", "косметолог", "эпиляц", "шугаринг", "волос"]):
        return "lifestyle", "beauty"

    # 8. Обучение и хобби
    if any(k in t for k in ["репетитор", "английск", "математик", "логопед", "курс", "обучен", "школа", "автошкола", "урок", "кинолог"]):
        return "education", "tutors"
    if any(k in t for k in ["йог", "фитнес", "тренер", "танц", "рисован", "художник", "арт", "музык", "фортепиано", "пианино", "хобби", "студи", "рыбалк"]):
        return "education", "hobby"

    # 9. Праздники
    if any(k in t for k in ["фотограф", "видеограф", "фотосесси", "видеосъемк", "видеосъёмк"]):
        return "events", "photo_video"
    if any(k in t for k in ["декор", "шары", "флорист", "букет", "оформлен", "торт", "кондитер", "выпечк", "фуршет"]):
        return "events", "decor"
    if any(k in t for k in ["ведущ", "церемониймейстер", "аниматор", "праздник", "диджей", "выездное кафе", "палаток"]):
        return "events", "org"

    # 10. Полезные места
    if any(k in t for k in ["магазин", "зоотовар", "грумер", "кафе", "ресторан", "шаурм", "пекарн", "база", "металлобаз", "склад", "аджик", "полуфабрикат", "рынок", "сервис", "фирма", "юридич", "открытие ип", "прокат", "ювелир", "колеровк", "ксерокоп", "market"]):
        return "places", "business"

    return "places", "other"

def generate_keywords(text: str, cat_title: str, sub_title: str) -> list:
    tokens = set()
    t = text.lower()
    words = re.findall(r'\b[а-яa-z0-9]{3,}\b', t)
    tokens.update(words)
    tokens.add(cat_title.lower())
    tokens.add(sub_title.lower())

    for root, syn_list in SYNONYMS.items():
        if root in t:
            tokens.update(syn_list)
    return list(tokens)

def add_master(masters: dict, counter: int, phone: str, name: str, service: str, recommended_by: str, starred: bool = False, is_leader: bool = False, overwrite: bool = False) -> int:
    phone = clean_phone(phone)
    if phone in STOP_PHONES or len(re.sub(r'\D', '', phone)) < 7:
        return counter

    if phone in masters and not overwrite:
        # Если уже есть в базе, просто обновим статус рекомендации при необходимости
        if starred:
            masters[phone]["starred"] = True
        return counter

    name = re.sub(r'[*_~`]', '', name).strip(" ,-–—:")
    service = re.sub(r'[*_~`]', '', service).strip(" ,-–—:")
    if not name or name.lower() in ["без имени", "(без имени)"]:
        name = "Специалист"
    if not service:
        service = "Услуги специалистов в Гагре"

    cat_key, sub_key = classify_service(f"{name} {service}")
    cat_title = TAXONOMY[cat_key]["title"]
    sub_title = TAXONOMY[cat_key]["subs"][sub_key]
    keywords = generate_keywords(f"{name} {service}", cat_title, sub_title)

    masters[phone] = {
        "id": masters[phone]["id"] if phone in masters else counter,
        "name": name[:35],
        "category": cat_key,
        "category_title": cat_title,
        "subcategory": sub_key,
        "subcategory_title": sub_title,
        "service": service[:160],
        "phone": phone,
        "recommended_by": recommended_by,
        "verified": True,
        "starred": starred or (masters[phone]["starred"] if phone in masters else False),
        "is_leader": is_leader,
        "keywords": keywords
    }
    return counter if phone in masters else counter + 1

def decode_vcard_value(value: str, params: str) -> str:
    if "QUOTED-PRINTABLE" in params.upper():
        try:
            return quopri.decodestring(value).decode("utf-8", errors="ignore").strip()
        except Exception:
            pass
    return value.replace("\\,", ",").replace("\\;", ";").replace("\\n", " ").strip()

def parse_vcf_files(masters: dict, master_counter: int) -> int:
    vcf_files = glob.glob("data/vcf/*.vcf") + glob.glob("*.vcf")
    if not vcf_files:
        return master_counter

    before_count = len(masters)
    for filepath in vcf_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                raw = f.read()
        except Exception:
            continue

        raw = re.sub(r'=\r?\n', '', raw)
        raw = re.sub(r'\r?\n[ \t]', '', raw)

        cards = re.findall(r'BEGIN:VCARD(.*?)END:VCARD', raw, re.S | re.I)
        for card in cards:
            fn = org = title = note = ""
            phones = []

            for line in card.splitlines():
                line = line.strip()
                if ":" not in line:
                    continue
                key_part, val = line.split(":", 1)
                key_upper = key_part.split(";")[0].upper()

                if key_upper == "FN":
                    fn = decode_vcard_value(val, key_part)
                elif key_upper == "ORG":
                    org = decode_vcard_value(val, key_part).replace(";", " ").strip()
                elif key_upper == "TITLE":
                    title = decode_vcard_value(val, key_part)
                elif key_upper == "NOTE":
                    note = decode_vcard_value(val, key_part)
                elif key_upper == "TEL":
                    ph = clean_phone(val)
                    if ph not in STOP_PHONES and len(re.sub(r'\D', '', ph)) >= 7:
                        phones.append(ph)

            if not phones:
                continue

            name = fn or org or os.path.splitext(os.path.basename(filepath))[0]
            extra_info = " ".join(x for x in [title, org, note] if x and x != name).strip()
            master_counter = add_master(
                masters, master_counter, phones[0], name,
                extra_info if extra_info else name,
                "Контакт из чата (VCF)", overwrite=False
            )

    print(f"Из .vcf добавлено новых контактов: {len(masters) - before_count}")
    return master_counter

def parse_digest_lines(lines: list, masters: dict, master_counter: int, is_leader_msg: bool) -> int:
    """Разбирает как однострочные (✅ +7..., Имя - услуга), так и многострочные (✅ Имя - услуга \\n 📞 +7...) дайджесты."""
    i = 0
    while i < len(lines):
        line = lines[i]
        if any(line.startswith(p) for p in ["✅", "⭐", "📍", "•"]):
            is_starred = "⭐" in line
            ph_match = re.search(PHONE_PATTERN, line)
            info = line

            # Если в строке нет телефона — смотрим следующие 1–2 строки (формат 📞 +7... и 📍 адрес)
            extra_addr = ""
            if not ph_match:
                j = i + 1
                while j < len(lines) and j <= i + 3:
                    nxt = lines[j]
                    if nxt.startswith("✅") or nxt.startswith("⭐"):
                        break
                    if nxt.startswith("📍") and not re.search(PHONE_PATTERN, nxt):
                        extra_addr = nxt.replace("📍", "").strip()
                    else:
                        m = re.search(PHONE_PATTERN, nxt)
                        if m and not ph_match:
                            ph_match = m
                    j += 1

            if ph_match:
                phone = ph_match.group(0)
                for ch in ["✅", "⭐", "📍", "•", "📞"]:
                    info = info.replace(ch, "")
                info = info.replace(phone, "").strip(" ,-–—")

                # Разделяем имя и описание услуги
                sep_match = re.split(r'\s+[-–—]\s+', info, maxsplit=1)
                if len(sep_match) == 2:
                    name, service = sep_match[0], sep_match[1]
                elif "," in info:
                    parts = info.split(",", 1)
                    name, service = parts[0], parts[1]
                else:
                    name, service = info, info

                if extra_addr:
                    service = f"{service} ({extra_addr})"

                is_leader = "Владимир" in name or is_leader_msg
                master_counter = add_master(
                    masters, master_counter, phone, name, service,
                    "Подборка чата (Гагра)", starred=is_starred, is_leader=is_leader, overwrite=True
                )
        i += 1
    return master_counter

def parse_chat():
    chat_file = "_chat.txt"
    masters = {}
    master_counter = 1

    if os.path.exists(chat_file):
        with open(chat_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = re.sub(r'[\u200e\u200f\u202a-\u202e\u202f\ufeff]', '', content)
        raw_messages = re.split(r'\n(?=\d{1,2}\.\d{1,2}\.\d{2,4})', content)

        digest_markers = [
            "полезные контакты", "новые мастера за неделю",
            "новых полезных контактов", "новые контакты за неделю"
        ]
        request_stop_words = [
            "#ищу", "# ищу", "нужен ", "нужна ", "нужны ", "ищу ", "подскажите",
            "кто знает", "есть мастер", "есть кто", "требуется помощница",
            "как пользоваться чатом", "пример:", "опрос:", "правила чата",
            "покинул(-а)", "присоединился", "добавил(-а) контакт",
            "сообщения и звонки защищены", "не распространять его номер"
        ]

        for msg in raw_messages:
            msg_lower = msg.lower()
            lines = [line.strip() for line in msg.split('\n') if line.strip()]
            if not lines:
                continue

            # Убираем дату и отправителя из первой строки для чистого анализа текста
            body_first = re.sub(r'^\d{1,2}\.\d{1,2}\.\d{2,4},?\s+\d{1,2}:\d{2}\s*-\s*[^:]+:\s*', '', lines[0])
            body_lines = [body_first] + lines[1:]
            body_text = "\n".join(body_lines).strip()
            body_lower = body_text.lower()

            # Ветка 1: Все еженедельные дайджесты и подборки Ринаты
            if any(dm in body_lower for dm in digest_markers):
                master_counter = parse_digest_lines(
                    body_lines, masters, master_counter,
                    is_leader_msg=("самым полезным участником" in body_lower)
                )
                continue

            # Пропускаем запросы клиентов, опросы и системные сообщения
            if any(sw in body_lower for sw in request_stop_words):
                continue

            # Ветка 2: Индивидуальные объявления (с тегами, 📍 Место или живым сленгом)
            ph_match = re.search(PHONE_PATTERN, body_text)
            if not ph_match:
                continue

            has_offer_tag = bool(re.search(r'#\s*(?:услуг|рекомендую|еда|место|полезноеместо|барбершоп|фотограф|дизайнер)', body_lower))
            has_offer_phrase = any(p in body_lower for p in [
                "📍 место", "📍полезное место", "полезный контакт дня", "рекомендую",
                "занимаюсь", "выполняю", "предоставляю услуги", "принимаю заказы",
                "мастер по", "установка и", "ремонт ", "доставка посылок", "домашние полуфабрикаты"
            ])

            if not (has_offer_tag or has_offer_phrase):
                continue

            phone = ph_match.group(0)
            clean_body = re.sub(r'https?://\S+', '', body_text)
            clean_body = re.sub(PHONE_PATTERN, '', clean_body)
            clean_body = re.sub(r'#\S+', '', clean_body)
            clean_body = re.sub(r'<Сообщение изменено>', '', clean_body)
            clean_body = " ".join(clean_body.split()).strip()

            if len(clean_body) < 8:
                continue

            # Пробуем вытащить имя из текста
            name = "Специалист"
            name_match = re.search(r'(?:меня зовут|мастер|имя:?)\s+([А-ЯЁ][а-яё]{2,15})', body_text, re.I)
            if name_match:
                name = name_match.group(1)

            master_counter = add_master(
                masters, master_counter, phone, name, clean_body,
                "Участник чата", starred=("⭐" in body_text or "рекомендую" in body_lower),
                overwrite=False
            )
    else:
        print("Файл _chat.txt не найден, парсим только .vcf")

    # Ветка 3: Добираем контакты из .vcf файлов (без перезаписи уже найденных в чате)
    master_counter = parse_vcf_files(masters, master_counter)

    masters_list = list(masters.values())
    masters_list.sort(key=lambda x: not x.get("starred", False))

    os.makedirs("data", exist_ok=True)
    with open("data/masters.json", "w", encoding="utf-8") as out:
        json.dump(masters_list, out, ensure_ascii=False, indent=2)

    print(f"Готово! Очищено от спама и структурировано {len(masters_list)} специалистов.")

if __name__ == "__main__":
    parse_chat()

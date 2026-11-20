import re
import json
import os
import glob
import zipfile
import urllib.request
import urllib.error

PHONE_PATTERN = r'(?:\+?7|8)?[\s\-]?(?:\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\b[679]\d{2}[\s\-]?\d{2}[\s\-]?\d{2}\b'

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

def extract_field(text: str, field_names: list) -> str:
    pattern = r'(?:^|\n)\s*(?:' + '|'.join(field_names) + r')\s*[:\-]\s*(.+?)(?=\n\s*(?:Кто|Кто я|Район|График|Оплата|Требования|Обязанности|Условия|Опыт|Навыки|Кого ищем|Рассматриваемые сферы|Контакт)\s*[:\-]|\Z)'
    m = re.search(pattern, text, re.I | re.S)
    if m:
        return " ".join(m.group(1).split()).strip()
    return ""

def parse_jobs_content(content: str) -> list:
    content = re.sub(r'[\u200e\u200f\u202a-\u202e\u202f\ufeff]', '', content)
    raw_messages = re.split(r'\n(?=\d{1,2}\.\d{1,2}\.\d{2,4})', content)

    stop_phrases = [
        "сообщения и звонки защищены", "создал(-а) группу", "присоединился(-ась)",
        "добавил(-а) контакт", "покинул(-а) группу", "закрепил(-а) сообщение",
        "вы вступили в группу", "почему удалили", "написала в личку",
        "подвести итоги недели", "напоминаю, что здесь вы можете",
        "файл добавлен", "кто скидывал номер детского врача", "без медиафайлов"
    ]

    jobs = []
    seen_keys = set()

    for msg in raw_messages:
        lines = [line.strip() for line in msg.split('\n') if line.strip()]
        if not lines:
            continue

        date_match = re.match(r'^(\d{1,2}\.\d{1,2}\.\d{2,4})', lines[0])
        msg_date = date_match.group(1) if date_match else ""

        body_first = re.sub(r'^\d{1,2}\.\d{1,2}\.\d{2,4},?\s+\d{1,2}:\d{2}\s*-\s*[^:]+:\s*', '', lines[0])
        body_lines = [body_first] + lines[1:]
        body_text = "\n".join(body_lines).replace("<Сообщение изменено>", "").strip()
        body_lower = body_text.lower()

        if len(body_text) < 25 or any(sp in body_lower for sp in stop_phrases):
            continue

        is_tagged = bool(re.search(r'#\s*(?:ваканси|ищу\s*работ|подработк|работ|архитектор)', body_lower))
        has_structured = ("кто:" in body_lower or "кто я:" in body_lower) and ("контакт" in body_lower or "район:" in body_lower)
        has_freeform = any(k in body_lower for k in ["нужен повар", "ищем ведущего", "требуется ", "ищу фармацевта"])

        if not (is_tagged or has_structured or has_freeform):
            continue

        if re.search(r'#\s*ищу\s*работ', body_lower) or "ищу работу" in body_lower or "ищем работу" in body_lower:
            job_type = "resume"
            badge = "#ищуработу"
        elif re.search(r'#\s*подработк', body_lower) or "подработк" in body_lower or "на новогоднюю ночь" in body_lower:
            job_type = "part_time"
            badge = "#подработка"
        else:
            job_type = "vacancy"
            badge = "#вакансия"

        who = extract_field(body_text, ["Кто я", "Кто"])
        district = extract_field(body_text, ["Район"]) or "Гагра"
        schedule = extract_field(body_text, ["График / оплата", "График"])
        salary = extract_field(body_text, ["Оплата"]) or "По договорённости"
        reqs = extract_field(body_text, ["Требования", "Кого ищем", "Опыт", "Навыки"])
        conds = extract_field(body_text, ["Условия", "Рассматриваемые сферы"])
        contact_raw = extract_field(body_text, ["Контакт"])

        if who:
            title = who[:85]
        else:
            clean_first = re.sub(r'#\S+', '', body_lines[0]).strip(" .:-—🎄🎤")
            title = clean_first[:85] if clean_first else "Предложение работы"

        ph_match = re.search(PHONE_PATTERN, contact_raw) or re.search(PHONE_PATTERN, body_text)
        phone = clean_phone(ph_match.group(0)) if ph_match else ""

        contact_text = contact_raw
        if ph_match and contact_text:
            contact_text = contact_text.replace(ph_match.group(0), "").strip(" ,-–—():")
        contact_text = re.sub(r'\((?:WhatsApp|Telegram|MAX|только WhatsApp|звонить[^)]*)\)', '', contact_text, flags=re.I).strip(" ,-–—")

        desc_parts = []
        if schedule:
            desc_parts.append(f"График: {schedule}")
        if reqs and reqs.lower() not in ["не указаны", "не указан"]:
            desc_parts.append(reqs)
        if conds:
            desc_parts.append(f"Условия: {conds}")

        if desc_parts:
            desc = " • ".join(desc_parts)
        else:
            clean_body = re.sub(PHONE_PATTERN, '', body_text)
            clean_body = re.sub(r'#\S+', '', clean_body)
            desc = " ".join(clean_body.split()).strip()

        dedup_key = f"{phone}_{title[:30].lower()}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        jobs.append({
            "type": job_type,
            "badge": badge,
            "title": title,
            "salary": salary[:60],
            "district": district[:50],
            "desc": desc[:320] + ("..." if len(desc) > 320 else ""),
            "contact": contact_text[:60] if contact_text else district[:40],
            "phone": phone,
            "date": msg_date
        })

    jobs.reverse()
    for idx, item in enumerate(jobs, 1):
        item["id"] = idx
    return jobs

def sync_to_supabase(jobs: list):
    sb_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    sb_key = os.environ.get("SUPABASE_KEY", "")

    if not sb_url or not sb_key:
        print("SUPABASE_URL или SUPABASE_KEY не заданы — пропускаем отправку в Supabase.")
        return

    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    # 1. Получаем уже существующие записи, чтобы не плодить дубли
    existing_keys = set()
    try:
        req = urllib.request.Request(
            f"{sb_url}/rest/v1/jobs?select=phone,title",
            headers=headers,
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            rows = json.loads(resp.read().decode("utf-8"))
            for r in rows:
                ph = re.sub(r'\D', '', str(r.get("phone") or ""))
                t = str(r.get("title") or "")[:30].lower().strip()
                existing_keys.add(f"{ph}_{t}")
    except Exception as e:
        print(f"Ошибка чтения существующих вакансий из Supabase: {e}")
        return

    # 2. Собираем только новые вакансии
    to_insert = []
    for job in jobs:
        ph = re.sub(r'\D', '', job.get("phone", ""))
        t = job.get("title", "")[:30].lower().strip()
        key = f"{ph}_{t}"
        if key in existing_keys:
            continue
        existing_keys.add(key)

        to_insert.append({
            "type": job["badge"],
            "title": job["title"],
            "salary": job["salary"],
            "desc": job["desc"],
            "contact": job["contact"],
            "city": job["district"],
            "phone": job["phone"],
            "is_approved": False
        })

    if not to_insert:
        print("Новых вакансий для отправки на модерацию в Supabase нет.")
        return

    # 3. Отправляем пачкой в Supabase
    try:
        payload = json.dumps(to_insert, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{sb_url}/rest/v1/jobs",
            data=payload,
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"Отправлено на модерацию в Supabase (jobs): {len(to_insert)} шт.")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"Ошибка записи в Supabase ({e.code}): {err_body}")
    except Exception as e:
        print(f"Ошибка отправки в Supabase: {e}")

def main():
    texts = []

    if os.path.exists("data/jobs_chat.txt"):
        with open("data/jobs_chat.txt", "r", encoding="utf-8", errors="ignore") as f:
            texts.append(f.read())

    for zpath in sorted(glob.glob("*.zip") + glob.glob("data/*.zip"), key=os.path.getmtime):
        try:
            with zipfile.ZipFile(zpath, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir() or not info.filename.lower().endswith(".txt"):
                        continue
                    raw_txt = zf.read(info).decode("utf-8", errors="ignore")
                    if "ваканси" in info.filename.lower() or "ваканси" in zpath.lower() or "#вакансия" in raw_txt.lower():
                        print(f"Найден чат вакансий в архиве: {zpath} -> {info.filename}")
                        texts.append(raw_txt)
        except Exception as e:
            print(f"Ошибка чтения архива {zpath}: {e}")

    if not texts:
        print("Файлы чата вакансий не найдены.")
        return

    all_jobs = parse_jobs_content("\n".join(texts))

    os.makedirs("data", exist_ok=True)
    with open("data/jobs.json", "w", encoding="utf-8") as out:
        json.dump(all_jobs, out, ensure_ascii=False, indent=2)

    print(f"Готово! Структурировано предложений работы: {len(all_jobs)}")
    sync_to_supabase(all_jobs)

if __name__ == "__main__":
    main()

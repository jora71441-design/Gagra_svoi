// ==================== КОНФИГУРАЦИЯ SUPABASE ====================

const SUPABASE_URL = 'https://yzbochrahmuhvryinajr.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl6Ym9jaHJhaG11aHZyeWluYWpyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMyNzYyODcsImV4cCI6MjEwODg1MjI4N30.dTjerKbrcLuTEr5xPKXkR43Df4ECaGA-ztCrGD_SO-A';

const sbHeaders = {
  'apikey': SUPABASE_ANON_KEY,
  'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
  'Content-Type': 'application/json'
};

async function insertToSupabase(table, data) {
  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/${table}`, {
      method: 'POST',
      headers: { ...sbHeaders, 'Prefer': 'return=minimal' },
      body: JSON.stringify(data)
    });
    if (!res.ok) console.error(`Ошибка записи в ${table}:`, await res.text());
  } catch (err) {
    console.error(`Сетевой сбой при отправке в ${table}:`, err);
  }
}

// ==================== ТАКСОНОМИЯ И СОСТОЯНИЕ ====================

const TAXONOMY = {
  appliances: {
    all: "Вся техника",
    washers: "Стиральные машины",
    fridges: "Холодильники",
    aircon: "Кондиционеры",
    gadgets: "Телефоны и ТВ",
    small_appliances: "Мелкая техника"
  },
  engineering: {
    all: "Вся сантехника/свет",
    plumbing: "Сантехника и вода",
    heating: "Котлы и отопление",
    electric: "Электрика и свет",
    underfloor: "Тёплые полы"
  },
  finish: {
    all: "Вся отделка",
    wallpaper: "Обои и покраска",
    ceilings: "Натяжные потолки",
    tiles: "Плитка и кафель",
    flooring: "Ламинат и полы",
    doors: "Окна и двери",
    furniture: "Мебель и сборка"
  },
  construction: {
    all: "Вся стройка",
    building: "Стройка под ключ",
    welding: "Сварка и навесы",
    climbing: "Пром. альпинизм",
    waste: "Вывоз мусора"
  },
  auto: {
    all: "Весь транспорт",
    autodiag: "Диагностика и автоэлектрик",
    gearbox: "Ремонт АКПП",
    bike: "Велосипеды",
    delivery: "Доставка и грузы"
  },
  lifestyle: {
    all: "Весь быт и здоровье",
    medical: "Массаж и врачи",
    beauty: "Красота и уход",
    garden: "Покос травы",
    sewing: "Шторы и шитье",
    stores: "Магазины и сервисы"
  }
};

// Словарь синонимов и народных запросов для поиска
const SEARCH_SYNONYMS = {
  'стиралка': ['стиральн', 'машин', 'постирать', 'стирплк', 'стирмашин'],
  'стиральная': ['стиралк', 'машин'],
  'кондер': ['кондиционер', 'сплит', 'климат', 'фреон', 'кондей'],
  'кондей': ['кондиционер', 'сплит', 'климат', 'кондер'],
  'кондиционер': ['кондер', 'сплит', 'климат', 'кондей'],
  'сантехник': ['сантехник', 'труб', 'кран', 'смесител', 'унитаз', 'засор', 'канализац', 'протечк', 'бойлер', 'котел'],
  'электрик': ['электрик', 'проводк', 'свет', 'розетк', 'щиток', 'автомат'],
  'плитка': ['плиточн', 'кафел', 'керамогранит', 'ванн'],
  'кафель': ['плитк', 'плиточн', 'керамогранит', 'ванн'],
  'починить': ['ремонт', 'мастер', 'исправ', 'настройк'],
  'ремонт': ['починить', 'мастер', 'исправ', 'отделк'],
  'авто': ['машин', 'автоэлектрик', 'коробк', 'акпп', 'диагностик', 'мотор'],
  'шторы': ['пошив', 'ткан', 'шить', 'штор'],
  'психолог': ['терапи', 'консультац', 'психотерапевт'],
  'собака': ['животн', 'грумер', 'ветеринар', 'щенок', 'пес']
};

let masters = [];
let helpsData = [];
let currentRoute = 'hub';
let activeCategory = 'all';
let activeSubcategory = 'all';

// ==================== РОУТИНГ И НАВИГАЦИЯ ====================

// Функция нативного шеринга ссылкой на портал
async function sharePortal() {
  const shareData = {
    title: 'Город Своих — Гагра & Абхазия',
    text: 'Единый сервис для жителей и гостей Гагры: проверенные мастера, долгосрочная аренда и вакансии без посредников.',
    url: window.location.origin + window.location.pathname
  };

  if (navigator.share) {
    try {
      await navigator.share(shareData);
    } catch (err) {
      if (err.name !== 'AbortError') console.warn('Ошибка шеринга:', err);
    }
  } else if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(shareData.url);
      alert('Ссылка на портал скопирована в буфер обмена!');
    } catch (e) {
      prompt('Скопируйте ссылку на портал:', shareData.url);
    }
  } else {
    prompt('Скопируйте ссылку на портал:', shareData.url);
  }
}

function navigateTo(route) {
  currentRoute = route;
  window.location.hash = (route === 'hub') ? '' : route;
  applyRoute();
}

function applyRoute() {
  const hash = window.location.hash.replace('#', '');
  currentRoute = ['masters', 'jobs', 'rent', 'helps'].includes(hash) ? hash : 'hub';

  const isHub = (currentRoute === 'hub');

  const vHub = document.getElementById('view-hub');
  const vHeader = document.getElementById('innerHeader');
  const vMasters = document.getElementById('view-masters');
  const vJobs = document.getElementById('view-jobs');
  const vRent = document.getElementById('view-rent');
  const vHelps = document.getElementById('view-helps');

  if (vHub) vHub.classList.toggle('hidden', !isHub);
  if (vHeader) vHeader.classList.toggle('hidden', isHub);
  if (vMasters) vMasters.classList.toggle('hidden', currentRoute !== 'masters');
  if (vJobs) vJobs.classList.toggle('hidden', currentRoute !== 'jobs');
  if (vRent) vRent.classList.toggle('hidden', currentRoute !== 'rent');
  if (vHelps) vHelps.classList.toggle('hidden', currentRoute !== 'helps');

  const titleEl = document.getElementById('innerHeaderTitle');
  const actionBtn = document.getElementById('innerHeaderActionBtn');

  if (actionBtn && titleEl) {
    if (currentRoute === 'masters') {
      titleEl.textContent = 'Мастера и услуги';
      actionBtn.className = "text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1.5 rounded-xl border border-emerald-200 hover:bg-emerald-100 transition";
      actionBtn.textContent = '+ Разместить';
    } else if (currentRoute === 'jobs') {
      titleEl.textContent = 'Работа и вакансии';
      actionBtn.className = "text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1.5 rounded-xl border border-blue-200 hover:bg-blue-100 transition";
      actionBtn.textContent = '+ Вакансия';
        } else if (currentRoute === 'rent') {
      titleEl.textContent = 'Аренда / сдача жилья';
      actionBtn.className = "text-xs font-bold text-sky-700 bg-sky-50 px-2.5 py-1.5 rounded-xl border border-sky-200 hover:bg-sky-100 transition";
      actionBtn.textContent = '+ Сдать жилье';
        } else if (currentRoute === 'helps') {
      titleEl.textContent = 'Город Своих помогает';
      actionBtn.className = "text-xs font-bold text-teal-800 bg-teal-50 px-2.5 py-1.5 rounded-xl border border-teal-200 hover:bg-teal-100 transition";
      actionBtn.textContent = '+ Инициатива';
    }
  }

  // Запуск отрисовки разделов при переходе
  if (currentRoute === 'rent') {
    renderRent();
  } else if (currentRoute === 'helps') {
    renderHelps();
  }

  window.scrollTo(0, 0);
}

window.addEventListener('hashchange', applyRoute);

// ==================== ЗАГРУЗКА ДАННЫХ (ГИБРИДНЫЙ РЕЖИМ) ====================

async function loadData() {
  let dbMasters = [];
  let localMasters = [];

  // 1. Тянем проверенных мастеров из Supabase
  try {
    const sbRes = await fetch(`${SUPABASE_URL}/rest/v1/masters?select=*&is_approved=eq.true&order=created_at.desc`, {
      headers: sbHeaders
    });
    if (sbRes.ok) dbMasters = await sbRes.json();
  } catch (e) {
    console.warn('Supabase недоступен, работаем с локальными данными');
  }

  // 2. Тянем основной каталог из masters.json
  try {
    const localRes = await fetch('data/masters.json?v=' + Date.now());
    if (localRes.ok) localMasters = await localRes.json();
  } catch (e) {
    console.warn('masters.json не найден');
  }

  // 3. Объединяем: новые из базы идут первыми, дубликаты по телефону отсекаются
  const dbPhones = new Set(dbMasters.map(m => (m.phone || '').replace(/[^0-9]/g, '')));
  const filteredLocal = localMasters.filter(m => !dbPhones.has((m.phone || '').replace(/[^0-9]/g, '')));
  masters = [...dbMasters, ...filteredLocal];
  
    // Лидер недели
  const leader = masters.find(m => m.is_leader) || masters.find(m => m.name && m.name.includes("Владимир"));
  const leaderCard = document.getElementById('hubLeaderCard');
  if (leaderCard) {
    if (leader) {
      leaderCard.classList.remove('hidden');
      const lName = document.getElementById('hubLeaderName');
      const lCat = document.getElementById('hubLeaderCategory');
      const lCity = document.getElementById('hubLeaderCity');
      const lDesc = document.getElementById('hubLeaderDesc');
      const lPhone = document.getElementById('hubLeaderPhone');
      const lWa = document.getElementById('hubLeaderWaLink');
      const lTel = document.getElementById('hubLeaderTelLink');
      const lSocWrap = document.getElementById('hubLeaderSocialWrap');
      const lSoc = document.getElementById('hubLeaderSocial');

      if (lName) lName.textContent = leader.name || '';
      if (lCat) lCat.textContent = leader.category_title || leader.subcategory_title || 'Услуги';
      if (lCity) lCity.textContent = leader.city || 'Гагра';
      if (lDesc) lDesc.textContent = leader.service || '';
      if (lPhone) lPhone.textContent = leader.phone || '';

      const cleanPhone = (leader.phone || '').replace(/[^0-9]/g, '');
      if (lWa) {
        const waText = encodeURIComponent(`Здравствуйте, ${leader.name}! Увидел ваш золотой закреп на главной "Город Своих".`);
        lWa.href = `https://wa.me/${cleanPhone}?text=${waText}`;
      }
      if (lTel) {
        lTel.href = `tel:${cleanPhone || leader.phone || ''}`;
      }

      if (lSocWrap && lSoc) {
        if (leader.social && leader.social.trim()) {
          lSocWrap.classList.remove('hidden');
          lSoc.href = leader.social.trim();
          const sLower = leader.social.toLowerCase();
          let label = 'Портфолио / Соцсети';
          if (sLower.includes('instagram.com')) label = 'Instagram мастера';
          else if (sLower.includes('t.me')) label = 'Telegram мастера';
          else if (sLower.includes('vk.com')) label = 'ВКонтакте мастера';
          const labelSpan = lSoc.querySelector('span');
          if (labelSpan) labelSpan.textContent = label;
        } else {
          lSocWrap.classList.add('hidden');
        }
      }
    } else {
      leaderCard.classList.add('hidden');
    }
  }
  renderMasters();

  // 4. Загрузка инициатив взаимовыручки
  try {
    const sbHelpsRes = await fetch(`${SUPABASE_URL}/rest/v1/helps?select=*&is_approved=eq.true&order=created_at.desc`, {
      headers: sbHeaders
    });
    if (sbHelpsRes.ok) {
      const dbHelps = await sbHelpsRes.json();
      if (dbHelps.length > 0) {
        helpsData = dbHelps;
      } else {
        await loadHelpsFromChatFile();
      }
    } else {
      await loadHelpsFromChatFile();
    }
  } catch (e) {
    await loadHelpsFromChatFile();
  }
  renderHelps('all');
}

async function loadHelpsFromChatFile() {
  try {
    const chatRes = await fetch('data/helps_chat.txt?v=' + Date.now());
    if (chatRes.ok) {
      const chatText = await chatRes.text();
      helpsData = parseHelpsFromChat(chatText);
    }
  } catch (err) {
    console.warn('helps_chat.txt пока не содержит данных');
  }
}

function parseHelpsFromChat(text) {
  const messages = text.split(/\n(?=\[?\d{2}\.\d{2}\.\d{2,4})/);
  const results = [];

  messages.forEach(msg => {
    const tags = ['#помощь_животным', '#эко_субботник', '#взаимовыручка', '#соц_мероприятие'];
    const foundTag = tags.find(t => msg.includes(t));
    if (!foundTag) return;

    let type = 'all', badge = '🤝 Инициатива';
    if (foundTag === '#помощь_животным') { type = 'animals'; badge = '🐾 Помощь животным'; }
    else if (foundTag === '#эко_субботник') { type = 'eco'; badge = '🌿 Эко-десант'; }
    else if (foundTag === '#взаимовыручка') { type = 'care'; badge = '🤝 Взаимовыручка'; }
    else if (foundTag === '#соц_мероприятие') { type = 'events'; badge = '🎈 Мероприятие'; }

    const extract = (keyword) => {
      const regex = new RegExp(`${keyword}\\s*(.*?)(?=\\n[А-Яа-яЁё]+:|\\n—|$)`, 's');
      const match = msg.match(regex);
      return match ? match[1].trim() : '';
    };

    const title = extract('Заголовок:') || extract('Инициатива:');
    const desc = extract('Описание:');
    const city = extract('Город:');
    const contactRaw = extract('Связь:') || extract('Координатор:');

    const phoneMatch = contactRaw.match(/\+?\d[\d\s\-()]{9,}/);
    const phone = phoneMatch ? phoneMatch[0] : '';
    const contactName = contactRaw.replace(phone, '').replace(/,\s*$/, '').trim();

    if (title && desc) {
      results.push({
        type: type,
        badge: badge,
        title: title,
        desc: desc,
        city: city || 'Гагра',
        contact: contactName || 'Куратор',
        phone: phone,
        status: 'Актуально',
        btn_text: 'Откликнуться'
      });
    }
  });

  return results.reverse();
}

    // ==================== АРЕНДА И СДАЧА ЖИЛЬЯ ====================
let rentList = [
  {
    id: 1,
    title: "2-комнатная квартира с ремонтом",
    price: "35 000 ₽ / мес",
    city: "Гагра",
    district: "Кемпинг",
    category: "flat",
    period: "year",
    type: "flat",
    badge: "🔒 На год+",
    desc: "Вся необходимая мебель, кондиционер, стиральная машина, автономное отопление. Фиксация цены без сезонных изменений.",
    photos: [],
    status: "Свободна к заселению",
    tg_link: "https://t.me/arenda_abkhazia_svoi"
  }
];

let rentFilterState = {
  city: 'all',
  category: 'all', // 'flat' | 'house'
  period: 'all'    // 'year' | 'season'
};
let rentDataLoaded = false;

// Автоматическая загрузка спарсенной базы из data/rent.json
async function loadRentData() {
  try {
    const res = await fetch('data/rent.json?v=' + Date.now());
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        rentList = data;
      }
    }
  } catch (e) {
    console.warn('Локальный rent.json пока недоступен, используется резервная база:', e);
  }
  rentDataLoaded = true;
  renderRent();
}

function renderRent() {
  if (!rentDataLoaded) {
    loadRentData();
    return;
  }

  const container = document.getElementById('rentContainer');
  if (!container) return;
  container.innerHTML = '';

  const filtered = rentList.filter(item => {
    // 1. Фильтр по городу
    if (rentFilterState.city !== 'all') {
      const itemCity = (item.city || '').toLowerCase();
      const filterCity = rentFilterState.city.toLowerCase();
      if (!itemCity.includes(filterCity)) return false;
    }

    // 2. Фильтр по категории: Квартира vs Дом
    if (rentFilterState.category !== 'all') {
      const itemCat = item.category || (item.type === 'house' ? 'house' : 'flat');
      if (itemCat !== rentFilterState.category) return false;
    }

    // 3. Фильтр по сроку: На год+ vs До лета
    if (rentFilterState.period !== 'all') {
      const itemPeriod = item.period || (item.type === 'season' ? 'season' : 'year');
      if (itemPeriod !== rentFilterState.period) return false;
    }

    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="bg-white rounded-3xl p-6 text-center border border-slate-200 shadow-xs">
        <span class="text-3xl">🏠</span>
        <p class="text-sm font-bold text-slate-800 mt-2">Нет вариантов по заданным параметрам</p>
        <p class="text-xs text-slate-500 mt-1">Попробуйте сбросить фильтры или выбрать другой город.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(item => {
    const isYear = (item.period || item.type) !== 'season';
    const periodBadge = isYear ? '🔒 На год+' : '⏳ До лета';
    const periodClass = isYear 
      ? 'bg-amber-100 text-amber-900 border border-amber-300' 
      : 'bg-sky-100 text-sky-900 border border-sky-300';
    
    const isHouse = (item.category === 'house' || item.type === 'house');
    const catBadge = isHouse ? '🏡 Дом' : '🏢 Квартира';
    const hasPhotos = Array.isArray(item.photos) && item.photos.length > 0;

    let mediaHtml = '';
    if (hasPhotos) {
      const photosImg = item.photos.map(url => `
        <img src="${url}" loading="lazy" class="snap-center w-full h-52 object-cover shrink-0 select-none pointer-events-none" alt="${item.title}">
      `).join('');

      mediaHtml = `
        <div class="relative h-52 bg-slate-900 overflow-hidden">
          <div class="flex overflow-x-auto snap-x snap-mandatory no-scrollbar h-full w-full">
            ${photosImg}
          </div>
          <div class="absolute inset-x-0 top-0 h-14 bg-gradient-to-b from-black/60 to-transparent pointer-events-none"></div>
          <span class="absolute top-3 left-3 bg-slate-900/80 text-white text-[10px] font-bold px-2.5 py-1 rounded-lg backdrop-blur-xs">
            ${item.city} • ${item.district}
          </span>
          <div class="absolute top-3 right-3 flex items-center gap-1.5">
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-white/95 text-slate-800 shadow-xs">
              ${catBadge}
            </span>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-md ${periodClass}">
              ${periodBadge}
            </span>
          </div>
          ${item.photos.length > 1 ? `
            <span class="absolute bottom-2.5 right-3 bg-slate-900/70 text-white text-[10px] font-medium px-2 py-0.5 rounded-full backdrop-blur-xs">
              📷 1/${item.photos.length} свайп →
            </span>
          ` : ''}
        </div>
      `;
    } else {
      const icon = isHouse ? '🏡' : '🏢';
      mediaHtml = `
        <div class="h-36 bg-slate-100 flex items-center justify-center text-slate-400 relative">
          <span class="absolute top-3 left-3 bg-slate-900/80 text-white text-[10px] font-bold px-2.5 py-1 rounded-lg backdrop-blur-xs">
            ${item.city} • ${item.district}
          </span>
          <div class="absolute top-3 right-3 flex items-center gap-1.5">
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-white text-slate-800 border border-slate-200">
              ${catBadge}
            </span>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-md ${periodClass}">
              ${periodBadge}
            </span>
          </div>
          <span class="text-4xl">${icon}</span>
        </div>
      `;
    }

    const card = document.createElement('div');
    card.className = "bg-white rounded-3xl overflow-hidden border border-slate-200 shadow-xs hover:border-slate-300 transition";
    card.innerHTML = `
      ${mediaHtml}
      <div class="p-4">
        <div class="flex justify-between items-start mb-1.5 gap-2">
          <h3 class="text-base font-bold text-slate-900 leading-snug">${item.title}</h3>
          <span class="text-xs font-black text-emerald-700 whitespace-nowrap">${item.price}</span>
        </div>
        <p class="text-xs text-slate-600 mb-3 leading-relaxed">${item.desc}</p>
        <div class="flex items-center justify-between pt-2.5 border-t border-slate-100">
          <span class="text-[11px] text-slate-500 font-medium">${item.status}</span>
          <a href="${item.tg_link}" target="_blank" 
             class="bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-3 py-1.5 rounded-xl transition active:scale-95">
            Пост в TG ↗
          </a>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function setRentCity(city) {
  rentFilterState.city = city;
  document.querySelectorAll('.rent-city-chip').forEach(btn => {
    btn.className = "rent-city-chip bg-white text-slate-700 border border-slate-200 text-xs font-medium px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-sky-50 transition";
  });
  const el = window.event && (window.event.currentTarget || window.event.target);
  if (el) {
    el.className = "rent-city-chip active bg-slate-900 text-white text-xs font-semibold px-3 py-1.5 rounded-full whitespace-nowrap shadow-xs transition";
  }
  renderRent();
}

function setRentCategory(cat) {
  rentFilterState.category = cat;
  document.querySelectorAll('.rent-cat-chip').forEach(btn => {
    btn.className = "rent-cat-chip bg-white text-slate-700 border border-slate-200 text-xs font-medium px-3 py-1 rounded-full whitespace-nowrap hover:bg-sky-50 transition";
  });
  const el = window.event && (window.event.currentTarget || window.event.target);
  if (el) {
    el.className = "rent-cat-chip active bg-slate-900 text-white text-xs font-semibold px-3 py-1 rounded-full whitespace-nowrap shadow-xs transition";
  }
  renderRent();
}

function setRentPeriod(period) {
  rentFilterState.period = period;
  document.querySelectorAll('.rent-period-chip').forEach(btn => {
    btn.className = "rent-period-chip bg-white text-slate-700 border border-slate-200 text-xs font-medium px-3 py-1 rounded-full whitespace-nowrap hover:bg-sky-50 transition";
  });
  const el = window.event && (window.event.currentTarget || window.event.target);
  if (el) {
    el.className = "rent-period-chip active bg-sky-600 text-white text-xs font-semibold px-3 py-1 rounded-full whitespace-nowrap shadow-xs transition";
  }
  renderRent();
}

// ==================== РЕНДЕРИНГ ====================

let currentHelpsType = 'all';
let currentAnimalSub = 'all';

function renderHelps() {
  const container = document.getElementById('helpsContainer');
  if (!container) return;
  container.innerHTML = '';

  const filtered = helpsData.filter(item => {
    // 1. Фильтр макро-направления
    if (currentHelpsType !== 'all' && item.type !== currentHelpsType) {
      return false;
    }

    // 2. Умная фильтрация подзакладок внутри раздела «Животные»
    if (currentHelpsType === 'animals' && currentAnimalSub !== 'all') {
      const fullTxt = `${item.title || ''} ${item.desc || ''}`.toLowerCase();
      if (currentAnimalSub === 'adopt') {
        // Ищут дом / пристрой
        return /дом|пристрой|руки|щенок|щенят|котен|котят|малыш|отдам|семь/i.test(fullTxt);
      } else if (currentAnimalSub === 'lost') {
        // Потерянные и найденные
        return /потер|пропал|нашл|найден|убежал|поиск|ошейник/i.test(fullTxt);
      } else if (currentAnimalSub === 'shelter') {
        // Лечение, корм, клиника, приют
        return /приют|лечен|операц|клиник|вет|корм|сбор|стационар|стерил|вакцин/i.test(fullTxt);
      }
    }

    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="bg-white rounded-3xl p-6 text-center border border-slate-200 shadow-xs">
        <span class="text-3xl">🐾</span>
        <p class="text-sm font-bold text-slate-800 mt-2">Пока нет активных записей в этой категории</p>
        <p class="text-xs text-slate-500 mt-1">Вы можете предложить свою инициативу с помощью кнопки вверху.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(item => {
    const cleanPhone = (item.phone || '').replace(/[^0-9]/g, '');
    const linkHref = cleanPhone 
      ? `https://api.whatsapp.com/send?phone=${cleanPhone}&text=` + encodeURIComponent(`Здравствуйте! Пишу по поводу инициативы "${item.title}" на портале Город Своих.`)
            : (item.chat_link || 'https://chat.whatsapp.com/CdowehMFvoy7E5uVBkGLRS?s=cl&p=a&iam=2');

    const card = document.createElement('div');
    card.className = "help-card bg-white rounded-3xl p-4 border border-slate-200 shadow-xs";
    card.innerHTML = `
      <div class="flex items-start justify-between gap-2 mb-1.5">
        <span class="text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-md">${item.badge}</span>
        <span class="text-[11px] font-semibold text-emerald-700">${item.status || 'Актуально'}</span>
      </div>
      <h3 class="text-sm font-bold text-slate-900">${item.title}</h3>
      <p class="text-xs text-slate-600 my-2 leading-relaxed">${item.desc}</p>
      <div class="flex items-center justify-between pt-2.5 border-t border-slate-100 text-xs">
        <span class="text-slate-500 font-medium">${item.city || 'Гагра'} • ${item.contact || 'Куратор'}</span>
        <a href="${linkHref}" target="_blank" 
           class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-3 py-1.5 rounded-xl transition active:scale-95">
          ${item.btn_text || 'Откликнуться'}
        </a>
      </div>
    `;
    container.appendChild(card);
  });
}

function filterHelps(type) {
  currentHelpsType = type;
  currentAnimalSub = 'all';

  // Переключение стилей кнопок первого уровня
  document.querySelectorAll('.help-chip').forEach(btn => {
    btn.className = "help-chip bg-white text-slate-700 border border-slate-200 text-xs font-medium px-3.5 py-1.5 rounded-full whitespace-nowrap shadow-xs";
  });
  if (window.event && window.event.target) {
    window.event.target.className = "help-chip active bg-slate-900 text-white text-xs font-medium px-3.5 py-1.5 rounded-full whitespace-nowrap shadow-xs";
  }

  // Показываем подзакладки только для животных
  const subContainer = document.getElementById('animalSubBarContainer');
  if (subContainer) {
    subContainer.classList.toggle('hidden', type !== 'animals');
  }

  // Сбрасываем кнопки подзакладок на «Все животные»
  document.querySelectorAll('.animal-sub-btn').forEach(btn => {
    btn.className = "animal-sub-btn bg-white text-slate-700 text-[11px] font-semibold px-3 py-1 rounded-xl whitespace-nowrap hover:bg-emerald-50 transition";
  });
  const firstSub = document.querySelector('.animal-sub-btn');
  if (firstSub) {
    firstSub.className = "animal-sub-btn active bg-emerald-700 text-white text-[11px] font-bold px-3 py-1 rounded-xl whitespace-nowrap shadow-xs transition";
  }

  renderHelps();
}

function filterAnimalSub(subType) {
  currentAnimalSub = subType;
  document.querySelectorAll('.animal-sub-btn').forEach(btn => {
    btn.className = "animal-sub-btn bg-white text-slate-700 text-[11px] font-semibold px-3 py-1 rounded-xl whitespace-nowrap hover:bg-emerald-50 transition";
  });
  if (window.event && window.event.target) {
    window.event.target.className = "animal-sub-btn active bg-emerald-700 text-white text-[11px] font-bold px-3 py-1 rounded-xl whitespace-nowrap shadow-xs transition";
  }
  renderHelps();
}

function renderSubBar() {
  const container = document.getElementById('subBarContainer');
  const bar = document.getElementById('subBar');
  if (!container || !bar) return;

  if (activeCategory === 'all' || !TAXONOMY[activeCategory]) {
    container.classList.add('hidden');
    bar.innerHTML = '';
    activeSubcategory = 'all';
    return;
  }

  container.classList.remove('hidden');
  bar.innerHTML = '';

  const subs = TAXONOMY[activeCategory];
  Object.keys(subs).forEach(subKey => {
    const btn = document.createElement('button');
    const isActive = (activeSubcategory === subKey);
    btn.className = isActive 
      ? "sub-btn active bg-emerald-600 text-white text-[11px] font-semibold px-2.5 py-1 rounded-lg whitespace-nowrap shadow-xs transition"
      : "sub-btn bg-white text-slate-700 text-[11px] font-medium px-2.5 py-1 rounded-lg whitespace-nowrap hover:bg-slate-50 transition";
    btn.textContent = subs[subKey];
    btn.onclick = () => {
      activeSubcategory = subKey;
      renderSubBar();
      renderMasters();
    };
    bar.appendChild(btn);
  });
}

function matchesQuery(master, searchWords) {
  if (searchWords.length === 0) return true;
  const fullContext = [
    master.name,
    master.service,
    master.category_title,
    master.subcategory_title || '',
    master.phone,
    ...(master.keywords || [])
  ].join(' ').toLowerCase();

  return searchWords.every(rawWord => {
    const word = rawWord.toLowerCase();
    const stem = word.length > 4 ? word.substring(0, word.length - 2) : word;

    // 1. Прямое совпадение по слову или усеченному корню
    if (fullContext.includes(word) || fullContext.includes(stem)) return true;

    // 2. Проверка по словарю синонимов и народных формулировок
    const syns = SEARCH_SYNONYMS[word] || SEARCH_SYNONYMS[stem] || [];
    return syns.some(syn => fullContext.includes(syn));
  });
}

function renderMasters() {
  const sInput = document.getElementById('searchInput');
  if (!sInput) return;
  const rawQuery = sInput.value.trim().toLowerCase();
  const searchWords = rawQuery ? rawQuery.split(/\s+/) : [];
  
  const listEl = document.getElementById('mastersList');
  const emptyEl = document.getElementById('emptyState');
  const countEl = document.getElementById('countDisplay');
  if (!listEl) return;

  const filtered = masters.filter(m => {
    const matchesCat = (activeCategory === 'all') || 
                       (m.category === activeCategory) ||
                       (m.category_title && m.category_title.toLowerCase().includes(activeCategory));

    const matchesSub = (activeSubcategory === 'all') || (m.subcategory === activeSubcategory);
    const matchesSearch = matchesQuery(m, searchWords);
    return matchesCat && matchesSub && matchesSearch;
  });

  // КОНТЕКСТНАЯ СОРТИРОВКА:
  // Во вкладке «Все» первым идет Топ каталога (is_top_all).
  // Внутри выбранной категории первым идет Закреп раздела (is_pinned).
  filtered.sort((a, b) => {
    if (activeCategory === 'all') {
      return (b.is_top_all ? 1 : 0) - (a.is_top_all ? 1 : 0);
    } else {
      return (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0);
    }
  });

  if (countEl) countEl.textContent = filtered.length;
  listEl.innerHTML = '';

  if (filtered.length === 0) {
    if (emptyEl) emptyEl.classList.remove('hidden');
    return;
  }
  if (emptyEl) emptyEl.classList.add('hidden');

  filtered.forEach(m => {
    const cleanPhone = (m.phone || '').replace(/[^0-9]/g, '');
    const waText = encodeURIComponent(`Здравствуйте, ${m.name}! Нашел ваш контакт в каталоге мастеров "Город Своих" (Гагра).`);
    const waLink = `https://wa.me/${cleanPhone}?text=${waText}`;
    const telLink = `tel:${m.phone}`;

    // Шаблон сообщения для жалобы куратору
    const complaintText = encodeURIComponent(`Здравствуйте, Рината! Претензия/жалоба по мастеру из каталога «Город Своих»:
Специалист: ${m.name}
Телефон: ${m.phone}
Сфера: ${m.subcategory_title || m.category_title || 'Услуги'}
Суть проблемы: `);
    const complaintLink = `https://wa.me/79263949118?text=${complaintText}`;

    const isContextTop = (activeCategory === 'all' && m.is_top_all);
    const isCategoryPin = (activeCategory !== 'all' && m.is_pinned);

    let borderClass = 'border-slate-200/90 bg-white';
    let promoBadge = '';

    if (isContextTop) {
      borderClass = 'border-amber-400 ring-2 ring-amber-300/60 bg-amber-50/15';
      promoBadge = `
        <span class="text-[10px] font-black bg-gradient-to-r from-amber-500 to-yellow-500 text-white px-2 py-0.5 rounded-md shadow-2xs">
          🔥 Топ каталога
        </span>
      `;
    } else if (isCategoryPin) {
      borderClass = 'border-amber-400 ring-2 ring-amber-300/60 bg-amber-50/15';
      promoBadge = `
        <span class="text-[10px] font-bold bg-yellow-100 text-yellow-900 border border-yellow-300 px-2 py-0.5 rounded-md">
          ⭐ В топе раздела
        </span>
      `;
    }

    // Расчет количества рекомендаций
    const recCount = m.recommendations_count || (m.starred ? 1 : 0);

    const card = document.createElement('div');
    card.className = `${borderClass} rounded-3xl p-4 border shadow-xs hover:border-slate-300 transition`;
    card.innerHTML = `
      <div class="flex items-start justify-between gap-2 mb-1.5">
        <div>
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="text-[10px] font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md">
              ${m.subcategory_title || m.category_title}
            </span>
            ${promoBadge}
          </div>
          <h3 class="text-base font-bold text-slate-900 leading-snug mt-1">${m.name}</h3>
        </div>
        ${m.starred ? `
          <span class="text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full whitespace-nowrap">
            ⭐ Рекомендуют (${recCount})
          </span>
        ` : `
          <span class="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full whitespace-nowrap">
            ✓ Проверен
          </span>
        `}
      </div>
      
      <p class="text-xs text-slate-600 mb-2 leading-relaxed">${m.service}</p>
      ${m.social ? `<p class="text-[11px] text-blue-700 font-medium mb-2">🔗 <a href="${m.social}" target="_blank" class="hover:underline">${m.social}</a></p>` : ''}
      
      <!-- Телефон и кнопка жалобы -->
      <div class="flex items-center justify-between mb-3 text-[11px]">
        <span class="font-mono font-medium text-slate-500">${m.phone}</span>
        <a href="${complaintLink}" target="_blank" 
           class="text-slate-400 hover:text-rose-600 transition flex items-center gap-1 font-medium">
          <span>🚩</span> Пожаловаться
        </a>
      </div>

      <div class="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100">
        <a href="${waLink}" target="_blank" 
           class="flex items-center justify-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-2.5 px-3 rounded-2xl transition shadow-xs">
          WhatsApp
        </a>
        <a href="${telLink}" 
           class="flex items-center justify-center gap-1 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold py-2.5 px-3 rounded-2xl transition">
          Позвонить
        </a>
      </div>
    `;
    listEl.appendChild(card);
  });
}

function filterJobs(type) {
  document.querySelectorAll('.job-chip').forEach(btn => {
    btn.className = "job-chip bg-white text-slate-700 border border-slate-200 text-xs font-medium px-3.5 py-1.5 rounded-full whitespace-nowrap";
  });
  if (window.event && window.event.target) {
    window.event.target.className = "job-chip active bg-slate-900 text-white text-xs font-medium px-3.5 py-1.5 rounded-full whitespace-nowrap shadow-xs";
  }

  document.querySelectorAll('.job-card').forEach(card => {
    if (type === 'all' || card.dataset.type === type) {
      card.classList.remove('hidden');
    } else {
      card.classList.add('hidden');
    }
  });
}

// ==================== МОДАЛЬНЫЕ ОКНА И ФОРМЫ С ЗАПИСЬЮ В SUPABASE ====================

function showModalView(view) {
  const views = ['hub', 'masters', 'jobs', 'rent', 'helps'];
  views.forEach(v => {
    const el = document.getElementById('modalView-' + v);
    if (el) el.classList.toggle('hidden', v !== view);
  });

  const title = document.getElementById('modalTitle');
  const subTitle = document.getElementById('modalSubTitle');
  const backBtn = document.getElementById('modalBackBtn');

  if (!title || !subTitle || !backBtn) return;

  if (view === 'hub') {
    title.textContent = 'Разместить объявление';
    subTitle.textContent = 'Сообщество «Город Своих»';
    backBtn.classList.add('hidden');
  } else if (view === 'masters') {
    title.textContent = 'Анкета мастера';
    subTitle.textContent = 'Каталог услуг Гагры';
    backBtn.classList.toggle('hidden', currentRoute === 'masters');
  } else if (view === 'jobs') {
    title.textContent = 'Подать вакансию';
    subTitle.textContent = 'Биржа труда Гагры';
    backBtn.classList.toggle('hidden', currentRoute === 'jobs');
  } else if (view === 'rent') {
    title.textContent = 'Сдать жилье на долгий срок';
    subTitle.textContent = 'Аренда в Абхазии (от 1 мес.)';
    backBtn.classList.toggle('hidden', currentRoute === 'rent');
  } else if (view === 'helps') {
    title.textContent = 'Предложить доброе дело';
    subTitle.textContent = 'Город Своих помогает';
    backBtn.classList.toggle('hidden', currentRoute === 'helps');
  }
}

function openModal(target) {
  const modal = document.getElementById('publishModal');
  if (modal) modal.classList.remove('hidden');
  if (target && target !== 'portal') {
    showModalView(target);
  } else if (currentRoute !== 'hub') {
    showModalView(currentRoute);
  } else {
    showModalView('hub');
  }
}

function openContextModal() {
  openModal(currentRoute);
}

function closeModal() {
  const modal = document.getElementById('publishModal');
  if (modal) modal.classList.add('hidden');
}

function toggleCustomCategory(select) {
  const customInput = document.getElementById('mFormCustomCat');
  if (!customInput) return;
  if (select.value === 'CUSTOM') {
    customInput.classList.remove('hidden');
    customInput.required = true;
    customInput.focus();
  } else {
    customInput.classList.add('hidden');
    customInput.required = false;
  }
}

// Карта соответствия категорий формы и фильтров каталога
const CATEGORY_MAP = {
  '🧺 Ремонт техники': 'appliances',
  '🔧 Сантехника и электрика': 'engineering',
  '🎨 Отделка и ремонт': 'finish',
  '🏗 Строительство и сварка': 'construction',
  '🚗 Авто и транспорт': 'auto',
  '🌿 Быт и здоровье': 'lifestyle'
};

// 1. Форма мастеров: пишем в таблицу masters и открываем WhatsApp
async function submitMastersForm(e) {
  e.preventDefault();
  const catSelect = document.getElementById('mFormCategory').value;
  const customCat = document.getElementById('mFormCustomCat').value.trim();
  const finalCategory = (catSelect === 'CUSTOM') ? `Другое (${customCat})` : catSelect;
  const systemCategory = CATEGORY_MAP[catSelect] || 'custom';

  const name = document.getElementById('mFormName').value.trim();
  const phone = document.getElementById('mFormPhone').value.trim();
  const service = document.getElementById('mFormService').value.trim();
  const district = document.getElementById('mFormDistrict').value;
  const socialInput = document.getElementById('mFormSocial');
  const social = socialInput ? socialInput.value.trim() : '';

  // Отправка в Supabase (на модерацию)
  await insertToSupabase('masters', {
    name: name,
    phone: phone,
    category: systemCategory,
    category_title: finalCategory,
    service: service,
    city: district,
    social: social || null,
    is_approved: false
  });

  const socialBlock = social ? `\nСоцсети/Портфолио: ${social}` : '';

  const text = 
`#услуга
Специалист: ${name}
Телефон: ${phone}
Сфера: ${finalCategory}
Услуги: ${service}
Город: ${district}${socialBlock}
—
(Анкета с сайта «Город Своих»)`;

  const rinataPhone = "79263949118";
  closeModal();
  window.location.href = `https://api.whatsapp.com/send?phone=${rinataPhone}&text=` + encodeURIComponent(text);
}

// 2. Форма вакансий: пишем в таблицу jobs и открываем WhatsApp
async function submitJobsForm(e) {
  e.preventDefault();
  const type = document.getElementById('jFormType').value;
  const title = document.getElementById('jFormTitle').value.trim();
  const salary = document.getElementById('jFormSalary').value.trim();
  const desc = document.getElementById('jFormDesc').value.trim();
  const contact = document.getElementById('jFormContact').value.trim();
  const district = document.getElementById('jFormDistrict').value.trim();
  const phone = document.getElementById('jFormPhone').value.trim();

  // Отправка в Supabase (на модерацию)
  await insertToSupabase('jobs', {
    type: type,
    title: title,
    salary: salary,
    desc: desc,
    contact: contact,
    city: district,
    phone: phone,
    is_approved: false
  });

  const text = 
`${type}
Должность: ${title}
Оплата: ${salary}
Требования/Условия: ${desc}
Город: ${district}
Контакт: ${contact}, ${phone}
—
(Подано через портал «Город Своих»)`;

  const rinataPhone = "79263949118";
  closeModal();
  window.location.href = `https://api.whatsapp.com/send?phone=${rinataPhone}&text=` + encodeURIComponent(text);
}

// ==================== ФОТО И ФОРМА АРЕНДЫ ====================
let selectedRentPhotos = [];

// Обработка выбора файлов (до 5 шт.)
function handleRentPhotosSelected(input) {
  const files = Array.from(input.files || []);
  if (!files.length) return;

  const remainingSlots = 5 - selectedRentPhotos.length;
  if (remainingSlots <= 0) {
    alert("Можно прикрепить максимум 5 фотографий");
    input.value = '';
    return;
  }

  const toAdd = files.slice(0, remainingSlots);
  selectedRentPhotos.push(...toAdd);
  input.value = '';
  renderRentPhotoPreviews();
}

// Рендер миниатюр превью с кнопкой удаления
function renderRentPhotoPreviews() {
  const grid = document.getElementById('rPhotoPreviewGrid');
  const countEl = document.getElementById('rPhotoCount');
  if (!grid || !countEl) return;

  countEl.textContent = `${selectedRentPhotos.length} из 5`;

  if (selectedRentPhotos.length === 0) {
    grid.innerHTML = '';
    grid.classList.add('hidden');
    return;
  }

  grid.classList.remove('hidden');
  grid.innerHTML = selectedRentPhotos.map((file, idx) => {
    const previewUrl = URL.createObjectURL(file);
    return `
      <div class="relative w-full aspect-square rounded-lg overflow-hidden border border-slate-200 bg-slate-100 group">
        <img src="${previewUrl}" class="w-full h-full object-cover">
        <button type="button" onclick="removeRentPhoto(${idx})" 
                class="absolute top-1 right-1 bg-black/70 hover:bg-black text-white w-5 h-5 rounded-full flex items-center justify-center text-[10px] leading-none transition">
          ✕
        </button>
      </div>
    `;
  }).join('');
}

// Удаление фото из списка перед отправкой
function removeRentPhoto(idx) {
  selectedRentPhotos.splice(idx, 1);
  renderRentPhotoPreviews();
}

// Сжатие изображения в браузере через Canvas (до 1200px по ширине, JPEG 80%)
function compressRentPhoto(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = (e) => {
      const img = new Image();
      img.src = e.target.result;
      img.onload = () => {
        let width = img.width;
        let height = img.height;
        const maxDim = 1200;

        if (width > maxDim || height > maxDim) {
          if (width > height) {
            height = Math.round((height * maxDim) / width);
            width = maxDim;
          } else {
            width = Math.round((width * maxDim) / height);
            height = maxDim;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob((blob) => {
          if (blob) resolve(blob);
          else reject(new Error("Ошибка сжатия изображения"));
        }, 'image/jpeg', 0.8);
      };
      img.onerror = reject;
    };
    reader.onerror = reject;
  });
}

// Загрузка одного сжатого фото в бакет Supabase Storage (rent-photos)
async function uploadRentPhotoToStorage(blob, fileName) {
  if (typeof supabase !== 'undefined' && supabase.storage) {
    const { data, error } = await supabase.storage.from('rent-photos').upload(fileName, blob, {
      contentType: 'image/jpeg',
      upsert: false
    });
    if (error) throw error;
    const { data: pubData } = supabase.storage.from('rent-photos').getPublicUrl(fileName);
    return pubData.publicUrl;
  }

  const sUrl = (typeof SUPABASE_URL !== 'undefined') ? SUPABASE_URL : '';
  const sKey = (typeof SUPABASE_ANON_KEY !== 'undefined') ? SUPABASE_ANON_KEY : (typeof SUPABASE_KEY !== 'undefined' ? SUPABASE_KEY : '');

  const res = await fetch(`${sUrl}/storage/v1/object/rent-photos/${fileName}`, {
    method: 'POST',
    headers: {
      'apikey': sKey,
      'Authorization': `Bearer ${sKey}`,
      'Content-Type': 'image/jpeg'
    },
    body: blob
  });

  if (!res.ok) {
    throw new Error('Ошибка загрузки фото в хранилище');
  }
  return `${sUrl}/storage/v1/object/public/rent-photos/${fileName}`;
}

// 3. Форма аренды: сжатие фото, загрузка в rent-photos, запись в таблицу rent и открытие TG
async function submitRentForm(e) {
  e.preventDefault();
  const btn = document.getElementById('rFormSubmitBtn');
  const originalBtnText = btn ? btn.innerHTML : 'Отправить на добавление ↗';

  try {
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="animate-spin">⏳</span><span>Загрузка фото...</span>`;
    }

    const type = document.getElementById('rFormType').value;
    const price = document.getElementById('rFormPrice').value.trim();
    const district = document.getElementById('rFormDistrict').value.trim();
    const desc = document.getElementById('rFormDesc').value.trim();
    const phone = document.getElementById('rFormPhone').value.trim();

    // Загрузка фото в Supabase Storage
    const uploadedPhotoUrls = [];
    for (let i = 0; i < selectedRentPhotos.length; i++) {
      if (btn) {
        btn.innerHTML = `<span class="animate-spin">⏳</span><span>Загрузка фото ${i + 1}/${selectedRentPhotos.length}...</span>`;
      }
      const compressedBlob = await compressRentPhoto(selectedRentPhotos[i]);
      const uniqueName = `rent_${Date.now()}_${Math.random().toString(36).slice(2, 7)}.jpg`;
      const publicUrl = await uploadRentPhotoToStorage(compressedBlob, uniqueName);
      uploadedPhotoUrls.push(publicUrl);
    }

    if (btn) {
      btn.innerHTML = `<span>Сохранение заявки...</span>`;
    }

    // Отправка в таблицу rent в Supabase
    await insertToSupabase('rent', {
      title: type,
      price: price,
      district: district,
      desc: desc,
      phone: phone,
      photos: uploadedPhotoUrls,
      is_approved: false
    });

    const photoInfo = uploadedPhotoUrls.length > 0 
      ? `\nФотографий прикреплено: ${uploadedPhotoUrls.length} шт.` 
      : '';

    const text = 
`Здравствуйте, Рината! Хочу сдать жилье на долгий срок:
Объект: ${type}
Цена: ${price} / месяц
Город: ${district}
Описание: ${desc}
Телефон: ${phone}${photoInfo}`;

    selectedRentPhotos = [];
    renderRentPhotoPreviews();
    closeModal();
    window.open(`https://t.me/rinata_tibay?text=` + encodeURIComponent(text), '_blank');

  } catch (err) {
    console.error('Ошибка отправки формы аренды:', err);
    alert('Не удалось отправить форму с фото: ' + (err.message || 'попробуйте ещё раз'));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalBtnText;
    }
  }
}

// 4. Форма инициатив взаимовыручки: пишем в таблицу helps и открываем WhatsApp
async function submitHelpsForm(e) {
  e.preventDefault();
  const type = document.getElementById('hFormType').value;
  const title = document.getElementById('hFormTitle').value.trim();
  const desc = document.getElementById('hFormDesc').value.trim();
  const contact = document.getElementById('hFormContact').value.trim();
  const district = document.getElementById('hFormDistrict').value;
  const phone = document.getElementById('hFormPhone').value.trim();

  let hashtag = '#городпомогает';
  let badge = '🤝 Инициатива';
  let cleanType = 'care';

  if (type.includes('животным')) {
    hashtag = '#помощь_животным';
    badge = '🐾 Помощь животным';
    cleanType = 'animals';
  } else if (type.includes('Экология')) {
    hashtag = '#эко_субботник';
    badge = '🌿 Эко-десант';
    cleanType = 'eco';
  } else if (type.includes('Взаимовыручка')) {
    hashtag = '#взаимовыручка';
    badge = '🤝 Взаимовыручка';
    cleanType = 'care';
  } else if (type.includes('Социальное')) {
    hashtag = '#соц_мероприятие';
    badge = '🎈 Мероприятие';
    cleanType = 'events';
  }

  // Отправка в Supabase (на модерацию)
  await insertToSupabase('helps', {
    type: cleanType,
    badge: badge,
    title: title,
    desc: desc,
    city: district,
    contact: contact,
    phone: phone,
    status: 'Актуально',
    is_approved: false
  });

  const text = 
`${hashtag}
Заголовок: ${title}
Описание: ${desc}
Город: ${district}
Связь: ${contact}, ${phone}
—
(Заявка с сайта «Город Своих»)`;

  const rinataPhone = "79263949118";
  closeModal();
  window.location.href = `https://api.whatsapp.com/send?phone=${rinataPhone}&text=` + encodeURIComponent(text);
}

// ==================== ИНИЦИАЛИЗАЦИЯ И СЛУШАТЕЛИ ====================

document.addEventListener('DOMContentLoaded', () => {
  const sIn = document.getElementById('searchInput');
  if (sIn) {
    sIn.addEventListener('input', (e) => {
      const cBtn = document.getElementById('clearSearch');
      if (cBtn) cBtn.classList.toggle('hidden', !e.target.value);
      renderMasters();
    });
  }

  const cSearch = document.getElementById('clearSearch');
  if (cSearch) {
    cSearch.addEventListener('click', () => {
      const input = document.getElementById('searchInput');
      if (input) input.value = '';
      cSearch.classList.add('hidden');
      renderMasters();
    });
  }

  document.querySelectorAll('.macro-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.macro-btn').forEach(b => {
        b.className = 'macro-btn bg-white text-slate-700 border border-slate-200 text-xs font-medium px-3 py-1.5 rounded-full whitespace-nowrap';
      });
      btn.className = 'macro-btn active bg-slate-900 text-white text-xs font-medium px-3.5 py-1.5 rounded-full whitespace-nowrap shadow-xs';
      activeCategory = btn.dataset.cat;
      activeSubcategory = 'all';
      renderSubBar();
      renderMasters();
    });
  });

  applyRoute();
  loadData();
});

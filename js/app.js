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

let masters = [];
let helpsData = [];
let currentRoute = 'hub';
let activeCategory = 'all';
let activeSubcategory = 'all';

// ==================== РОУТИНГ И НАВИГАЦИЯ ====================

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
      titleEl.textContent = 'Долгосрочная аренда';
      actionBtn.className = "text-xs font-bold text-sky-700 bg-sky-50 px-2.5 py-1.5 rounded-xl border border-sky-200 hover:bg-sky-100 transition";
      actionBtn.textContent = '+ Сдать жилье';
    } else if (currentRoute === 'helps') {
      titleEl.textContent = 'Город Своих помогает';
      actionBtn.className = "text-xs font-bold text-teal-800 bg-teal-50 px-2.5 py-1.5 rounded-xl border border-teal-200 hover:bg-teal-100 transition";
      actionBtn.textContent = '+ Инициатива';
    }
  }

  window.scrollTo(0, 0);
}

window.addEventListener('hashchange', applyRoute);

// ==================== ЗАГРУЗКА И ПАРСИНГ ДАННЫХ ====================

async function loadData() {
  // 1. Каталог мастеров
  try {
    const response = await fetch('data/masters.json?v=' + Date.now());
    if (response.ok) {
      masters = await response.json();

      const leader = masters.find(m => m.is_leader) || masters.find(m => m.name && m.name.includes("Владимир"));
      if (leader) {
        const lName = document.getElementById('hubLeaderName');
        const lServ = document.getElementById('hubLeaderService');
        const lDesc = document.getElementById('hubLeaderDesc');
        const lLink = document.getElementById('hubLeaderWaLink');
        if (lName) lName.textContent = leader.name;
        if (lServ) lServ.textContent = leader.subcategory_title || leader.category_title;
        if (lDesc) lDesc.textContent = leader.service;
        if (lLink) {
          const cleanPhone = (leader.phone || '').replace(/[^0-9]/g, '');
          lLink.href = `https://wa.me/${cleanPhone}?text=` + encodeURIComponent(`Здравствуйте, ${leader.name}! Увидел ваш закреп лидера недели на портале "Город Своих".`);
        }
      }
      renderMasters();
    }
  } catch (err) {
    console.error('Ошибка загрузки мастеров:', err);
  }

  // 2. Чат инициатив взаимовыручки
  try {
    const chatRes = await fetch('data/helps_chat.txt?v=' + Date.now());
    if (chatRes.ok) {
      const chatText = await chatRes.text();
      helpsData = parseHelpsFromChat(chatText);
    }
  } catch (e) {
    console.warn('Экспорт чата helps_chat.txt не найден или пуст.');
  }
  renderHelps('all');
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

// ==================== РЕНДЕРИНГ ====================

function renderHelps(filterType = 'all') {
  const container = document.getElementById('helpsContainer');
  if (!container) return;
  container.innerHTML = '';

  const filtered = helpsData.filter(h => filterType === 'all' || h.type === filterType);
  filtered.forEach(item => {
    const cleanPhone = (item.phone || '').replace(/[^0-9]/g, '');
    const linkHref = cleanPhone 
      ? `https://api.whatsapp.com/send?phone=${cleanPhone}&text=` + encodeURIComponent(`Здравствуйте! Пишу по поводу инициативы "${item.title}" на портале Город Своих.`)
      : (item.chat_link || 'https://chat.whatsapp.com/GnHSLd8VWaxGboukz9s3FI');

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
        <span class="text-slate-500 font-medium">${item.city} • ${item.contact}</span>
        <a href="${linkHref}" target="_blank" 
           class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-3 py-1.5 rounded-xl transition">
          ${item.btn_text || 'Откликнуться'}
        </a>
      </div>
    `;
    container.appendChild(card);
  });
}

function filterHelps(type) {
  document.querySelectorAll('.help-chip').forEach(btn => {
    btn.className = "help-chip bg-white text-slate-700 border border-slate-200 text-xs font-medium px-3.5 py-1.5 rounded-full whitespace-nowrap shadow-xs";
  });
  if (window.event && window.event.target) {
    window.event.target.className = "help-chip active bg-slate-900 text-white text-xs font-medium px-3.5 py-1.5 rounded-full whitespace-nowrap shadow-xs";
  }
  renderHelps(type);
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

  return searchWords.every(word => {
    const stem = word.length > 4 ? word.substring(0, word.length - 2) : word;
    return fullContext.includes(stem);
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
    const matchesCat = (activeCategory === 'all') || (m.category === activeCategory);
    const matchesSub = (activeSubcategory === 'all') || (m.subcategory === activeSubcategory);
    const matchesSearch = matchesQuery(m, searchWords);
    return matchesCat && matchesSub && matchesSearch;
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

    const card = document.createElement('div');
    card.className = "bg-white rounded-3xl p-4 border border-slate-200/90 shadow-xs hover:border-slate-300 transition";
    card.innerHTML = `
      <div class="flex items-start justify-between gap-2 mb-1.5">
        <div>
          <span class="text-[10px] font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md">
            ${m.subcategory_title || m.category_title}
          </span>
          <h3 class="text-base font-bold text-slate-900 leading-snug mt-1">${m.name}</h3>
        </div>
        ${m.starred ? `
          <span class="text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full whitespace-nowrap">
            ⭐ Рекомендуют
          </span>
        ` : `
          <span class="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full whitespace-nowrap">
            ✓ Проверен
          </span>
        `}
      </div>
      
      <p class="text-xs text-slate-600 mb-2 leading-relaxed">${m.service}</p>
      <p class="text-[11px] font-mono font-medium text-slate-500 mb-3">${m.phone}</p>

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

// ==================== МОДАЛЬНЫЕ ОКНА И ФОРМЫ ====================

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

function submitMastersForm(e) {
  e.preventDefault();
  const catSelect = document.getElementById('mFormCategory').value;
  const customCat = document.getElementById('mFormCustomCat').value.trim();
  const finalCategory = (catSelect === 'CUSTOM') ? `Другое (${customCat})` : catSelect;

  const name = document.getElementById('mFormName').value.trim();
  const phone = document.getElementById('mFormPhone').value.trim();
  const service = document.getElementById('mFormService').value.trim();
  const district = document.getElementById('mFormDistrict').value;

  const text = 
`#услуга
Специалист: ${name}
Телефон: ${phone}
Сфера: ${finalCategory}
Услуги: ${service}
Город: ${district}
—
(Анкета с сайта «Город Своих»)`;

  const rinataPhone = "79263949118";
  closeModal();
  window.location.href = `https://api.whatsapp.com/send?phone=${rinataPhone}&text=` + encodeURIComponent(text);
}

function submitJobsForm(e) {
  e.preventDefault();
  const type = document.getElementById('jFormType').value;
  const title = document.getElementById('jFormTitle').value.trim();
  const salary = document.getElementById('jFormSalary').value.trim();
  const desc = document.getElementById('jFormDesc').value.trim();
  const contact = document.getElementById('jFormContact').value.trim();
  const district = document.getElementById('jFormDistrict').value.trim();
  const phone = document.getElementById('jFormPhone').value.trim();

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

function submitRentForm(e) {
  e.preventDefault();
  const type = document.getElementById('rFormType').value;
  const price = document.getElementById('rFormPrice').value.trim();
  const district = document.getElementById('rFormDistrict').value.trim();
  const desc = document.getElementById('rFormDesc').value.trim();
  const phone = document.getElementById('rFormPhone').value.trim();

  const text = 
`Здравствуйте, Рината! Хочу сдать жилье на долгий срок:
Объект: ${type}
Цена: ${price} / месяц
Город: ${district}
Описание: ${desc}
Телефон: ${phone}`;

  closeModal();
  window.open(`https://t.me/rinata_tibay?text=` + encodeURIComponent(text), '_blank');
}

function submitHelpsForm(e) {
  e.preventDefault();
  const type = document.getElementById('hFormType').value;
  const title = document.getElementById('hFormTitle').value.trim();
  const desc = document.getElementById('hFormDesc').value.trim();
  const contact = document.getElementById('hFormContact').value.trim();
  const district = document.getElementById('hFormDistrict').value;
  const phone = document.getElementById('hFormPhone').value.trim();

  let hashtag = '#городпомогает';
  if (type.includes('животным')) hashtag = '#помощь_животным';
  else if (type.includes('Экология')) hashtag = '#эко_субботник';
  else if (type.includes('Взаимовыручка')) hashtag = '#взаимовыручка';
  else if (type.includes('Социальное')) hashtag = '#соц_мероприятие';

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

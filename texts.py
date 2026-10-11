"""Все тексты бота на трёх языках. Чтобы изменить текст, правится только этот файл."""

LANGS = {"az": "🇦🇿 Azərbaycanca", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
DEFAULT_LANG = "az"

_CHOOSE = "🌐 Dil seçin / Выберите язык / Choose language"

T: dict[str, dict[str, str]] = {
    "az": {
        "choose_lang": _CHOOSE,
        "welcome": "👋 Salam! Mən <b>Azərbaycan Texnologiya Universiteti</b>nin rəsmi məlumat botuyam.\n\nAşağıdakı menyudan istədiyiniz bölməni seçin.",
        "menu_title": "📋 Əsas menyu",
        "btn_faculties": "🏛 Fakültələr",
        "btn_admission": "🎓 Qəbul",
        "btn_news": "📰 Xəbərlər",
        "btn_ann": "📢 Elanlar",
        "btn_contacts": "📞 Əlaqə",
        "btn_cabinet": "👤 Tələbə kabineti",
        "btn_lang": "🌐 Dil",
        "btn_cancel": "❌ Ləğv et",
        "btn_logout": "🚪 Çıxış",
        "btn_back": "⬅️ Əsas menyu",
        "btn_back_inline": "⬅️ Geri",
        "btn_site": "🌐 Saytda aç",
        "btn_all_news": "📰 Bütün xəbərlər",
        "btn_all_ann": "📢 Bütün elanlar",
        "btn_lms": "💻 LMS sisteminə giriş",
        "lnk_admission": "📋 Qəbul qaydaları",
        "lnk_fees": "💰 Təhsil haqqı və ixtisaslar",
        "lnk_schedule": "🗓 Dərs cədvəlləri",
        "lnk_calendar": "📆 Akademik təqvim",
        "lnk_intl": "🌍 Əcnəbi tələbə qəbulu",
        "faculties_title": "🏛 <b>Fakültələr</b>\n\nƏtraflı məlumat üçün fakültəni seçin:",
        "faculty_card": "🏛 <b>{name}</b>\n\n👤 Dekan: {dean}\n📧 {email}\n📞 {phone}",
        "admission": "🎓 <b>Qəbul və ixtisaslar</b>\n\nUniversitetdə <b>27</b> bakalavr və <b>40</b> magistr ixtisası üzrə təhsil verilir.\n\nƏtraflı məlumat üçün rəsmi səhifələrə keçin:",
        "news_title": "📰 <b>Son xəbərlər</b>\n",
        "ann_title": "📢 <b>Son elanlar</b>\n",
        "contacts": "📞 <b>Əlaqə</b>\n\n📍 {address}\n☎️ {phone}\n📧 {email}\n🌐 {site}",
        "cabinet_intro": "👤 <b>Tələbə kabineti</b>\n\n⚠️ <i>Demo rejimi: real tələbə məlumatları qoşulmayıb, test hesabından istifadə olunur.</i>\n\nTest giriş: FİN <code>{fin}</code>, parol <code>{password}</code>\n\nFİN kodunuzu daxil edin (7 simvol):",
        "ask_password": "🔑 Parolu daxil edin. Təhlükəsizlik üçün mesaj dərhal silinəcək.",
        "bad_fin": "❗️ FİN 7 simvoldan (latın hərfləri və rəqəmlər) ibarət olmalıdır. Yenidən cəhd edin.",
        "wrong_creds": "❌ FİN və ya parol yanlışdır. Qalan cəhd sayı: {left}.\n\nFİN kodunu yenidən daxil edin:",
        "locked": "⛔️ Çox sayda uğursuz cəhd. {minutes} dəq. sonra yenidən cəhd edin.",
        "profile": "👤 <b>{name}</b>\n\n🏛 {faculty}\n📘 {specialty}\n🎓 {course}-ci kurs · Qrup: {group}\n📊 GPA: <b>{gpa}</b>\n\n<b>Qiymətlər:</b>\n{grades}\n\n⚠️ <i>Bunlar demo məlumatlardır.</i>",
        "logged_out": "🚪 Kabinetdən çıxdınız.",
        "cancelled": "Əməliyyat ləğv edildi.",
        "unknown": "Zəhmət olmasa menyudan bölmə seçin 👇",
        "only_text": "Zəhmət olmasa mətn göndərin.",
    },
    "ru": {
        "choose_lang": _CHOOSE,
        "welcome": "👋 Здравствуйте! Я официальный информационный бот <b>Азербайджанского технологического университета</b>.\n\nВыберите нужный раздел в меню ниже.",
        "menu_title": "📋 Главное меню",
        "btn_faculties": "🏛 Факультеты",
        "btn_admission": "🎓 Поступление",
        "btn_news": "📰 Новости",
        "btn_ann": "📢 Объявления",
        "btn_contacts": "📞 Контакты",
        "btn_cabinet": "👤 Кабинет студента",
        "btn_lang": "🌐 Язык",
        "btn_cancel": "❌ Отмена",
        "btn_logout": "🚪 Выйти",
        "btn_back": "⬅️ Главное меню",
        "btn_back_inline": "⬅️ Назад",
        "btn_site": "🌐 Открыть на сайте",
        "btn_all_news": "📰 Все новости",
        "btn_all_ann": "📢 Все объявления",
        "btn_lms": "💻 Вход в LMS",
        "lnk_admission": "📋 Правила приёма",
        "lnk_fees": "💰 Стоимость обучения и специальности",
        "lnk_schedule": "🗓 Расписание занятий",
        "lnk_calendar": "📆 Академический календарь",
        "lnk_intl": "🌍 Приём иностранных студентов",
        "faculties_title": "🏛 <b>Факультеты</b>\n\nВыберите факультет:",
        "faculty_card": "🏛 <b>{name}</b>\n\n👤 Декан: {dean}\n📧 {email}\n📞 {phone}",
        "admission": "🎓 <b>Поступление и специальности</b>\n\nВ университете обучение ведётся по <b>27</b> бакалаврским и <b>40</b> магистерским специальностям.\n\nПодробности на официальных страницах:",
        "news_title": "📰 <b>Последние новости</b>\n",
        "ann_title": "📢 <b>Последние объявления</b>\n",
        "contacts": "📞 <b>Контакты</b>\n\n📍 {address}\n☎️ {phone}\n📧 {email}\n🌐 {site}",
        "cabinet_intro": "👤 <b>Кабинет студента</b>\n\n⚠️ <i>Демо-режим: реальные данные студентов не подключены, используется тестовый аккаунт.</i>\n\nТестовый вход: FİN <code>{fin}</code>, пароль <code>{password}</code>\n\nВведите ваш FİN (7 символов):",
        "ask_password": "🔑 Введите пароль. Сообщение будет сразу удалено в целях безопасности.",
        "bad_fin": "❗️ FİN должен состоять из 7 символов (латинские буквы и цифры). Попробуйте ещё раз.",
        "wrong_creds": "❌ Неверный FİN или пароль. Осталось попыток: {left}.\n\nВведите FİN ещё раз:",
        "locked": "⛔️ Слишком много неудачных попыток. Повторите через {minutes} мин.",
        "profile": "👤 <b>{name}</b>\n\n🏛 {faculty}\n📘 {specialty}\n🎓 {course} курс · Группа: {group}\n📊 GPA: <b>{gpa}</b>\n\n<b>Оценки:</b>\n{grades}\n\n⚠️ <i>Это демо-данные.</i>",
        "logged_out": "🚪 Вы вышли из кабинета.",
        "cancelled": "Действие отменено.",
        "unknown": "Пожалуйста, выберите раздел в меню 👇",
        "only_text": "Пожалуйста, отправьте текстовое сообщение.",
    },
    "en": {
        "choose_lang": _CHOOSE,
        "welcome": "👋 Hello! I am the official information bot of the <b>Azerbaijan Technology University</b>.\n\nChoose a section from the menu below.",
        "menu_title": "📋 Main menu",
        "btn_faculties": "🏛 Faculties",
        "btn_admission": "🎓 Admission",
        "btn_news": "📰 News",
        "btn_ann": "📢 Announcements",
        "btn_contacts": "📞 Contacts",
        "btn_cabinet": "👤 Student account",
        "btn_lang": "🌐 Language",
        "btn_cancel": "❌ Cancel",
        "btn_logout": "🚪 Log out",
        "btn_back": "⬅️ Main menu",
        "btn_back_inline": "⬅️ Back",
        "btn_site": "🌐 Open on website",
        "btn_all_news": "📰 All news",
        "btn_all_ann": "📢 All announcements",
        "btn_lms": "💻 LMS login",
        "lnk_admission": "📋 Admission rules",
        "lnk_fees": "💰 Tuition fees and programs",
        "lnk_schedule": "🗓 Class schedules",
        "lnk_calendar": "📆 Academic calendar",
        "lnk_intl": "🌍 International admission",
        "faculties_title": "🏛 <b>Faculties</b>\n\nChoose a faculty:",
        "faculty_card": "🏛 <b>{name}</b>\n\n👤 Dean: {dean}\n📧 {email}\n📞 {phone}",
        "admission": "🎓 <b>Admission and programs</b>\n\nThe university offers <b>27</b> bachelor's and <b>40</b> master's programs.\n\nSee the official pages for details:",
        "news_title": "📰 <b>Latest news</b>\n",
        "ann_title": "📢 <b>Latest announcements</b>\n",
        "contacts": "📞 <b>Contacts</b>\n\n📍 {address}\n☎️ {phone}\n📧 {email}\n🌐 {site}",
        "cabinet_intro": "👤 <b>Student account</b>\n\n⚠️ <i>Demo mode: real student data is not connected, a test account is used.</i>\n\nTest login: FİN <code>{fin}</code>, password <code>{password}</code>\n\nEnter your FİN (7 characters):",
        "ask_password": "🔑 Enter your password. The message will be deleted immediately for security.",
        "bad_fin": "❗️ FİN must be 7 characters (Latin letters and digits). Please try again.",
        "wrong_creds": "❌ Wrong FİN or password. Attempts left: {left}.\n\nEnter your FİN again:",
        "locked": "⛔️ Too many failed attempts. Try again in {minutes} min.",
        "profile": "👤 <b>{name}</b>\n\n🏛 {faculty}\n📘 {specialty}\n🎓 Year {course} · Group: {group}\n📊 GPA: <b>{gpa}</b>\n\n<b>Grades:</b>\n{grades}\n\n⚠️ <i>This is demo data.</i>",
        "logged_out": "🚪 You have logged out.",
        "cancelled": "Cancelled.",
        "unknown": "Please choose a section from the menu 👇",
        "only_text": "Please send a text message.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    text = T.get(lang, T[DEFAULT_LANG]).get(key) or T[DEFAULT_LANG][key]
    return text.format(**kwargs) if kwargs else text


# ---------- Расписание ----------

_EXTRA = {
    "az": {
        "btn_schedule": "🗓 Dərs cədvəli",
        "btn_myschedule": "📅 Mənim cədvəlim",
        "btn_today": "📅 Bu gün",
        "btn_week": "📆 Bütün həftə",
        "schedule_title": "🗓 <b>Dərs cədvəli</b>\n\nFakültəni seçin:",
        "schedule_pick": "🗓 <b>{faculty}</b>\n\nCədvəli seçin:",
        "schedule_empty": "🗓 <b>{faculty}</b>\n\nBu fakültə üçün cədvəl hələ yüklənməyib. Zəhmət olmasa sonra yoxlayın.",
        "schedule_file_error": "⚠️ Fayl hazırda əlçatan deyil. Zəhmət olmasa universitet administrasiyasına müraciət edin.",
        "myschedule_today": "📅 <b>Bu gün</b> — {day}\n\n{lessons}\n\n⚠️ <i>Bunlar demo məlumatlardır.</i>",
        "myschedule_week": "📆 <b>Həftəlik cədvəl</b>\n\n{lessons}\n\n⚠️ <i>Bunlar demo məlumatlardır.</i>",
        "myschedule_none": "Bu gün dərs yoxdur 🎉",
        "myschedule_free": "dərs yoxdur",
        "session_expired": "Sessiya başa çatıb. Zəhmət olmasa kabinetə yenidən daxil olun.",
    },
    "ru": {
        "btn_schedule": "🗓 Расписание",
        "btn_myschedule": "📅 Моё расписание",
        "btn_today": "📅 Сегодня",
        "btn_week": "📆 Вся неделя",
        "schedule_title": "🗓 <b>Расписание занятий</b>\n\nВыберите факультет:",
        "schedule_pick": "🗓 <b>{faculty}</b>\n\nВыберите расписание:",
        "schedule_empty": "🗓 <b>{faculty}</b>\n\nРасписание для этого факультета ещё не загружено. Загляните позже.",
        "schedule_file_error": "⚠️ Файл сейчас недоступен. Пожалуйста, обратитесь в администрацию университета.",
        "myschedule_today": "📅 <b>Сегодня</b> — {day}\n\n{lessons}\n\n⚠️ <i>Это демо-данные.</i>",
        "myschedule_week": "📆 <b>Расписание на неделю</b>\n\n{lessons}\n\n⚠️ <i>Это демо-данные.</i>",
        "myschedule_none": "Сегодня занятий нет 🎉",
        "myschedule_free": "занятий нет",
        "session_expired": "Сессия истекла. Пожалуйста, войдите в кабинет заново.",
    },
    "en": {
        "btn_schedule": "🗓 Schedule",
        "btn_myschedule": "📅 My schedule",
        "btn_today": "📅 Today",
        "btn_week": "📆 Whole week",
        "schedule_title": "🗓 <b>Class schedule</b>\n\nChoose a faculty:",
        "schedule_pick": "🗓 <b>{faculty}</b>\n\nChoose a schedule:",
        "schedule_empty": "🗓 <b>{faculty}</b>\n\nNo schedule has been uploaded for this faculty yet. Please check back later.",
        "schedule_file_error": "⚠️ The file is unavailable right now. Please contact the university administration.",
        "myschedule_today": "📅 <b>Today</b> — {day}\n\n{lessons}\n\n⚠️ <i>This is demo data.</i>",
        "myschedule_week": "📆 <b>Weekly schedule</b>\n\n{lessons}\n\n⚠️ <i>This is demo data.</i>",
        "myschedule_none": "No classes today 🎉",
        "myschedule_free": "no classes",
        "session_expired": "Your session has expired. Please log in to your account again.",
    },
}
for _lang, _extra in _EXTRA.items():
    T[_lang].update(_extra)

WEEKDAYS: dict[str, list[str]] = {
    "az": ["Bazar ertəsi", "Çərşənbə axşamı", "Çərşənbə", "Cümə axşamı", "Cümə", "Şənbə", "Bazar"],
    "ru": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}


# ---------- Служебные таблицы для статистики и фильтров ----------

SECTION_BUTTONS = (
    "btn_faculties",
    "btn_admission",
    "btn_news",
    "btn_ann",
    "btn_schedule",
    "btn_contacts",
    "btn_cabinet",
    "btn_myschedule",
    "btn_lang",
)
# текст кнопки (на любом языке) -> имя раздела, например "news"
BUTTON_TO_SECTION: dict[str, str] = {
    T[lang][key]: key[len("btn_"):] for key in SECTION_BUTTONS for lang in T
}
# все кнопки нижней клавиатуры (чтобы не принимать их за обычный ввод)
ALL_REPLY_BUTTONS: set[str] = set(BUTTON_TO_SECTION) | {
    T[lang][key] for lang in T for key in ("btn_back", "btn_cancel", "btn_logout")
}

"""Данные университета. Источник: официальный сайт https://atu.edu.az/ (проверено 09.10.2026).

В боевой версии эти данные хранятся в БД и редактируются через админ-панель.
"""

SITE = "https://atu.edu.az"
LMS_URL = "https://atu.kodera.az"

CONTACT = {
    "address": "Gəncə ş. AZ2011 Şah İsmayıl Xətai prospekti 103",
    "phone": "(+994 22) 268-08-81",
    "email": "info@atu.edu.az",
    "site": "www.atu.edu.az",
    "lat": 40.68856853905134,
    "lon": 46.38421577501259,
}

FACULTIES = [
    {
        "slug": "neqliyyat-ve-senaye-texnologiyalari",
        "name": {
            "az": "Nəqliyyat və sənaye texnologiyaları",
            "ru": "Транспортные и промышленные технологии",
            "en": "Transport and Industrial Technologies",
        },
        "dean": "Dos. Əliyev Şakir Hüseynqulu oğlu",
        "email": "sh.eliyev@atu.edu.az",
        "phone": "(+994 22) 268 07 09",
    },
    {
        "slug": "qida-muhendisliyi",
        "name": {"az": "Qida mühəndisliyi", "ru": "Пищевая инженерия", "en": "Food Engineering"},
        "dean": "Dos. İsmayılov Mehman Telman oğlu",
        "email": "m.ismayilov@atu.edu.az",
        "phone": "(+994 22) 268 08 42",
    },
    {
        "slug": "reqemsal-texnologiyalar",
        "name": {"az": "Rəqəmsal texnologiyalar", "ru": "Цифровые технологии", "en": "Digital Technologies"},
        "dean": "Dos. Hacıyev Rövşən Mustafa oğlu",
        "email": "r.hajiyev@atu.edu.az",
        "phone": "(+994 22) 268 63 02",
    },
    {
        "slug": "iqtisadiyyat-ve-idareetme",
        "name": {"az": "İqtisadiyyat və idarəetmə", "ru": "Экономика и управление", "en": "Economics and Management"},
        "dean": "Dos. Kərimov Fazil Cəmil oğlu",
        "email": "f.kerimov@atu.edu.az",
        "phone": "(+994 22) 268 39 98",
    },
    {
        "slug": "turizm",
        "name": {"az": "Turizm", "ru": "Туризм", "en": "Tourism"},
        "dean": "Hümbətov Yusif Əbülfət oğlu",
        "email": "y.humbetov@atu.edu.az",
        "phone": "(+994 22) 111111",
    },
]

NEWS = [
    {"date": "2026-10-08", "title": "🚀 Rektor “Startapçı tələbə” təqaüd proqramının ilk qalibləri ilə görüşüb", "url": f"{SITE}/xeber/1547"},
    {"date": "2026-10-07", "title": "Azərbaycan dövlətçiliyinin yeni inkişaf mərhələsi və YAP-ın siyasi-strateji prioritetləri", "url": f"{SITE}/xeber/1546"},
    {"date": "2026-10-05", "title": "🌱 ATU-da yaşıl enerji və ekoloji dayanıqlıqla bağlı tədbirlər planı müzakirə olunub", "url": f"{SITE}/xeber/1545"},
    {"date": "2026-10-01", "title": "Günəş və külək enerjisi tələbələrin praktiki təcrübəsinə çevrilir", "url": f"{SITE}/xeber/1542"},
]

ANNOUNCEMENTS = [
    {"date": "2026-10-08", "title": "ATU növbəti tyutor kurslarına start verir", "url": f"{SITE}/elan/246"},
    {"date": "2026-10-06", "title": "Azərbaycan Texnologiya Universitetində Respublika Elmi-Praktik Konfransı keçiriləcəkdir", "url": f"{SITE}/elan/245"},
    {"date": "2026-08-24", "title": "Magistratura üzrə ikinci tur ixtisası seçiminə start verildi", "url": f"{SITE}/elan/243"},
]

LINKS = {
    "lnk_admission": f"{SITE}/sovbe/qebul-qaydalari",
    "lnk_fees": f"{SITE}/sovbe/tehsil-haqqi-ve-ixtisaslar",
    "lnk_schedule": f"{SITE}/sovbe/ders-cedvelleri",
    "lnk_calendar": f"{SITE}/sovbe/akademik-teqvim",
    "lnk_intl": f"{SITE}/sovbe/ecnebi-telebe-qebulu",
}

NEWS_ALL_URL = f"{SITE}/xeberler/1"
ANN_ALL_URL = f"{SITE}/elanlar/1"

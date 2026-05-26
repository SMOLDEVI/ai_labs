import sqlite3
import os

def create_massive_knowledge_base():
    db_path = "linux_distributives.kb"
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # --- СОЗДАНИЕ ТАБЛИЦ ---
    cursor.execute("CREATE TABLE sections (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
    cursor.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
    cursor.execute("CREATE TABLE properties (id INTEGER PRIMARY KEY, event_id INTEGER, name TEXT)")
    cursor.execute("""
        CREATE TABLE gradations (
            id INTEGER PRIMARY KEY, property_id INTEGER, name TEXT,
            g_type TEXT DEFAULT 'text', num1 REAL, num2 REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE relations (
            id INTEGER PRIMARY KEY, section_id INTEGER, gradation_id INTEGER, 
            weight REAL, UNIQUE(section_id, gradation_id)
        )
    """)

    # --- 30 ДИСТРИБУТИВОВ ---
    distros = [
        # Оригинальные 10
        "Ubuntu",           # 1. Новичок, дом/офис
        "Linux Mint",       # 2. Новичок, самый дружелюбный
        "Debian",           # 3. Сервер, стабильность
        "Arch Linux",       # 4. Энтузиаст, rolling
        "Gentoo",           # 5. Гуру, компиляция
        "Fedora",           # 6. Разработчик, свежие пакеты
        "Manjaro",          # 7. Геймер, rolling с GUI
        "Kali Linux",       # 8. Кибербезопасность
        "CentOS Stream",    # 9. Корпоративный сервер
        "Alpine Linux",     # 10. Микроконтейнеры, роутеры
        # Новые 20
        "openSUSE Tumbleweed",  # 11. Разработчик, rolling, KDE
        "openSUSE Leap",        # 12. Корпоративный, стабильный
        "Pop!_OS",              # 13. Геймер, NVIDIA из коробки
        "Elementary OS",        # 14. Новичок, дизайн как macOS
        "Zorin OS",             # 15. Новичок, замена Windows
        "MX Linux",             # 16. Слабое железо, стабильность
        "Tails",                # 17. Анонимность, приватность
        "Whonix",               # 18. Максимальная анонимность
        "Parrot OS",            # 19. Кибербезопасность + приватность
        "Slackware",            # 20. Олдскул, UNIX-философия
        "Void Linux",           # 21. Легковесный, runit, rolling
        "NixOS",                # 22. Декларативная конфигурация
        "Qubes OS",             # 23. Безопасность через изоляцию VM
        "Raspberry Pi OS",      # 24. Одноплатники, IoT
        "Ubuntu Server",        # 25. Облачные серверы, DevOps
        "Rocky Linux",          # 26. Замена CentOS, Enterprise
        "Lubuntu",              # 27. Очень старое железо, LXQt
        "Kali Purple",          # 28. Защитная безопасность (Blue Team)
        "Garuda Linux",         # 29. Геймер, Arch-based, красивый
        "EndeavourOS",          # 30. Arch с удобной установкой
    ]

    for d in distros:
        cursor.execute("INSERT INTO sections (name) VALUES (?)", (d,))

    cursor.execute("SELECT id, name FROM sections")
    d_ids = {name: sid for sid, name in cursor.fetchall()}

    def add_prop(event_name, prop_name):
        cursor.execute("INSERT OR IGNORE INTO events (name) VALUES (?)", (event_name,))
        cursor.execute("SELECT id FROM events WHERE name = ?", (event_name,))
        ev_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO properties (event_id, name) VALUES (?, ?)",
            (ev_id, prop_name)
        )
        return cursor.lastrowid

    # --- 10 СВОЙСТВ (те же категории) ---
    p_usage = add_prop("1. Целевое назначение",       "Главная сфера применения")
    p_exp   = add_prop("2. Уровень пользователя",     "Требуемый опыт работы")
    p_ram   = add_prop("3. Требования к ОЗУ",         "ОЗУ для комфортной работы (ГБ)")
    p_disk  = add_prop("4. Требования к накопителю",  "Мин. место на диске (ГБ)")
    p_rel   = add_prop("5. Жизненный цикл",           "Цикл обновлений (мес.)")
    p_gui   = add_prop("6. Графическая оболочка",     'GUI "из коробки"')
    p_inst  = add_prop("7. Процесс установки",        "Среднее время установки (мин.)")
    p_game  = add_prop("8. Игры и Мультимедиа",       "Готовность к Steam / Играм")
    p_prop  = add_prop("9. Драйвера и Кодеки",        "Проприетарное ПО в комплекте")
    p_dev   = add_prop("10. Разработка ПО",           "Самые свежие компиляторы/пакеты")

    g_ids = {}

    def add_grad(prop_id, name, g_type="text", n1=None, n2=None):
        cursor.execute(
            "INSERT INTO gradations (property_id, name, g_type, num1, num2) VALUES (?, ?, ?, ?, ?)",
            (prop_id, name, g_type, n1, n2),
        )
        g_ids[name] = cursor.lastrowid

    # --- ГРАДАЦИИ: Назначение ---
    add_grad(p_usage, "Дом / Офис / Игры")
    add_grad(p_usage, "Разработка ПО")
    add_grad(p_usage, "Сервер / Хостинг")
    add_grad(p_usage, "Кибербезопасность")
    add_grad(p_usage, "Энтузиаст / Изучение систем")
    add_grad(p_usage, "Анонимность / Приватность")   # новая
    add_grad(p_usage, "IoT / Одноплатники")           # новая

    # --- ГРАДАЦИИ: Опыт ---
    add_grad(p_exp, "Начинающий (Как в Windows)")
    add_grad(p_exp, "Средний (Знаком с терминалом)")
    add_grad(p_exp, "Опытный (Системный администратор)")
    add_grad(p_exp, "Гуру (Сборка ядра из исходников)")

    # --- ГРАДАЦИИ: ОЗУ ---
    add_grad(p_ram, "Микро-ПК / Роутер (0 - 1 ГБ)",         "range", 0,  1)
    add_grad(p_ram, "Слабый ПК (1 - 4 ГБ)",                  "range", 1,  4)
    add_grad(p_ram, "Средний ПК (4 - 8 ГБ)",                 "range", 4,  8)
    add_grad(p_ram, "Мощный ПК / Компиляция (8 - 32 ГБ)",    "range", 8, 32)

    # --- ГРАДАЦИИ: Диск ---
    add_grad(p_disk, "Сверхлегкая (5 ГБ)",           "numeric",  5)
    add_grad(p_disk, "Легкая (15 ГБ)",               "numeric", 15)
    add_grad(p_disk, "Стандарт (30 ГБ)",             "numeric", 30)
    add_grad(p_disk, "Тяжелая / Исходники (50 ГБ)",  "numeric", 50)

    # --- ГРАДАЦИИ: Цикл релизов ---
    add_grad(p_rel, "Rolling-релиз (Свежак, 1 мес)",   "numeric",  1)
    add_grad(p_rel, "Стандартный релиз (6 мес)",        "numeric",  6)
    add_grad(p_rel, "LTS Релиз (24 мес)",               "numeric", 24)
    add_grad(p_rel, "Enterprise Релиз (60 мес)",        "numeric", 60)

    # --- ГРАДАЦИИ: Время установки ---
    add_grad(p_inst, "Мгновенно (10 мин)",                "numeric",  10)
    add_grad(p_inst, "Быстро (20 мин)",                   "numeric",  20)
    add_grad(p_inst, "Вручную через консоль (45 мин)",    "numeric",  45)
    add_grad(p_inst, "Компиляция мира (300 мин)",         "numeric", 300)

    # --- ГРАДАЦИИ: Бинарные ---
    add_grad(p_gui,  "Да (Графика есть)",               "binary", 1)
    add_grad(p_gui,  "Нет (Только консоль)",            "binary", 0)
    add_grad(p_game, "Да (Игры работают)",              "binary", 1)
    add_grad(p_game, "Нет (Не для игр)",                "binary", 0)
    add_grad(p_prop, "Да (Дрова Wi-Fi/NVIDIA вшиты)",   "binary", 1)
    add_grad(p_prop, "Нет (Только Open-Source)",        "binary", 0)
    add_grad(p_dev,  "Да (Свежие версии)",              "binary", 1)
    add_grad(p_dev,  "Нет (Старые, но стабильные)",     "binary", 0)

    # =====================================================================
    # МАТРИЦА ЗНАНИЙ: (дистрибутив, градация, вес 1-10)
    # Логика весов:
    #   10 — абсолютно лучший выбор в этой категории
    #   7-9 — хорошо подходит
    #   4-6 — нейтрально / частично
    #   1-3 — плохо подходит (не используем, чтобы не засорять)
    # Каждый дистрибутив получает ровно 10 записей (по одной на свойство)
    # =====================================================================
    matrix = [
        # ── Ubuntu ──────────────────────────────────────────────────────
        ("Ubuntu", "Дом / Офис / Игры",                    8),
        ("Ubuntu", "Начинающий (Как в Windows)",           8),
        ("Ubuntu", "Средний ПК (4 - 8 ГБ)",               6),
        ("Ubuntu", "Стандарт (30 ГБ)",                     5),
        ("Ubuntu", "Стандартный релиз (6 мес)",            6),
        ("Ubuntu", "Да (Графика есть)",                    9),
        ("Ubuntu", "Быстро (20 мин)",                      5),
        ("Ubuntu", "Да (Игры работают)",                   9),
        ("Ubuntu", "Да (Дрова Wi-Fi/NVIDIA вшиты)",        8),
        ("Ubuntu", "Нет (Старые, но стабильные)",          4),

        # ── Linux Mint ──────────────────────────────────────────────────
        ("Linux Mint", "Дом / Офис / Игры",                10),
        ("Linux Mint", "Начинающий (Как в Windows)",       10),
        ("Linux Mint", "Слабый ПК (1 - 4 ГБ)",             8),
        ("Linux Mint", "Легкая (15 ГБ)",                    6),
        ("Linux Mint", "LTS Релиз (24 мес)",                8),
        ("Linux Mint", "Да (Графика есть)",                10),
        ("Linux Mint", "Быстро (20 мин)",                   6),
        ("Linux Mint", "Да (Игры работают)",                8),
        ("Linux Mint", "Да (Дрова Wi-Fi/NVIDIA вшиты)",    10),
        ("Linux Mint", "Нет (Старые, но стабильные)",       5),

        # ── Debian ──────────────────────────────────────────────────────
        ("Debian", "Сервер / Хостинг",                      9),
        ("Debian", "Опытный (Системный администратор)",      8),
        ("Debian", "Слабый ПК (1 - 4 ГБ)",                  7),
        ("Debian", "Сверхлегкая (5 ГБ)",                    5),
        ("Debian", "LTS Релиз (24 мес)",                   10),
        ("Debian", "Нет (Только консоль)",                   6),
        ("Debian", "Быстро (20 мин)",                        4),
        ("Debian", "Нет (Не для игр)",                       7),
        ("Debian", "Нет (Только Open-Source)",              10),
        ("Debian", "Нет (Старые, но стабильные)",            8),

        # ── Arch Linux ──────────────────────────────────────────────────
        ("Arch Linux", "Энтузиаст / Изучение систем",      10),
        ("Arch Linux", "Гуру (Сборка ядра из исходников)",  8),
        ("Arch Linux", "Средний ПК (4 - 8 ГБ)",             5),
        ("Arch Linux", "Легкая (15 ГБ)",                     6),
        ("Arch Linux", "Rolling-релиз (Свежак, 1 мес)",    10),
        ("Arch Linux", "Нет (Только консоль)",               8),
        ("Arch Linux", "Вручную через консоль (45 мин)",     9),
        ("Arch Linux", "Да (Игры работают)",                 6),
        ("Arch Linux", "Нет (Только Open-Source)",           5),
        ("Arch Linux", "Да (Свежие версии)",                10),

        # ── Gentoo ──────────────────────────────────────────────────────
        ("Gentoo", "Энтузиаст / Изучение систем",          10),
        ("Gentoo", "Гуру (Сборка ядра из исходников)",     10),
        ("Gentoo", "Мощный ПК / Компиляция (8 - 32 ГБ)",  10),
        ("Gentoo", "Тяжелая / Исходники (50 ГБ)",           8),
        ("Gentoo", "Rolling-релиз (Свежак, 1 мес)",         6),
        ("Gentoo", "Нет (Только консоль)",                   9),
        ("Gentoo", "Компиляция мира (300 мин)",             10),
        ("Gentoo", "Нет (Не для игр)",                       8),
        ("Gentoo", "Нет (Только Open-Source)",               5),
        ("Gentoo", "Да (Свежие версии)",                     8),

        # ── Fedora ──────────────────────────────────────────────────────
        ("Fedora", "Разработка ПО",                        10),
        ("Fedora", "Средний (Знаком с терминалом)",         7),
        ("Fedora", "Средний ПК (4 - 8 ГБ)",                 6),
        ("Fedora", "Стандарт (30 ГБ)",                      5),
        ("Fedora", "Стандартный релиз (6 мес)",             8),
        ("Fedora", "Да (Графика есть)",                      8),
        ("Fedora", "Быстро (20 мин)",                        5),
        ("Fedora", "Нет (Не для игр)",                       5),
        ("Fedora", "Нет (Только Open-Source)",               8),
        ("Fedora", "Да (Свежие версии)",                    10),

        # ── Manjaro ─────────────────────────────────────────────────────
        ("Manjaro", "Дом / Офис / Игры",                    8),
        ("Manjaro", "Средний (Знаком с терминалом)",         8),
        ("Manjaro", "Средний ПК (4 - 8 ГБ)",                6),
        ("Manjaro", "Стандарт (30 ГБ)",                      5),
        ("Manjaro", "Rolling-релиз (Свежак, 1 мес)",         8),
        ("Manjaro", "Да (Графика есть)",                     9),
        ("Manjaro", "Мгновенно (10 мин)",                    6),
        ("Manjaro", "Да (Игры работают)",                    9),
        ("Manjaro", "Да (Дрова Wi-Fi/NVIDIA вшиты)",        10),
        ("Manjaro", "Да (Свежие версии)",                    8),

        # ── Kali Linux ──────────────────────────────────────────────────
        ("Kali Linux", "Кибербезопасность",                10),
        ("Kali Linux", "Опытный (Системный администратор)", 8),
        ("Kali Linux", "Средний ПК (4 - 8 ГБ)",             5),
        ("Kali Linux", "Стандарт (30 ГБ)",                   5),
        ("Kali Linux", "Rolling-релиз (Свежак, 1 мес)",      6),
        ("Kali Linux", "Да (Графика есть)",                  6),
        ("Kali Linux", "Быстро (20 мин)",                    5),
        ("Kali Linux", "Нет (Не для игр)",                   9),
        ("Kali Linux", "Да (Дрова Wi-Fi/NVIDIA вшиты)",      8),
        ("Kali Linux", "Да (Свежие версии)",                 7),

        # ── CentOS Stream ───────────────────────────────────────────────
        ("CentOS Stream", "Сервер / Хостинг",              10),
        ("CentOS Stream", "Опытный (Системный администратор)", 8),
        ("CentOS Stream", "Средний ПК (4 - 8 ГБ)",          6),
        ("CentOS Stream", "Стандарт (30 ГБ)",                5),
        ("CentOS Stream", "Enterprise Релиз (60 мес)",      10),
        ("CentOS Stream", "Нет (Только консоль)",            7),
        ("CentOS Stream", "Быстро (20 мин)",                 4),
        ("CentOS Stream", "Нет (Не для игр)",                9),
        ("CentOS Stream", "Нет (Только Open-Source)",        6),
        ("CentOS Stream", "Нет (Старые, но стабильные)",     8),

        # ── Alpine Linux ────────────────────────────────────────────────
        ("Alpine Linux", "Сервер / Хостинг",                8),
        ("Alpine Linux", "Гуру (Сборка ядра из исходников)", 8),
        ("Alpine Linux", "Микро-ПК / Роутер (0 - 1 ГБ)",   10),
        ("Alpine Linux", "Сверхлегкая (5 ГБ)",             10),
        ("Alpine Linux", "Стандартный релиз (6 мес)",        5),
        ("Alpine Linux", "Нет (Только консоль)",            10),
        ("Alpine Linux", "Мгновенно (10 мин)",               8),
        ("Alpine Linux", "Нет (Не для игр)",                10),
        ("Alpine Linux", "Нет (Только Open-Source)",         8),
        ("Alpine Linux", "Нет (Старые, но стабильные)",      6),

        # ── openSUSE Tumbleweed ─────────────────────────────────────────
        # Rolling-дистрибутив от SUSE с KDE Plasma.
        # Популярен у разработчиков и энтузиастов.
        # Инструмент YaST делает настройку проще, чем у Arch.
        ("openSUSE Tumbleweed", "Разработка ПО",                    9),
        ("openSUSE Tumbleweed", "Средний (Знаком с терминалом)",     7),
        ("openSUSE Tumbleweed", "Средний ПК (4 - 8 ГБ)",             6),
        ("openSUSE Tumbleweed", "Стандарт (30 ГБ)",                   5),
        ("openSUSE Tumbleweed", "Rolling-релиз (Свежак, 1 мес)",     9),
        ("openSUSE Tumbleweed", "Да (Графика есть)",                  9),
        ("openSUSE Tumbleweed", "Быстро (20 мин)",                    6),
        ("openSUSE Tumbleweed", "Да (Игры работают)",                 6),
        ("openSUSE Tumbleweed", "Нет (Только Open-Source)",           7),
        ("openSUSE Tumbleweed", "Да (Свежие версии)",                 9),

        # ── openSUSE Leap ───────────────────────────────────────────────
        # Стабильная ветка openSUSE, основана на SUSE Linux Enterprise.
        # Корпоративная надёжность с удобным GUI (YaST).
        ("openSUSE Leap", "Сервер / Хостинг",                        8),
        ("openSUSE Leap", "Средний (Знаком с терминалом)",            7),
        ("openSUSE Leap", "Средний ПК (4 - 8 ГБ)",                   6),
        ("openSUSE Leap", "Стандарт (30 ГБ)",                         5),
        ("openSUSE Leap", "LTS Релиз (24 мес)",                       9),
        ("openSUSE Leap", "Да (Графика есть)",                        8),
        ("openSUSE Leap", "Быстро (20 мин)",                          5),
        ("openSUSE Leap", "Нет (Не для игр)",                         7),
        ("openSUSE Leap", "Нет (Только Open-Source)",                  7),
        ("openSUSE Leap", "Нет (Старые, но стабильные)",               8),

        # ── Pop!_OS ─────────────────────────────────────────────────────
        # Ubuntu-based от System76. NVIDIA-драйверы из коробки.
        # Лучший выбор для геймеров с видеокартой NVIDIA.
        ("Pop!_OS", "Дом / Офис / Игры",                             10),
        ("Pop!_OS", "Начинающий (Как в Windows)",                     8),
        ("Pop!_OS", "Средний ПК (4 - 8 ГБ)",                          7),
        ("Pop!_OS", "Стандарт (30 ГБ)",                                5),
        ("Pop!_OS", "LTS Релиз (24 мес)",                              7),
        ("Pop!_OS", "Да (Графика есть)",                              10),
        ("Pop!_OS", "Быстро (20 мин)",                                 6),
        ("Pop!_OS", "Да (Игры работают)",                             10),
        ("Pop!_OS", "Да (Дрова Wi-Fi/NVIDIA вшиты)",                  10),
        ("Pop!_OS", "Нет (Старые, но стабильные)",                     5),

        # ── Elementary OS ───────────────────────────────────────────────
        # Ubuntu-based с интерфейсом в стиле macOS (Pantheon DE).
        # Идеален для пользователей Apple, переходящих на Linux.
        ("Elementary OS", "Дом / Офис / Игры",                        8),
        ("Elementary OS", "Начинающий (Как в Windows)",               10),
        ("Elementary OS", "Средний ПК (4 - 8 ГБ)",                    6),
        ("Elementary OS", "Стандарт (30 ГБ)",                          5),
        ("Elementary OS", "LTS Релиз (24 мес)",                        7),
        ("Elementary OS", "Да (Графика есть)",                        10),
        ("Elementary OS", "Быстро (20 мин)",                           6),
        ("Elementary OS", "Нет (Не для игр)",                          6),
        ("Elementary OS", "Да (Дрова Wi-Fi/NVIDIA вшиты)",             8),
        ("Elementary OS", "Нет (Старые, но стабильные)",               5),

        # ── Zorin OS ────────────────────────────────────────────────────
        # Ubuntu-based, специально для мигрантов с Windows.
        # Имеет "Windows-режим" интерфейса. Идеален для школ/офисов.
        ("Zorin OS", "Дом / Офис / Игры",                             9),
        ("Zorin OS", "Начинающий (Как в Windows)",                    10),
        ("Zorin OS", "Слабый ПК (1 - 4 ГБ)",                          7),
        ("Zorin OS", "Легкая (15 ГБ)",                                 6),
        ("Zorin OS", "LTS Релиз (24 мес)",                             8),
        ("Zorin OS", "Да (Графика есть)",                             10),
        ("Zorin OS", "Быстро (20 мин)",                                6),
        ("Zorin OS", "Да (Игры работают)",                             7),
        ("Zorin OS", "Да (Дрова Wi-Fi/NVIDIA вшиты)",                  9),
        ("Zorin OS", "Нет (Старые, но стабильные)",                    5),

        # ── MX Linux ────────────────────────────────────────────────────
        # Debian-based, Xfce. Лидер по популярности на DistroWatch.
        # Отлично работает на старых ПК, есть MX Tools для управления.
        ("MX Linux", "Дом / Офис / Игры",                             8),
        ("MX Linux", "Средний (Знаком с терминалом)",                  7),
        ("MX Linux", "Слабый ПК (1 - 4 ГБ)",                         10),
        ("MX Linux", "Легкая (15 ГБ)",                                 7),
        ("MX Linux", "LTS Релиз (24 мес)",                             9),
        ("MX Linux", "Да (Графика есть)",                              9),
        ("MX Linux", "Быстро (20 мин)",                                6),
        ("MX Linux", "Нет (Не для игр)",                               6),
        ("MX Linux", "Нет (Только Open-Source)",                        8),
        ("MX Linux", "Нет (Старые, но стабильные)",                    8),

        # ── Tails ───────────────────────────────────────────────────────
        # Live-дистрибутив для анонимности. Весь трафик через Tor.
        # Не оставляет следов на компьютере. Для журналистов/активистов.
        ("Tails", "Анонимность / Приватность",                        10),
        ("Tails", "Средний (Знаком с терминалом)",                     7),
        ("Tails", "Слабый ПК (1 - 4 ГБ)",                              8),
        ("Tails", "Сверхлегкая (5 ГБ)",                                9),
        ("Tails", "Rolling-релиз (Свежак, 1 мес)",                      7),
        ("Tails", "Да (Графика есть)",                                  7),
        ("Tails", "Мгновенно (10 мин)",                                 9),
        ("Tails", "Нет (Не для игр)",                                  10),
        ("Tails", "Нет (Только Open-Source)",                          10),
        ("Tails", "Нет (Старые, но стабильные)",                        6),

        # ── Whonix ──────────────────────────────────────────────────────
        # Максимальная анонимность через двойную VM (Gateway + Workstation).
        # Весь трафик через Tor даже если приложение взломано.
        ("Whonix", "Анонимность / Приватность",                       10),
        ("Whonix", "Опытный (Системный администратор)",                 9),
        ("Whonix", "Мощный ПК / Компиляция (8 - 32 ГБ)",               8),
        ("Whonix", "Стандарт (30 ГБ)",                                  6),
        ("Whonix", "Стандартный релиз (6 мес)",                         6),
        ("Whonix", "Да (Графика есть)",                                  6),
        ("Whonix", "Быстро (20 мин)",                                    5),
        ("Whonix", "Нет (Не для игр)",                                  10),
        ("Whonix", "Нет (Только Open-Source)",                          10),
        ("Whonix", "Нет (Старые, но стабильные)",                        7),

        # ── Parrot OS ───────────────────────────────────────────────────
        # Debian-based. Совмещает инструменты pentest (как Kali)
        # и защиту приватности (Tor, I2P). Легче Kali, пригоден как основной.
        ("Parrot OS", "Кибербезопасность",                              9),
        ("Parrot OS", "Опытный (Системный администратор)",               8),
        ("Parrot OS", "Слабый ПК (1 - 4 ГБ)",                           8),
        ("Parrot OS", "Легкая (15 ГБ)",                                  6),
        ("Parrot OS", "Rolling-релиз (Свежак, 1 мес)",                   7),
        ("Parrot OS", "Да (Графика есть)",                               8),
        ("Parrot OS", "Быстро (20 мин)",                                 6),
        ("Parrot OS", "Нет (Не для игр)",                                8),
        ("Parrot OS", "Да (Дрова Wi-Fi/NVIDIA вшиты)",                   7),
        ("Parrot OS", "Да (Свежие версии)",                              7),

        # ── Slackware ───────────────────────────────────────────────────
        # Старейший живой дистрибутив (с 1993 г.).
        # UNIX-философия: минимум автоматизации, максимум контроля.
        # Нет менеджера зависимостей — всё вручную.
        ("Slackware", "Энтузиаст / Изучение систем",                  10),
        ("Slackware", "Гуру (Сборка ядра из исходников)",             10),
        ("Slackware", "Слабый ПК (1 - 4 ГБ)",                          7),
        ("Slackware", "Легкая (15 ГБ)",                                  5),
        ("Slackware", "LTS Релиз (24 мес)",                              7),
        ("Slackware", "Да (Графика есть)",                               6),
        ("Slackware", "Вручную через консоль (45 мин)",                  9),
        ("Slackware", "Нет (Не для игр)",                                8),
        ("Slackware", "Нет (Только Open-Source)",                        9),
        ("Slackware", "Нет (Старые, но стабильные)",                     9),

        # ── Void Linux ──────────────────────────────────────────────────
        # Независимый rolling-дистрибутив (не Debian/Arch/RPM).
        # Использует runit вместо systemd. Очень быстрый и лёгкий.
        ("Void Linux", "Энтузиаст / Изучение систем",                   9),
        ("Void Linux", "Опытный (Системный администратор)",              8),
        ("Void Linux", "Слабый ПК (1 - 4 ГБ)",                          9),
        ("Void Linux", "Легкая (15 ГБ)",                                  7),
        ("Void Linux", "Rolling-релиз (Свежак, 1 мес)",                   9),
        ("Void Linux", "Нет (Только консоль)",                            8),
        ("Void Linux", "Вручную через консоль (45 мин)",                   7),
        ("Void Linux", "Нет (Не для игр)",                                 7),
        ("Void Linux", "Нет (Только Open-Source)",                         8),
        ("Void Linux", "Да (Свежие версии)",                               8),

        # ── NixOS ───────────────────────────────────────────────────────
        # Декларативная конфигурация всей ОС через один файл .nix.
        # Атомарные обновления с откатом. Идеал DevOps/инфраструктуры.
        ("NixOS", "Разработка ПО",                                       9),
        ("NixOS", "Гуру (Сборка ядра из исходников)",                    9),
        ("NixOS", "Средний ПК (4 - 8 ГБ)",                               6),
        ("NixOS", "Тяжелая / Исходники (50 ГБ)",                          7),
        ("NixOS", "Rolling-релиз (Свежак, 1 мес)",                        8),
        ("NixOS", "Нет (Только консоль)",                                  8),
        ("NixOS", "Вручную через консоль (45 мин)",                        9),
        ("NixOS", "Нет (Не для игр)",                                      7),
        ("NixOS", "Нет (Только Open-Source)",                               7),
        ("NixOS", "Да (Свежие версии)",                                     9),

        # ── Qubes OS ────────────────────────────────────────────────────
        # Безопасность через изоляцию: каждое приложение в своей VM (qube).
        # Рекомендован Сноуденом. Требует мощного железа (VT-x/VT-d).
        ("Qubes OS", "Анонимность / Приватность",                        9),
        ("Qubes OS", "Опытный (Системный администратор)",                 9),
        ("Qubes OS", "Мощный ПК / Компиляция (8 - 32 ГБ)",              10),
        ("Qubes OS", "Тяжелая / Исходники (50 ГБ)",                       8),
        ("Qubes OS", "Стандартный релиз (6 мес)",                          6),
        ("Qubes OS", "Да (Графика есть)",                                   7),
        ("Qubes OS", "Вручную через консоль (45 мин)",                      8),
        ("Qubes OS", "Нет (Не для игр)",                                   10),
        ("Qubes OS", "Нет (Только Open-Source)",                             8),
        ("Qubes OS", "Нет (Старые, но стабильные)",                          6),

        # ── Raspberry Pi OS ─────────────────────────────────────────────
        # Официальный дистрибутив для Raspberry Pi (ARM).
        # Debian-based, оптимизирован для одноплатников и IoT-проектов.
        ("Raspberry Pi OS", "IoT / Одноплатники",                       10),
        ("Raspberry Pi OS", "Начинающий (Как в Windows)",                 8),
        ("Raspberry Pi OS", "Микро-ПК / Роутер (0 - 1 ГБ)",             10),
        ("Raspberry Pi OS", "Сверхлегкая (5 ГБ)",                         9),
        ("Raspberry Pi OS", "LTS Релиз (24 мес)",                          8),
        ("Raspberry Pi OS", "Да (Графика есть)",                           8),
        ("Raspberry Pi OS", "Мгновенно (10 мин)",                          9),
        ("Raspberry Pi OS", "Нет (Не для игр)",                            7),
        ("Raspberry Pi OS", "Нет (Только Open-Source)",                     8),
        ("Raspberry Pi OS", "Нет (Старые, но стабильные)",                  7),

        # ── Ubuntu Server ────────────────────────────────────────────────
        # Headless-версия Ubuntu. Стандарт для облачных провайдеров
        # (AWS, GCP, Azure). LTS-поддержка 5 лет, Pro — 10 лет.
        ("Ubuntu Server", "Сервер / Хостинг",                           10),
        ("Ubuntu Server", "Опытный (Системный администратор)",            8),
        ("Ubuntu Server", "Слабый ПК (1 - 4 ГБ)",                         8),
        ("Ubuntu Server", "Легкая (15 ГБ)",                                 6),
        ("Ubuntu Server", "LTS Релиз (24 мес)",                            10),
        ("Ubuntu Server", "Нет (Только консоль)",                          10),
        ("Ubuntu Server", "Быстро (20 мин)",                                6),
        ("Ubuntu Server", "Нет (Не для игр)",                              10),
        ("Ubuntu Server", "Да (Дрова Wi-Fi/NVIDIA вшиты)",                  7),
        ("Ubuntu Server", "Нет (Старые, но стабильные)",                     7),

        # ── Rocky Linux ──────────────────────────────────────────────────
        # Бинарно-совместимая замена CentOS 8. Создан сообществом.
        # Enterprise-стабильность без подписки Red Hat.
        ("Rocky Linux", "Сервер / Хостинг",                             10),
        ("Rocky Linux", "Опытный (Системный администратор)",              9),
        ("Rocky Linux", "Средний ПК (4 - 8 ГБ)",                          6),
        ("Rocky Linux", "Стандарт (30 ГБ)",                                 5),
        ("Rocky Linux", "Enterprise Релиз (60 мес)",                       10),
        ("Rocky Linux", "Нет (Только консоль)",                             8),
        ("Rocky Linux", "Быстро (20 мин)",                                   5),
        ("Rocky Linux", "Нет (Не для игр)",                                  9),
        ("Rocky Linux", "Нет (Только Open-Source)",                           7),
        ("Rocky Linux", "Нет (Старые, но стабильные)",                        9),

        # ── Lubuntu ──────────────────────────────────────────────────────
        # Официальный флавор Ubuntu с LXQt. Самый лёгкий из Ubuntu-семьи.
        # Идеален для ПК с 512 МБ — 2 ГБ ОЗУ (нетбуки, старые офисные ПК).
        ("Lubuntu", "Дом / Офис / Игры",                                 7),
        ("Lubuntu", "Начинающий (Как в Windows)",                         8),
        ("Lubuntu", "Слабый ПК (1 - 4 ГБ)",                             10),
        ("Lubuntu", "Легкая (15 ГБ)",                                      8),
        ("Lubuntu", "LTS Релиз (24 мес)",                                   8),
        ("Lubuntu", "Да (Графика есть)",                                    9),
        ("Lubuntu", "Быстро (20 мин)",                                       7),
        ("Lubuntu", "Нет (Не для игр)",                                      6),
        ("Lubuntu", "Да (Дрова Wi-Fi/NVIDIA вшиты)",                         7),
        ("Lubuntu", "Нет (Старые, но стабильные)",                            6),

        # ── Kali Purple ──────────────────────────────────────────────────
        # Новая ветка Kali для Blue Team (защита, мониторинг, SOC).
        # Содержит инструменты SIEM, IDS, форензики. Дополняет классический Kali.
        ("Kali Purple", "Кибербезопасность",                             10),
        ("Kali Purple", "Опытный (Системный администратор)",              9),
        ("Kali Purple", "Мощный ПК / Компиляция (8 - 32 ГБ)",             8),
        ("Kali Purple", "Тяжелая / Исходники (50 ГБ)",                     7),
        ("Kali Purple", "Rolling-релиз (Свежак, 1 мес)",                    7),
        ("Kali Purple", "Да (Графика есть)",                                7),
        ("Kali Purple", "Быстро (20 мин)",                                   5),
        ("Kali Purple", "Нет (Не для игр)",                                 10),
        ("Kali Purple", "Да (Дрова Wi-Fi/NVIDIA вшиты)",                     7),
        ("Kali Purple", "Да (Свежие версии)",                                8),

        # ── Garuda Linux ─────────────────────────────────────────────────
        # Arch-based, заточен под геймеров: BTRFS, zram, gamemode, WINE.
        # Красивый KDE Plasma/GNOME. Установщик Calamares — проще Arch.
        ("Garuda Linux", "Дом / Офис / Игры",                           10),
        ("Garuda Linux", "Средний (Знаком с терминалом)",                 7),
        ("Garuda Linux", "Средний ПК (4 - 8 ГБ)",                         7),
        ("Garuda Linux", "Стандарт (30 ГБ)",                                6),
        ("Garuda Linux", "Rolling-релиз (Свежак, 1 мес)",                  9),
        ("Garuda Linux", "Да (Графика есть)",                              10),
        ("Garuda Linux", "Быстро (20 мин)",                                  6),
        ("Garuda Linux", "Да (Игры работают)",                             10),
        ("Garuda Linux", "Да (Дрова Wi-Fi/NVIDIA вшиты)",                   9),
        ("Garuda Linux", "Да (Свежие версии)",                               9),

        # ── EndeavourOS ──────────────────────────────────────────────────
        # Arch-based с графическим установщиком Calamares.
        # "Arch для людей" — минимум bloatware, максимум свободы настройки.
        ("EndeavourOS", "Энтузиаст / Изучение систем",                    9),
        ("EndeavourOS", "Средний (Знаком с терминалом)",                   8),
        ("EndeavourOS", "Средний ПК (4 - 8 ГБ)",                           6),
        ("EndeavourOS", "Легкая (15 ГБ)",                                    6),
        ("EndeavourOS", "Rolling-релиз (Свежак, 1 мес)",                   10),
        ("EndeavourOS", "Да (Графика есть)",                                 8),
        ("EndeavourOS", "Быстро (20 мин)",                                    7),
        ("EndeavourOS", "Да (Игры работают)",                                 7),
        ("EndeavourOS", "Нет (Только Open-Source)",                            6),
        ("EndeavourOS", "Да (Свежие версии)",                                 10),
    ]

    for d_name, g_name, raw_weight in matrix:
        cursor.execute(
            "INSERT INTO relations (section_id, gradation_id, weight) VALUES (?, ?, ?)",
            (d_ids[d_name], g_ids[g_name], raw_weight),
        )

    conn.commit()
    conn.close()

    # --- Итоговая статистика ---
    print("✅ База знаний создана!")
    print(f"   Дистрибутивов : {len(distros)}")
    print(f"   Свойств        : 10")
    print(f"   Записей матрицы: {len(matrix)}")
    print(f"   Файл           : {db_path}")


if __name__ == "__main__":
    create_massive_knowledge_base()
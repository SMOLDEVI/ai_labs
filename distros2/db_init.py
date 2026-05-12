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

    distros = [
        "Ubuntu", "Linux Mint", "Debian", "Arch Linux", "Gentoo",
        "Fedora", "Manjaro", "Kali Linux", "CentOS Stream", "Alpine Linux"
    ]
    for d in distros:
        cursor.execute("INSERT INTO sections (name) VALUES (?)", (d,))

    cursor.execute("SELECT id, name FROM sections")
    d_ids = {name: sid for sid, name in cursor.fetchall()}

    def add_prop(event_name, prop_name):
        cursor.execute("INSERT OR IGNORE INTO events (name) VALUES (?)", (event_name,))
        cursor.execute("SELECT id FROM events WHERE name = ?", (event_name,))
        ev_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO properties (event_id, name) VALUES (?, ?)", (ev_id, prop_name))
        return cursor.lastrowid

    p_usage = add_prop("1. Целевое назначение", "Главная сфера применения")
    p_exp = add_prop("2. Уровень пользователя", "Требуемый опыт работы")
    p_ram = add_prop("3. Требования к ОЗУ", "ОЗУ для комфортной работы (ГБ)")
    p_disk = add_prop("4. Требования к накопителю", "Мин. место на диске (ГБ)")
    p_rel = add_prop("5. Жизненный цикл", "Цикл обновлений (мес.)")
    p_gui = add_prop("6. Графическая оболочка", 'GUI "из коробки"')
    p_inst = add_prop("7. Процесс установки", "Среднее время установки (мин.)")
    p_game = add_prop("8. Игры и Мультимедиа", "Готовность к Steam / Играм")
    p_prop = add_prop("9. Драйвера и Кодеки", "Проприетарное ПО в комплекте")
    p_dev = add_prop("10. Разработка ПО", "Самые свежие компиляторы/пакеты")

    g_ids = {}

    def add_grad(prop_id, name, g_type="text", n1=None, n2=None):
        cursor.execute(
            "INSERT INTO gradations (property_id, name, g_type, num1, num2) VALUES (?, ?, ?, ?, ?)",
            (prop_id, name, g_type, n1, n2),
        )
        g_ids[name] = cursor.lastrowid

    add_grad(p_usage, "Дом / Офис / Игры")
    add_grad(p_usage, "Разработка ПО")
    add_grad(p_usage, "Сервер / Хостинг")
    add_grad(p_usage, "Кибербезопасность")
    add_grad(p_usage, "Энтузиаст / Изучение систем")

    add_grad(p_exp, "Начинающий (Как в Windows)")
    add_grad(p_exp, "Средний (Знаком с терминалом)")
    add_grad(p_exp, "Опытный (Системный администратор)")
    add_grad(p_exp, "Гуру (Сборка ядра из исходников)")

    add_grad(p_ram, "Микро-ПК / Роутер (0 - 1 ГБ)", "range", 0, 1)
    add_grad(p_ram, "Слабый ПК (1 - 4 ГБ)", "range", 1, 4)
    add_grad(p_ram, "Средний ПК (4 - 8 ГБ)", "range", 4, 8)
    add_grad(p_ram, "Мощный ПК / Компиляция (8 - 32 ГБ)", "range", 8, 32)

    add_grad(p_disk, "Сверхлегкая (5 ГБ)", "numeric", 5)
    add_grad(p_disk, "Легкая (15 ГБ)", "numeric", 15)
    add_grad(p_disk, "Стандарт (30 ГБ)", "numeric", 30)
    add_grad(p_disk, "Тяжелая / Исходники (50 ГБ)", "numeric", 50)

    add_grad(p_rel, "Rolling-релиз (Свежак, 1 мес)", "numeric", 1)
    add_grad(p_rel, "Стандартный релиз (6 мес)", "numeric", 6)
    add_grad(p_rel, "LTS Релиз (24 мес)", "numeric", 24)
    add_grad(p_rel, "Enterprise Релиз (60 мес)", "numeric", 60)

    add_grad(p_inst, "Мгновенно (10 мин)", "numeric", 10)
    add_grad(p_inst, "Быстро (20 мин)", "numeric", 20)
    add_grad(p_inst, "Вручную через консоль (45 мин)", "numeric", 45)
    add_grad(p_inst, "Компиляция мира (300 мин)", "numeric", 300)

    add_grad(p_gui, "Да (Графика есть)", "binary", 1)
    add_grad(p_gui, "Нет (Только консоль)", "binary", 0)

    add_grad(p_game, "Да (Игры работают)", "binary", 1)
    add_grad(p_game, "Нет (Не для игр)", "binary", 0)

    add_grad(p_prop, "Да (Дрова Wi-Fi/NVIDIA вшиты)", "binary", 1)
    add_grad(p_prop, "Нет (Только Open-Source)", "binary", 0)

    add_grad(p_dev, "Да (Свежие версии)", "binary", 1)
    add_grad(p_dev, "Нет (Старые, но стабильные)", "binary", 0)

    matrix = [
        ("Ubuntu", "Дом / Офис / Игры", 8),
        ("Ubuntu", "Начинающий (Как в Windows)", 8),
        ("Ubuntu", "Средний ПК (4 - 8 ГБ)", 6),
        ("Ubuntu", "Стандарт (30 ГБ)", 5),
        ("Ubuntu", "Стандартный релиз (6 мес)", 6),
        ("Ubuntu", "Да (Графика есть)", 9),
        ("Ubuntu", "Быстро (20 мин)", 5),
        ("Ubuntu", "Да (Игры работают)", 9),
        ("Ubuntu", "Да (Дрова Wi-Fi/NVIDIA вшиты)", 8),
        ("Ubuntu", "Нет (Старые, но стабильные)", 4),
        ("Linux Mint", "Дом / Офис / Игры", 10),
        ("Linux Mint", "Начинающий (Как в Windows)", 10),
        ("Linux Mint", "Слабый ПК (1 - 4 ГБ)", 8),
        ("Linux Mint", "Легкая (15 ГБ)", 6),
        ("Linux Mint", "LTS Релиз (24 мес)", 8),
        ("Linux Mint", "Да (Графика есть)", 10),
        ("Linux Mint", "Быстро (20 мин)", 6),
        ("Linux Mint", "Да (Игры работают)", 8),
        ("Linux Mint", "Да (Дрова Wi-Fi/NVIDIA вшиты)", 10),
        ("Linux Mint", "Нет (Старые, но стабильные)", 5),
        ("Debian", "Сервер / Хостинг", 9),
        ("Debian", "Опытный (Системный администратор)", 8),
        ("Debian", "Слабый ПК (1 - 4 ГБ)", 7),
        ("Debian", "Сверхлегкая (5 ГБ)", 5),
        ("Debian", "LTS Релиз (24 мес)", 10),
        ("Debian", "Нет (Только консоль)", 6),
        ("Debian", "Быстро (20 мин)", 4),
        ("Debian", "Нет (Не для игр)", 7),
        ("Debian", "Нет (Только Open-Source)", 10),  
        ("Debian", "Нет (Старые, но стабильные)", 8),
        ("Arch Linux", "Энтузиаст / Изучение систем", 10),
        ("Arch Linux", "Гуру (Сборка ядра из исходников)", 8),
        ("Arch Linux", "Средний ПК (4 - 8 ГБ)", 5),
        ("Arch Linux", "Легкая (15 ГБ)", 6),
        ("Arch Linux", "Rolling-релиз (Свежак, 1 мес)", 10),
        ("Arch Linux", "Нет (Только консоль)", 8),
        ("Arch Linux", "Вручную через консоль (45 мин)", 9),
        ("Arch Linux", "Да (Игры работают)", 6),
        ("Arch Linux", "Нет (Только Open-Source)", 5),
        ("Arch Linux", "Да (Свежие версии)", 10),
        ("Gentoo", "Энтузиаст / Изучение систем", 10),
        ("Gentoo", "Гуру (Сборка ядра из исходников)", 10),
        ("Gentoo", "Мощный ПК / Компиляция (8 - 32 ГБ)", 10),  
        ("Gentoo", "Тяжелая / Исходники (50 ГБ)", 8),
        ("Gentoo", "Rolling-релиз (Свежак, 1 мес)", 6),
        ("Gentoo", "Нет (Только консоль)", 9),
        ("Gentoo", "Компиляция мира (300 мин)", 10),  
        ("Gentoo", "Нет (Не для игр)", 8),
        ("Gentoo", "Нет (Только Open-Source)", 5),
        ("Gentoo", "Да (Свежие версии)", 8),
        ("Fedora", "Разработка ПО", 10),
        ("Fedora", "Средний (Знаком с терминалом)", 7),
        ("Fedora", "Средний ПК (4 - 8 ГБ)", 6),
        ("Fedora", "Стандарт (30 ГБ)", 5),
        ("Fedora", "Стандартный релиз (6 мес)", 8),
        ("Fedora", "Да (Графика есть)", 8),
        ("Fedora", "Быстро (20 мин)", 5),
        ("Fedora", "Нет (Не для игр)", 5),
        ("Fedora", "Нет (Только Open-Source)", 8),  
        ("Fedora", "Да (Свежие версии)", 10),
        ("Manjaro", "Дом / Офис / Игры", 8),
        ("Manjaro", "Средний (Знаком с терминалом)", 8),
        ("Manjaro", "Средний ПК (4 - 8 ГБ)", 6),
        ("Manjaro", "Стандарт (30 ГБ)", 5),
        ("Manjaro", "Rolling-релиз (Свежак, 1 мес)", 8),
        ("Manjaro", "Да (Графика есть)", 9),
        ("Manjaro", "Мгновенно (10 мин)", 6),
        ("Manjaro", "Да (Игры работают)", 9),
        ("Manjaro", "Да (Дрова Wi-Fi/NVIDIA вшиты)", 10),
        ("Manjaro", "Да (Свежие версии)", 8),
        ("Kali Linux", "Кибербезопасность", 10),  
        ("Kali Linux", "Опытный (Системный администратор)", 8),
        ("Kali Linux", "Средний ПК (4 - 8 ГБ)", 5),
        ("Kali Linux", "Стандарт (30 ГБ)", 5),
        ("Kali Linux", "Rolling-релиз (Свежак, 1 мес)", 6),
        ("Kali Linux", "Да (Графика есть)", 6),
        ("Kali Linux", "Быстро (20 мин)", 5),
        ("Kali Linux", "Нет (Не для игр)", 9),
        ("Kali Linux", "Да (Дрова Wi-Fi/NVIDIA вшиты)", 8),
        ("Kali Linux", "Да (Свежие версии)", 7),
        ("CentOS Stream", "Сервер / Хостинг", 10),
        ("CentOS Stream", "Опытный (Системный администратор)", 8),
        ("CentOS Stream", "Средний ПК (4 - 8 ГБ)", 6),
        ("CentOS Stream", "Стандарт (30 ГБ)", 5),
        ("CentOS Stream", "Enterprise Релиз (60 мес)", 10),
        ("CentOS Stream", "Нет (Только консоль)", 7),
        ("CentOS Stream", "Быстро (20 мин)", 4),
        ("CentOS Stream", "Нет (Не для игр)", 9),
        ("CentOS Stream", "Нет (Только Open-Source)", 6),
        ("CentOS Stream", "Нет (Старые, но стабильные)", 8),
        ("Alpine Linux", "Сервер / Хостинг", 8),
        ("Alpine Linux", "Гуру (Сборка ядра из исходников)", 8),
        ("Alpine Linux", "Микро-ПК / Роутер (0 - 1 ГБ)", 10),  
        ("Alpine Linux", "Сверхлегкая (5 ГБ)", 10),
        ("Alpine Linux", "Стандартный релиз (6 мес)", 5),
        ("Alpine Linux", "Нет (Только консоль)", 10),
        ("Alpine Linux", "Мгновенно (10 мин)", 8),
        ("Alpine Linux", "Нет (Не для игр)", 10),
        ("Alpine Linux", "Нет (Только Open-Source)", 8),
        ("Alpine Linux", "Нет (Старые, но стабильные)", 6),
    ]

    for d_name, g_name, raw_weight in matrix:
        cursor.execute(
            "INSERT INTO relations (section_id, gradation_id, weight) VALUES (?, ?, ?)",
            (d_ids[d_name], g_ids[g_name], raw_weight),
        )

    # ==== Я УДАЛИЛ БЛОК НОРМАЛИЗАЦИИ ОТСЮДА ====

    conn.commit()
    conn.close()
    print("✅ Создана элитная база знаний! Шкала строго от 1 до 10!")

if __name__ == "__main__":
    create_massive_knowledge_base()

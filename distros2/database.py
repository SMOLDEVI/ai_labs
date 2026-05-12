import sqlite3


class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.conn = None

    def connect(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        return self.conn

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def solve_interactive(self, user_inputs):
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name FROM sections")
            sections = cursor.fetchall()

            if not user_inputs: return []
            results = []

            for section_id, section_name in sections:
                cursor.execute("""
                    SELECT r.gradation_id, r.weight, g.g_type, g.num1, g.num2, g.property_id
                    FROM relations r JOIN gradations g ON r.gradation_id = g.id
                    WHERE r.section_id = ?
                """, (section_id,))
                section_rels = cursor.fetchall()

                # Общий вес ОС для расчета 100%
                total_distro_weight = sum(w for _, w, _, _, _, _ in section_rels)

                # Группируем признаки ОС из базы по их свойствам
                distro_props = {}
                for grad_id, weight, g_type, num1, num2, prop_id in section_rels:
                    if prop_id not in distro_props: distro_props[prop_id] = []
                    distro_props[prop_id].append({'grad_id': grad_id, 'weight': weight})

                matched_weight = 0.0
                is_valid = True # Флаг: подходит ли эта ОС под ВСЕ выбранные фильтры

                # Идем по всем критериям, которые выбрал пользователь
                for prop_id, u_in_list in user_inputs.items():
                    # ЖЕСТКОЕ ПРАВИЛО 1: Если у ОС вообще не описано это свойство в базе - она вылетает
                    if prop_id not in distro_props:
                        is_valid = False
                        break
                    
                    matched_any_in_prop = False
                    best_w = 0.0

                    # ЖЕСТКОЕ ПРАВИЛО 2: Хотя бы одно из выбранных пользователем значений (ИЛИ) 
                    # должно совпасть с тем, что есть у ОС в базе
                    for u_in in u_in_list:
                        u_val = u_in["value"]
                        for grad in distro_props[prop_id]:
                            if u_val == grad['grad_id']:
                                matched_any_in_prop = True
                                if grad['weight'] > best_w:
                                    best_w = grad['weight']
                    
                    if not matched_any_in_prop:
                        is_valid = False # Не совпало - ОС удаляется из выдачи
                        break
                    
                    matched_weight += best_w

                # Если ОС прошла через все фильтры
                if is_valid and total_distro_weight > 0:
                    perc = (matched_weight / total_distro_weight) * 100
                    results.append((section_id, section_name, perc))

            results.sort(key=lambda x: x[2], reverse=True)
            return results

    def init_empty_database(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS sections (id INTEGER PRIMARY KEY, name TEXT UNIQUE)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, name TEXT UNIQUE)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY, event_id INTEGER, name TEXT)"
        )
        # ДОБАВЛЕНЫ ПОЛЯ ТИПОВ
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gradations (
                id INTEGER PRIMARY KEY, property_id INTEGER, name TEXT,
                g_type TEXT DEFAULT 'text', num1 REAL, num2 REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY, section_id INTEGER, gradation_id INTEGER,
                weight REAL, UNIQUE(section_id, gradation_id)
            )
        """)
        self.conn.commit()

    # Разделы, События, Свойства - ОСТАЮТСЯ КАК БЫЛИ
    def get_sections(self):
        return (
            self.conn.cursor()
            .execute("SELECT id, name FROM sections ORDER BY name")
            .fetchall()
        )

    def add_section(self, name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO sections (name) VALUES (?)", (name,))
        self.conn.commit()
        return cursor.lastrowid

    def delete_section(self, section_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sections WHERE id = ?", (section_id,))
        cursor.execute("DELETE FROM relations WHERE section_id = ?", (section_id,))
        self.conn.commit()

    def get_events(self):
        return (
            self.conn.cursor()
            .execute("SELECT id, name FROM events ORDER BY name")
            .fetchall()
        )

    def add_event(self, name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO events (name) VALUES (?)", (name,))
        self.conn.commit()
        return cursor.lastrowid

    def delete_event(self, event_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM properties WHERE event_id = ?", (event_id,))
        for (prop_id,) in cursor.fetchall():
            cursor.execute(
                "SELECT id FROM gradations WHERE property_id = ?", (prop_id,)
            )
            for (grad_id,) in cursor.fetchall():
                cursor.execute(
                    "DELETE FROM relations WHERE gradation_id = ?", (grad_id,)
                )
            cursor.execute("DELETE FROM gradations WHERE property_id = ?", (prop_id,))
        cursor.execute("DELETE FROM properties WHERE event_id = ?", (event_id,))
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.conn.commit()

    def get_properties(self, event_id):
        return (
            self.conn.cursor()
            .execute(
                "SELECT id, name FROM properties WHERE event_id = ? ORDER BY name",
                (event_id,),
            )
            .fetchall()
        )

    def add_property(self, event_id, name):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO properties (event_id, name) VALUES (?, ?)", (event_id, name)
        )
        self.conn.commit()
        return cursor.lastrowid

    def delete_property(self, property_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM gradations WHERE property_id = ?", (property_id,)
        )
        for (grad_id,) in cursor.fetchall():
            cursor.execute("DELETE FROM relations WHERE gradation_id = ?", (grad_id,))
        cursor.execute("DELETE FROM gradations WHERE property_id = ?", (property_id,))
        cursor.execute("DELETE FROM properties WHERE id = ?", (property_id,))
        self.conn.commit()

    # ========== Градации (ОБНОВЛЕНЫ ДЛЯ ТИПОВ) ==========
    def get_gradations(self, property_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, g_type, num1, num2 FROM gradations WHERE property_id = ? ORDER BY name",
            (property_id,),
        )
        return cursor.fetchall()

    def add_gradation(self, property_id, name, g_type="text", num1=None, num2=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO gradations (property_id, name, g_type, num1, num2) VALUES (?, ?, ?, ?, ?)",
            (property_id, name, g_type, num1, num2),
        )
        self.conn.commit()
        return cursor.lastrowid

    def delete_gradation(self, gradation_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM relations WHERE gradation_id = ?", (gradation_id,))
        cursor.execute("DELETE FROM gradations WHERE id = ?", (gradation_id,))
        self.conn.commit()

    # ========== Связи (ОСТАЮТСЯ КАК БЫЛИ) ==========
    def get_relations(self, section_id=None):
        cursor = self.conn.cursor()
        if section_id:
            cursor.execute(
                """
                SELECT r.id, s.name, e.name, g.name, r.weight
                FROM relations r JOIN sections s ON r.section_id = s.id
                JOIN gradations g ON r.gradation_id = g.id
                JOIN properties p ON g.property_id = p.id
                JOIN events e ON p.event_id = e.id WHERE r.section_id = ? ORDER BY s.name, r.weight DESC
            """,
                (section_id,),
            )
        else:
            cursor.execute("""
                SELECT r.id, s.name, e.name, g.name, r.weight
                FROM relations r JOIN sections s ON r.section_id = s.id
                JOIN gradations g ON r.gradation_id = g.id
                JOIN properties p ON g.property_id = p.id
                JOIN events e ON p.event_id = e.id ORDER BY s.name, r.weight DESC
            """)
        return cursor.fetchall()

    def add_relation(self, section_id, gradation_id, weight):
        self.conn.cursor().execute(
            "INSERT INTO relations (section_id, gradation_id, weight) VALUES (?, ?, ?)",
            (section_id, gradation_id, weight),
        )
        self.conn.commit()

    def delete_relation(self, relation_id):
        self.conn.cursor().execute("DELETE FROM relations WHERE id = ?", (relation_id,))
        self.conn.commit()

    def update_relation_weight(self, relation_id, weight):
        self.conn.cursor().execute(
            "UPDATE relations SET weight = ? WHERE id = ?", (weight, relation_id)
        )
        self.conn.commit()

    def normalize_relations(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM sections")
        for (section_id,) in cursor.fetchall():
            cursor.execute(
                "SELECT id, weight FROM relations WHERE section_id = ?", (section_id,)
            )
            rels = cursor.fetchall()
            if rels:
                total = sum(w for _, w in rels)
                if total > 0:
                    for rel_id, w in rels:
                        cursor.execute(
                            "UPDATE relations SET weight = ? WHERE id = ?",
                            (w / total, rel_id),
                        )
        self.conn.commit()

    def get_all_relations_with_names(self):
        return (
            self.conn.cursor()
            .execute("""
            SELECT s.name, e.name, g.name, r.weight
            FROM relations r JOIN sections s ON r.section_id = s.id
            JOIN gradations g ON r.gradation_id = g.id
            JOIN properties p ON g.property_id = p.id
            JOIN events e ON p.event_id = e.id ORDER BY s.name, r.weight DESC
        """)
            .fetchall()
        )

    # ========== РЕДАКТИРОВАНИЕ (UPDATE) ==========
    def update_section(self, section_id, new_name):
        self.conn.cursor().execute(
            "UPDATE sections SET name = ? WHERE id = ?", (new_name, section_id)
        )
        self.conn.commit()

    def update_event(self, event_id, new_name):
        self.conn.cursor().execute(
            "UPDATE events SET name = ? WHERE id = ?", (new_name, event_id)
        )
        self.conn.commit()

    def update_property(self, property_id, new_name):
        self.conn.cursor().execute(
            "UPDATE properties SET name = ? WHERE id = ?", (new_name, property_id)
        )
        self.conn.commit()

    def get_gradation_by_id(self, gradation_id):
        """Получает текущие данные градации для заполнения окна редактирования"""
        return (
            self.conn.cursor()
            .execute(
                "SELECT name, g_type, num1, num2 FROM gradations WHERE id = ?",
                (gradation_id,),
            )
            .fetchone()
        )

    def update_gradation(self, gradation_id, name, g_type, num1, num2):
        self.conn.cursor().execute(
            "UPDATE gradations SET name = ?, g_type = ?, num1 = ?, num2 = ? WHERE id = ?",
            (name, g_type, num1, num2, gradation_id),
        )
        self.conn.commit()

    # ========== НОВЫЙ УМНЫЙ РЕШАТЕЛЬ ==========
    def solve(self, user_inputs):
        """
        user_inputs: словарь {property_id: {'type': str, 'value': user_val}}
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM sections")
        sections = cursor.fetchall()

        results = []
        for section_id, section_name in sections:
            cursor.execute(
                """
                SELECT r.gradation_id, r.weight, g.g_type, g.num1, g.num2, g.property_id
                FROM relations r
                JOIN gradations g ON r.gradation_id = g.id
                WHERE r.section_id = ?
            """,
                (section_id,),
            )
            section_rels = cursor.fetchall()

            if not section_rels:
                continue

            total_weight = 0
            match_score = 0

            for grad_id, weight, g_type, num1, num2, prop_id in section_rels:
                total_weight += weight
                if prop_id not in user_inputs:
                    continue

                u_in = user_inputs[prop_id]
                u_type = u_in["type"]
                u_val = u_in["value"]

                ratio = 0.0

                # Текст или бинарный (точное совпадение ID градации)
                if g_type in ("text", "binary"):
                    if u_type in ("text", "binary") and u_val == grad_id:
                        ratio = 1.0

                # Числовой (чем ближе, тем выше балл, макс отклонение = 20 для расчета)
                elif g_type == "numeric" and u_type == "numeric":
                    target = float(num1)
                    user_num = float(u_val)
                    diff = abs(user_num - target)
                    ratio = max(0.0, 1.0 - (diff / max(target, 10.0)))

                # Диапазонный (Пересечение диапазонов)
                elif g_type == "range" and u_type == "range":
                    u_min, u_max = u_val
                    t_min, t_max = float(num1), float(num2)
                    inter_min = max(u_min, t_min)
                    inter_max = min(u_max, t_max)

                    if inter_min <= inter_max:
                        inter_len = inter_max - inter_min
                        union_len = max(u_max, t_max) - min(u_min, t_min)
                        ratio = (inter_len / union_len) if union_len > 0 else 1.0

                # Умножаем процент попадания на ВЕС признака!
                match_score += ratio * weight

            final_ratio = (match_score / total_weight) if total_weight > 0 else 0.0
            results.append((section_name, match_score, total_weight, final_ratio))

        results.sort(key=lambda x: x[3], reverse=True)
        return results

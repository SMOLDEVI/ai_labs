from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


class ExplanationDialog(QDialog):
    """Окно с детальным объяснением, почему дистрибутив получил такой процент."""

    def __init__(self, section_name, perc, details, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Пояснение: {section_name} — {perc:.1f}%")
        self.setMinimumSize(750, 500)

        layout = QVBoxLayout(self)

        # --- Заголовок ---
        header = QLabel(f"📊  {section_name}  —  итого {perc:.1f}%")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        if perc >= 70:
            header.setStyleSheet("color: green; padding: 10px;")
        elif perc >= 40:
            header.setStyleSheet("color: orange; padding: 10px;")
        else:
            header.setStyleSheet("color: red; padding: 10px;")
        layout.addWidget(header)

        # --- Формула ---
        formula = QLabel(
            f"Формула:  Σ(score × weight) / Σ(total_weight)  =  "
            f"{details['matched_weight']:.2f} / {details['max_possible']:.2f}  =  {perc:.1f}%"
        )
        formula.setFont(QFont("Consolas", 10))
        formula.setAlignment(Qt.AlignCenter)
        formula.setStyleSheet("background: #f0f0f0; padding: 8px; border-radius: 5px;")
        layout.addWidget(formula)

        # --- Таблица ---
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Свойство", "Вы ввели", "Градация в БЗ (вес)",
            "Score (0-1)", "Балл (score×вес)", "Макс. возможный"
        ])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)

        rows = details["rows"]
        table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            item0 = QTableWidgetItem(row["prop_name"])
            item0.setFont(QFont("Arial", 9, QFont.Bold))
            table.setItem(i, 0, item0)

            table.setItem(i, 1, QTableWidgetItem(row["user_input"]))
            table.setItem(i, 2, QTableWidgetItem(row["grad_info"]))

            score_item = QTableWidgetItem(f"{row['score']:.3f}")
            if row["score"] >= 0.8:
                score_item.setBackground(QColor(200, 255, 200))
            elif row["score"] >= 0.4:
                score_item.setBackground(QColor(255, 240, 200))
            elif row["score"] > 0:
                score_item.setBackground(QColor(255, 220, 200))
            else:
                score_item.setBackground(QColor(255, 180, 180))
            table.setItem(i, 3, score_item)

            table.setItem(i, 4, QTableWidgetItem(f"{row['weighted']:.2f}"))
            table.setItem(i, 5, QTableWidgetItem(f"{row['max_possible']:.2f}"))

            if row["score"] == 0:
                for col in range(6):
                    cell = table.item(i, col)
                    if cell:
                        cell.setBackground(QColor(255, 200, 200))
                        cell.setForeground(QColor(150, 0, 0))

        layout.addWidget(table)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)


class SolveDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.user_inputs = {}
        self.current_event_id = None
        self.current_prop_id = None
        self.current_prop_is_numeric = False
        self.last_results = []
        self.locked_section_ids = None
        self.init_ui()
        self.load_events()

    def init_ui(self):
        self.setWindowTitle("Система выдвижения гипотез")
        self.setMinimumSize(850, 600)
        main_layout = QGridLayout(self)
        main_layout.setSpacing(10)

        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_layout = QVBoxLayout()
        btn_reset = QPushButton("Отменить весь выбор")
        btn_reset.clicked.connect(self.reset_all)
        left_layout.addWidget(btn_reset)

        self.img_label = QLabel("БЗ")
        self.img_label.setFixedSize(150, 150)
        self.img_label.setStyleSheet(
            "background-color: purple; color: white; font-weight: bold; font-size: 40px;"
        )
        self.img_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.img_label, alignment=Qt.AlignCenter)

        left_layout.addWidget(QLabel("Возможные решения (двойной клик — пояснение)"))
        self.res_list = QListWidget()
        self.res_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        left_layout.addWidget(self.res_list)

        btn_solve = QPushButton("Вывод гипотезы")
        btn_solve.clicked.connect(self.full_recalculate)
        left_layout.addWidget(btn_solve)
        main_layout.addLayout(left_layout, 0, 0, 2, 1)

        # --- ЦЕНТРАЛЬНАЯ ПАНЕЛЬ ---
        mid_layout = QVBoxLayout()
        mid_layout.addWidget(QLabel("Выбор признаков", alignment=Qt.AlignCenter))

        lists_layout = QHBoxLayout()
        self.ev_list = QListWidget()
        self.ev_list.itemClicked.connect(self.on_event_clicked)
        lists_layout.addWidget(self.ev_list)
        self.prop_list = QListWidget()
        self.prop_list.itemClicked.connect(self.on_prop_clicked)
        lists_layout.addWidget(self.prop_list)
        mid_layout.addLayout(lists_layout)

        self.grad_list = QListWidget()
        self.grad_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        mid_layout.addWidget(self.grad_list)

        self.input_mode_widget = QWidget()
        mode_layout = QHBoxLayout(self.input_mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.addWidget(QLabel("Режим ввода:"))
        self.input_mode_combo = QComboBox()
        self.input_mode_combo.addItems(["Точное значение", "Диапазон"])
        self.input_mode_combo.currentIndexChanged.connect(self.update_input_mode_ui)
        mode_layout.addWidget(self.input_mode_combo)
        self.input_mode_widget.hide()
        mid_layout.addWidget(self.input_mode_widget)

        self.numeric_widget = QWidget()
        num_layout = QHBoxLayout(self.numeric_widget)
        num_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_input_from = QLabel("Значение:")
        num_layout.addWidget(self.lbl_input_from)
        self.input_spin1 = QDoubleSpinBox()
        self.input_spin1.setRange(-99999, 999999)
        self.input_spin1.setDecimals(2)
        num_layout.addWidget(self.input_spin1)
        self.lbl_input_to = QLabel("До:")
        num_layout.addWidget(self.lbl_input_to)
        self.input_spin2 = QDoubleSpinBox()
        self.input_spin2.setRange(-99999, 999999)
        self.input_spin2.setDecimals(2)
        num_layout.addWidget(self.input_spin2)
        self.numeric_widget.hide()
        mid_layout.addWidget(self.numeric_widget)

        btn_layout = QHBoxLayout()
        btn_unsel = QPushButton("Отменить выбор")
        btn_sel = QPushButton("Выбрать")
        btn_sel.clicked.connect(self.select_gradation)
        btn_unsel.clicked.connect(self.deselect_gradation)
        btn_layout.addWidget(btn_unsel)
        btn_layout.addWidget(btn_sel)
        mid_layout.addLayout(btn_layout)
        main_layout.addLayout(mid_layout, 0, 1, 2, 1)

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_layout = QVBoxLayout()
        right_layout.addWidget(
            QLabel("Выбранные признаки", alignment=Qt.AlignCenter)
        )
        self.info_list = QListWidget()
        right_layout.addWidget(self.info_list)
        main_layout.addLayout(right_layout, 1, 2, 1, 1)
        main_layout.setColumnStretch(1, 2)

    # -------------------------------------------------------
    # ЗАГРУЗКА ДАННЫХ
    # -------------------------------------------------------
    def load_events(self):
        self.ev_list.clear()
        for eid, name in self.db.get_events():
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, eid)
            self.ev_list.addItem(item)

    def on_event_clicked(self, item):
        self.current_event_id = item.data(Qt.UserRole)
        self.current_prop_id = None
        self.grad_list.clear()
        self.prop_list.clear()
        self.input_mode_widget.hide()
        self.numeric_widget.hide()
        for pid, name in self.db.get_properties(self.current_event_id):
            p_item = QListWidgetItem(name)
            p_item.setData(Qt.UserRole, pid)
            self.prop_list.addItem(p_item)

    def on_prop_clicked(self, item):
        if not item:
            return
        self.current_prop_id = item.data(Qt.UserRole)
        self.grad_list.clear()

        grads = self.db.get_gradations(self.current_prop_id)

        self.current_prop_is_numeric = False
        for gid, name, g_type, num1, num2 in grads:
            if g_type in ("numeric", "range"):
                self.current_prop_is_numeric = True
                break

        for gid, name, g_type, num1, num2 in grads:
            if g_type == "numeric":
                display = f"{name}  [эталон: {num1}]"
            elif g_type == "range":
                display = f"{name}  [эталон: {num1} — {num2}]"
            else:
                display = name

            g_item = QListWidgetItem(display)
            g_item.setData(Qt.UserRole, gid)
            g_item.setData(Qt.UserRole + 1, g_type)
            g_item.setData(Qt.UserRole + 2, num1)
            g_item.setData(Qt.UserRole + 3, num2)

            if self.current_prop_id in self.user_inputs:
                for u in self.user_inputs[self.current_prop_id]:
                    if u["type"] == "exact_id" and u.get("value") == gid:
                        g_item.setText(f"✓  {display}")
                        break

            self.grad_list.addItem(g_item)

        self.grad_list.addItem("Пока неизвестно")

        if self.current_prop_is_numeric:
            self.input_mode_widget.show()
            self.numeric_widget.show()
            self.update_input_mode_ui()

            if self.current_prop_id in self.user_inputs:
                data = self.user_inputs[self.current_prop_id]
                if data:
                    d = data[0]
                    if d["type"] == "numeric":
                        self.input_mode_combo.setCurrentIndex(0)
                        self.input_spin1.setValue(d["value"])
                    elif d["type"] == "range":
                        self.input_mode_combo.setCurrentIndex(1)
                        self.input_spin1.setValue(d["value"][0])
                        self.input_spin2.setValue(d["value"][1])
        else:
            self.input_mode_widget.hide()
            self.numeric_widget.hide()

    def update_input_mode_ui(self):
        mode = self.input_mode_combo.currentIndex()
        if mode == 0:
            self.lbl_input_from.setText("Значение:")
            self.lbl_input_to.hide()
            self.input_spin2.hide()
        else:
            self.lbl_input_from.setText("От:")
            self.lbl_input_to.show()
            self.input_spin2.show()

    # -------------------------------------------------------
    # ВЫБОР / ОТМЕНА
    # -------------------------------------------------------
    def select_gradation(self):
        if not self.current_prop_id:
            return

        if self.current_prop_is_numeric:
            mode = self.input_mode_combo.currentIndex()
            prop_name = ""
            if self.prop_list.currentItem():
                prop_name = self.prop_list.currentItem().text()

            if mode == 0:
                val = self.input_spin1.value()
                self.user_inputs[self.current_prop_id] = [{
                    "type": "numeric",
                    "value": val,
                    "name": f"{prop_name}: точно {val}"
                }]
            else:
                v1 = self.input_spin1.value()
                v2 = self.input_spin2.value()
                if v1 > v2:
                    v1, v2 = v2, v1
                self.user_inputs[self.current_prop_id] = [{
                    "type": "range",
                    "value": (v1, v2),
                    "name": f"{prop_name}: от {v1} до {v2}"
                }]

            self.update_info_list()
            self.on_prop_clicked(self.prop_list.currentItem())
            self.recalculate()
            return

        items = self.grad_list.selectedItems()
        if not items:
            return

        if self.current_prop_id not in self.user_inputs:
            self.user_inputs[self.current_prop_id] = []

        for item in items:
            if item.text().strip() == "Пока неизвестно":
                if self.current_prop_id in self.user_inputs:
                    del self.user_inputs[self.current_prop_id]
                self.update_info_list()
                self.on_prop_clicked(self.prop_list.currentItem())
                self.recalculate()
                return

            gid = item.data(Qt.UserRole)
            if gid is None:
                continue

            raw_name = item.text().replace("✓  ", "")
            exists = any(
                x.get("value") == gid
                for x in self.user_inputs[self.current_prop_id]
            )
            if not exists:
                self.user_inputs[self.current_prop_id].append({
                    "type": "exact_id",
                    "value": gid,
                    "name": raw_name
                })

        self.update_info_list()
        self.on_prop_clicked(self.prop_list.currentItem())
        self.recalculate()

    def deselect_gradation(self):
        if not self.current_prop_id:
            return

        if self.current_prop_is_numeric:
            if self.current_prop_id in self.user_inputs:
                del self.user_inputs[self.current_prop_id]
            self.input_spin1.setValue(0)
            self.input_spin2.setValue(0)
            self.update_info_list()
            self.on_prop_clicked(self.prop_list.currentItem())
            self.recalculate()
            return

        items = self.grad_list.selectedItems()
        if not items:
            return
        for item in items:
            gid = item.data(Qt.UserRole)
            if self.current_prop_id in self.user_inputs:
                self.user_inputs[self.current_prop_id] = [
                    x for x in self.user_inputs[self.current_prop_id]
                    if x.get("value") != gid
                ]
        if self.current_prop_id in self.user_inputs and not self.user_inputs[self.current_prop_id]:
            del self.user_inputs[self.current_prop_id]

        self.update_info_list()
        self.on_prop_clicked(self.prop_list.currentItem())
        self.recalculate()

    def reset_all(self):
        self.user_inputs.clear()
        self.locked_section_ids = None
        self.last_results.clear()
        self.update_info_list()
        self.res_list.clear()
        self.input_spin1.setValue(0)
        self.input_spin2.setValue(0)
        if self.prop_list.currentItem():
            self.on_prop_clicked(self.prop_list.currentItem())

    def update_info_list(self):
        self.info_list.clear()
        for prop_id, data_list in self.user_inputs.items():
            for data in data_list:
                self.info_list.addItem(f"• {data['name']}")

    # -------------------------------------------------------
    # КЛИК ПО РЕЗУЛЬТАТУ → ПОЯСНЕНИЕ
    # -------------------------------------------------------
    def on_result_double_clicked(self, item):
        section_id = item.data(Qt.UserRole)
        if section_id is None:
            return

        for res in self.last_results:
            if res["section_id"] == section_id:
                dlg = ExplanationDialog(
                    res["section_name"],
                    res["perc"],
                    res["details"],
                    self
                )
                dlg.exec_()
                return

    # -------------------------------------------------------
    # РАСЧЁТ РЕЗУЛЬТАТОВ
    # -------------------------------------------------------
    def full_recalculate(self):
        """Кнопка 'Вывод гипотезы' — полный пересчёт, новый список."""
        self.locked_section_ids = None
        self._do_recalculate()

    def recalculate(self):
        """Автоматический пересчёт при смене критерия.
        Если список уже сформирован — только обновляем проценты."""
        self._do_recalculate()

    def _do_recalculate(self):
        self.res_list.clear()
        self.last_results.clear()

        if not self.user_inputs:
            self.locked_section_ids = None
            return

        good_results, partial_results = self.solve(self.user_inputs)

        # ── Если список ещё не зафиксирован — фиксируем ──
        if self.locked_section_ids is None:
            if good_results:
                self.locked_section_ids = [r["section_id"] for r in good_results]
            elif partial_results:
                self.locked_section_ids = [r["section_id"] for r in partial_results]
            else:
                self.res_list.addItem("❌ Совпадений не найдено вообще")
                return

        # ── Фильтруем: показываем ТОЛЬКО зафиксированные ──
        locked = set(self.locked_section_ids)

        filtered_good = [r for r in good_results if r["section_id"] in locked]
        filtered_partial = [r for r in partial_results if r["section_id"] in locked]

        # Те, кто был в списке, но теперь вообще выпал — показать с 0%
        found_ids = {r["section_id"] for r in filtered_good + filtered_partial}
        missing_ids = locked - found_ids

        if missing_ids:
            cursor = self.db.conn.cursor()
            for sid in missing_ids:
                cursor.execute("SELECT name FROM sections WHERE id = ?", (sid,))
                row = cursor.fetchone()
                if row:
                    filtered_partial.append({
                        "section_id": sid,
                        "section_name": row[0],
                        "perc": 0.0,
                        "details": {
                            "matched_weight": 0.0,
                            "max_possible": 1.0,
                            "rows": [],
                        },
                    })

        # Объединяем и сортируем
        all_results = filtered_good + filtered_partial
        all_results.sort(key=lambda x: x["perc"], reverse=True)

        if not all_results:
            self.res_list.addItem("❌ Совпадений не найдено вообще")
            return

        # ── Отображаем ──
        good_ids = {r["section_id"] for r in filtered_good}
        has_good = len(good_ids) > 0

        if has_good:
            header = QListWidgetItem(
                f"✅ Результаты ({len(all_results)}):"
            )
            header.setFlags(Qt.NoItemFlags)
            header.setBackground(QColor(180, 230, 180))
            header.setForeground(QColor(30, 100, 30))
        else:
            header = QListWidgetItem(
                "⚠️  Точных совпадений нет. Ближайшие варианты:"
            )
            header.setFlags(Qt.NoItemFlags)
            header.setBackground(QColor(255, 240, 200))
            header.setForeground(QColor(150, 100, 0))
        self.res_list.addItem(header)

        for res in all_results:
            perc = res["perc"]
            item = QListWidgetItem(
                f"  {res['section_name']}  —  {perc:.1f}%"
            )
            item.setData(Qt.UserRole, res["section_id"])
            if perc >= 70:
                item.setBackground(QColor(200, 255, 200))
            elif perc >= 40:
                item.setBackground(QColor(255, 230, 180))
            elif perc > 0:
                item.setBackground(QColor(255, 210, 210))
            else:
                item.setBackground(QColor(220, 220, 220))
                item.setForeground(QColor(100, 100, 100))
            self.res_list.addItem(item)

        self.last_results = all_results

    def solve(self, user_inputs):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, name FROM sections")
        sections = cursor.fetchall()

        if not user_inputs:
            return [], []

        # Имена свойств и градаций для пояснения
        prop_names = {}
        cursor.execute("SELECT id, name FROM properties")
        for pid, pname in cursor.fetchall():
            prop_names[pid] = pname

        grad_names = {}
        cursor.execute("SELECT id, name, g_type, num1, num2 FROM gradations")
        for gid, gname, gtype, n1, n2 in cursor.fetchall():
            grad_names[gid] = {
                "name": gname, "g_type": gtype, "num1": n1, "num2": n2
            }

        good_results = []
        partial_results = []

        for section_id, section_name in sections:
            cursor.execute("""
                SELECT r.gradation_id, r.weight, g.g_type, g.num1, g.num2, g.property_id
                FROM relations r
                JOIN gradations g ON r.gradation_id = g.id
                WHERE r.section_id = ?
            """, (section_id,))
            section_rels = cursor.fetchall()

            if not section_rels:
                continue

            # total_weight = сумма ВСЕХ весов дистрибутива
            total_weight = sum(w for _, w, _, _, _, _ in section_rels)
            if total_weight == 0:
                continue

            distro_props = {}
            for grad_id, weight, g_type, num1, num2, prop_id in section_rels:
                if prop_id not in distro_props:
                    distro_props[prop_id] = []
                distro_props[prop_id].append({
                    "grad_id": grad_id,
                    "weight":  weight,
                    "g_type":  g_type,
                    "num1":    num1,
                    "num2":    num2,
                })

            matched_weight = 0.0
            missed_props = 0
            detail_rows = []

            for prop_id, u_in_list in user_inputs.items():
                p_name = prop_names.get(prop_id, f"Свойство #{prop_id}")

                user_str_parts = []
                for u_in in u_in_list:
                    user_str_parts.append(u_in.get("name", str(u_in["value"])))
                user_str = "; ".join(user_str_parts)

                if prop_id not in distro_props:
                    missed_props += 1
                    detail_rows.append({
                        "prop_name":    p_name,
                        "user_input":   user_str,
                        "grad_info":    "— нет данных в БЗ —",
                        "score":        0.0,
                        "weighted":     0.0,
                        "max_possible": 0.0,
                    })
                    continue

                best_possible = max(g["weight"] for g in distro_props[prop_id])

                best_score = 0.0
                best_weighted = 0.0
                best_grad_info = ""

                for u_in in u_in_list:
                    for grad in distro_props[prop_id]:
                        score = self._compare(u_in["type"], u_in["value"], grad)
                        weighted = score * grad["weight"]

                        gid = grad["grad_id"]
                        gi = grad_names.get(gid, {})
                        g_display = gi.get("name", "?")
                        g_display += f"  (вес={grad['weight']})"

                        if weighted > best_weighted:
                            best_score = score
                            best_weighted = weighted
                            best_grad_info = g_display

                if best_score == 0:
                    missed_props += 1
                    if distro_props[prop_id]:
                        top_g = max(distro_props[prop_id], key=lambda g: g["weight"])
                        gid = top_g["grad_id"]
                        gi = grad_names.get(gid, {})
                        best_grad_info = (
                            f"{gi.get('name', '?')}  (вес={top_g['weight']}) ← не совпало"
                        )

                matched_weight += best_weighted

                detail_rows.append({
                    "prop_name":    p_name,
                    "user_input":   user_str,
                    "grad_info":    best_grad_info,
                    "score":        best_score,
                    "weighted":     best_weighted,
                    "max_possible": best_possible,
                })

            perc = (matched_weight / total_weight) * 100

            if perc < 1.0:
                continue

            result_entry = {
                "section_id":   section_id,
                "section_name": section_name,
                "perc":         perc,
                "details": {
                    "matched_weight": matched_weight,
                    "max_possible":   total_weight,
                    "rows":           detail_rows,
                },
            }

            if missed_props == 0:
                good_results.append(result_entry)
            elif matched_weight > 0:
                partial_results.append(result_entry)

        good_results.sort(key=lambda x: x["perc"], reverse=True)
        partial_results.sort(key=lambda x: x["perc"], reverse=True)
        partial_results = partial_results[:5]

        return good_results, partial_results

    def _compare(self, u_type, u_val, grad):
        g_type = grad["g_type"]
        g_num1 = float(grad["num1"]) if grad["num1"] is not None else 0.0
        g_num2 = float(grad["num2"]) if grad["num2"] is not None else 0.0

        if u_type == "exact_id":
            return 1.0 if u_val == grad["grad_id"] else 0.0

        if u_type == "numeric":
            user_num = float(u_val)
            if g_type == "numeric":
                diff = abs(user_num - g_num1)
                max_dev = max(abs(g_num1), 10.0)
                return max(0.0, 1.0 - (diff / max_dev))
            elif g_type == "range":
                if g_num1 <= user_num <= g_num2:
                    return 1.0
                else:
                    dist = min(abs(user_num - g_num1), abs(user_num - g_num2))
                    span = max(g_num2 - g_num1, 10.0)
                    return max(0.0, 1.0 - (dist / span))
            elif g_type == "text":
                return 0.0

        if u_type == "range":
            u_min, u_max = float(u_val[0]), float(u_val[1])
            if g_type == "range":
                inter_min = max(u_min, g_num1)
                inter_max = min(u_max, g_num2)
                if inter_min <= inter_max:
                    inter_len = inter_max - inter_min
                    union_len = max(u_max, g_num2) - min(u_min, g_num1)
                    return (inter_len / union_len) if union_len > 0 else 1.0
                else:
                    dist = min(abs(u_min - g_num2), abs(u_max - g_num1))
                    span = max(u_max - u_min, g_num2 - g_num1, 10.0)
                    return max(0.0, 1.0 - (dist / span))
            elif g_type == "numeric":
                if u_min <= g_num1 <= u_max:
                    return 1.0
                else:
                    dist = min(abs(g_num1 - u_min), abs(g_num1 - u_max))
                    span = max(u_max - u_min, 10.0)
                    return max(0.0, 1.0 - (dist / span))
            elif g_type == "text":
                return 0.0

        return 0.0

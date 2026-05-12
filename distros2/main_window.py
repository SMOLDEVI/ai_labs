import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from solve_window import SolveDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = None
        self.current_mode = -1 
        self.current_mid_id = None
        self.current_right_id = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Интегрированная среда для создания экспертной системы")
        self.setMinimumSize(1000, 650)
        
        menubar = self.menuBar()
        menu_main = menubar.addMenu("Меню")
        act_new = QAction("Новая БЗ", self)
        act_new.triggered.connect(self.new_kb)
        menu_main.addAction(act_new)
        act_open = QAction("Открыть БЗ", self)
        act_open.triggered.connect(self.open_kb)
        menu_main.addAction(act_open)
        menu_main.addAction("Выход", self.close)

        menu_solve = menubar.addMenu("Решение задач")
        act_solve = QAction("Запустить систему", self)
        act_solve.triggered.connect(self.solve_task)
        menu_solve.addAction(act_solve)
        menubar.addMenu("Помощь")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setEnabled(False) 
        
        main_layout = QVBoxLayout(self.central_widget)
        
        # --- ВЕРХНЯЯ ПОЛОВИНА ---
        top_layout = QHBoxLayout()
        
        sec_layout = QVBoxLayout()
        sec_layout.addWidget(QLabel("Разделы", alignment=Qt.AlignCenter))
        dummy_btn = QPushButton(" ")
        dummy_btn.setFlat(True)
        dummy_btn.setEnabled(False)
        dummy_btn.setStyleSheet("background: transparent; border: none;")
        sec_layout.addWidget(dummy_btn)
        
        self.mode_list = QListWidget()
        self.mode_list.addItem("Дистрибутивы")
        self.mode_list.addItem("Критерии подбора")
        self.mode_list.itemClicked.connect(self.on_mode_clicked)
        self.mode_list.setStyleSheet("QListWidget::item { padding: 10px; font-size: 14px; }")
        sec_layout.addWidget(self.mode_list)
        top_layout.addLayout(sec_layout, stretch=1)
        
        self.mid_group = QWidget()
        mid_layout = QVBoxLayout(self.mid_group)
        mid_layout.setContentsMargins(0,0,0,0)
        self.lbl_mid = QLabel("События", alignment=Qt.AlignCenter)
        mid_layout.addWidget(self.lbl_mid)
        
        mid_btns = QHBoxLayout()
        self.btn_mid_del = QPushButton("Удалить")
        self.btn_mid_add = QPushButton("Создать")
        self.btn_mid_add.clicked.connect(self.add_mid)
        self.btn_mid_del.clicked.connect(self.del_mid)
        mid_btns.addWidget(self.btn_mid_del); mid_btns.addWidget(self.btn_mid_add)
        mid_layout.addLayout(mid_btns)
        
        self.list_mid = QListWidget()
        self.list_mid.itemClicked.connect(self.on_mid_clicked)
        mid_layout.addWidget(self.list_mid)
        top_layout.addWidget(self.mid_group, stretch=1)
        
        self.right_group = QWidget()
        right_layout = QVBoxLayout(self.right_group)
        right_layout.setContentsMargins(0,0,0,0)
        self.lbl_right = QLabel("Свойства события", alignment=Qt.AlignCenter)
        right_layout.addWidget(self.lbl_right)
        
        right_btns = QHBoxLayout()
        self.btn_right_del = QPushButton("Удалить")
        self.btn_right_add = QPushButton("Создать")
        self.btn_right_add.clicked.connect(self.add_right)
        self.btn_right_del.clicked.connect(self.del_right)
        right_btns.addWidget(self.btn_right_del); right_btns.addWidget(self.btn_right_add)
        right_layout.addLayout(right_btns)
        
        self.list_right = QListWidget()
        self.list_right.itemClicked.connect(self.on_right_clicked)
        right_layout.addWidget(self.list_right)
        top_layout.addWidget(self.right_group, stretch=1)

        main_layout.addLayout(top_layout, stretch=2)

        # --- НИЖНЯЯ ПОЛОВИНА ---
        self.bottom_stack = QStackedWidget()
        
        # СТРАНИЦА 0: РЕДАКТИРОВАНИЕ ГРАДАЦИЙ
        page_grads = QWidget()
        pg_layout = QHBoxLayout(page_grads)
        pg_layout.setContentsMargins(0,0,0,0)
        
        # --- ПАНЕЛЬ РЕДАКТОРА (ОБНОВЛЕННАЯ) ---
        editor_box = QGroupBox("Создание градации")
        ed_layout = QVBoxLayout(editor_box)

        # 1. Название
        lay_name = QHBoxLayout()
        lay_name.addWidget(QLabel("Название (текст):"))
        self.grad_name_edit = QLineEdit()
        self.grad_name_edit.setPlaceholderText('Например: Медленно (80 минут)')
        lay_name.addWidget(self.grad_name_edit)
        ed_layout.addLayout(lay_name)

        # 2. Выбор типа
        lay_type = QHBoxLayout()
        lay_type.addWidget(QLabel("Тип значения:"))
        self.grad_type_combo = QComboBox()
        self.grad_type_combo.addItems(["Обычный текст", "Точное число", "Диапазон чисел"])
        self.grad_type_combo.currentIndexChanged.connect(self.update_grad_ui)
        lay_type.addWidget(self.grad_type_combo)
        ed_layout.addLayout(lay_type)
        
        # 3. Числовые поля
        self.num_widget = QWidget()
        lay_num = QHBoxLayout(self.num_widget)
        lay_num.setContentsMargins(0,0,0,0)
        
        self.lbl_num1 = QLabel("Число:")
        self.grad_spin1 = QDoubleSpinBox()
        self.grad_spin1.setRange(-99999, 999999) # Большой лимит
        
        self.lbl_num2 = QLabel("До:")
        self.grad_spin2 = QDoubleSpinBox()
        self.grad_spin2.setRange(-99999, 999999)

        lay_num.addWidget(self.lbl_num1)
        lay_num.addWidget(self.grad_spin1)
        lay_num.addWidget(self.lbl_num2)
        lay_num.addWidget(self.grad_spin2)
        ed_layout.addWidget(self.num_widget)

        # Кнопки
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        btn_cancel = QPushButton("Отменить")
        btn_accept = QPushButton("Принять")
        btn_accept.clicked.connect(self.accept_gradation)
        btn_cancel.clicked.connect(self.cancel_gradation)
        btn_lay.addWidget(btn_cancel)
        btn_lay.addWidget(btn_accept)
        ed_layout.addLayout(btn_lay)

        ed_layout.addStretch()
        pg_layout.addWidget(editor_box, stretch=2)

        # Инициализация интерфейса редактора
        self.update_grad_ui()

        # Правая часть (Список градаций)
        grad_box = QVBoxLayout()
        grad_box.addWidget(QLabel("Возможные градации свойства", alignment=Qt.AlignCenter))
        self.btn_grad_del = QPushButton("Удалить")
        self.btn_grad_del.clicked.connect(self.del_gradation)
        grad_box.addWidget(self.btn_grad_del)
        self.list_grads = QListWidget()
        grad_box.addWidget(self.list_grads)
        
        pg_layout.addLayout(grad_box, stretch=1) 
        self.bottom_stack.addWidget(page_grads)
        
        # СТРАНИЦА 1: ПРИВЯЗКА ПРИЗНАКОВ К ДИСТРИБУТИВУ
        page_rels = QWidget()
        pr_layout = QHBoxLayout(page_rels)
        pr_layout.setContentsMargins(0,0,0,0)
        avail_box = QVBoxLayout()
        avail_box.addWidget(QLabel("Доступные признаки", alignment=Qt.AlignCenter))
        self.list_avail = QListWidget()
        avail_box.addWidget(self.list_avail)
        pr_layout.addLayout(avail_box, stretch=2)
        
        link_btns = QVBoxLayout()
        link_btns.addStretch()
        self.btn_link = QPushButton(">>")
        self.btn_unlink = QPushButton("<<")
        self.btn_link.clicked.connect(self.link_gradation)
        self.btn_unlink.clicked.connect(self.unlink_gradation)
        link_btns.addWidget(self.btn_link); link_btns.addWidget(self.btn_unlink)
        link_btns.addStretch()
        pr_layout.addLayout(link_btns)
        
        linked_box = QVBoxLayout()
        linked_box.addWidget(QLabel("Признаки дистрибутива", alignment=Qt.AlignCenter))
        self.list_linked = QListWidget()
        linked_box.addWidget(self.list_linked)
        pr_layout.addLayout(linked_box, stretch=2)
        self.bottom_stack.addWidget(page_rels)
        
        main_layout.addWidget(self.bottom_stack, stretch=1)
        self.statusBar().showMessage("Откройте или создайте базу знаний")

    # --- ЛОГИКА ФАЙЛОВ ---
    def new_kb(self):
        from database import DatabaseManager
        path, _ = QFileDialog.getSaveFileName(self, "Создать", "", "*.kb")
        if path:
            self.db = DatabaseManager()
            self.db.connect(path)
            self.db.init_empty_database()
            self.refresh_all()

    def open_kb(self):
        from database import DatabaseManager
        path, _ = QFileDialog.getOpenFileName(self, "Открыть", "", "*.kb")
        if path:
            self.db = DatabaseManager()
            self.db.connect(path)
            self.refresh_all()

    def refresh_all(self):
        self.central_widget.setEnabled(True)
        self.mode_list.setCurrentRow(0)
        self.on_mode_clicked(self.mode_list.item(0))

    def solve_task(self):
        if not self.db: return
        SolveDialog(self.db, self).exec_()

    # --- ЛОГИКА ПЕРЕКЛЮЧЕНИЯ РЕЖИМОВ ---
    def on_mode_clicked(self, item):
        mode = self.mode_list.row(item)
        self.current_mode = mode
        self.current_mid_id = None
        self.current_right_id = None
        self.list_mid.clear(); self.list_right.clear(); self.list_grads.clear(); self.list_linked.clear()
        
        if mode == 0:
            self.lbl_mid.setText("Дистрибутивы")
            self.right_group.hide()
            self.bottom_stack.setCurrentIndex(1)
            self.refresh_mid_list()
            self.refresh_avail_list() 
        else:
            self.lbl_mid.setText("События")
            self.right_group.show()
            self.bottom_stack.setCurrentIndex(0) 
            self.refresh_mid_list()

    def on_mid_clicked(self, item):
        self.current_mid_id = item.data(Qt.UserRole)
        self.current_right_id = None
        if self.current_mode == 0: self.refresh_linked_list()
        else: self.list_grads.clear(); self.refresh_right_list()

    def on_right_clicked(self, item):
        self.current_right_id = item.data(Qt.UserRole)
        self.refresh_grads_list()

    def refresh_mid_list(self):
        self.list_mid.clear()
        if not self.db: return
        if self.current_mode == 0:
            for sid, name in self.db.get_sections():
                it = QListWidgetItem(name); it.setData(Qt.UserRole, sid); self.list_mid.addItem(it)
        else:
            for eid, name in self.db.get_events():
                it = QListWidgetItem(name); it.setData(Qt.UserRole, eid); self.list_mid.addItem(it)

    def refresh_right_list(self):
        self.list_right.clear()
        if not self.db or not self.current_mid_id: return
        for pid, name in self.db.get_properties(self.current_mid_id):
            it = QListWidgetItem(name); it.setData(Qt.UserRole, pid); self.list_right.addItem(it)

    def refresh_grads_list(self):
        self.list_grads.clear()
        if not self.db or not self.current_right_id: return
        for gid, name, g_type, _, _ in self.db.get_gradations(self.current_right_id):
            it = QListWidgetItem(name); it.setData(Qt.UserRole, gid); self.list_grads.addItem(it)

    def refresh_avail_list(self):
        self.list_avail.clear()
        if not self.db: return
        cursor = self.db.conn.cursor()
        cursor.execute('''SELECT g.id, e.name, p.name, g.name FROM gradations g 
                          JOIN properties p ON g.property_id = p.id 
                          JOIN events e ON p.event_id = e.id ORDER BY e.name, p.name''')
        for gid, e, p, g in cursor.fetchall():
            it = QListWidgetItem(f"{e} → {p} → {g}"); it.setData(Qt.UserRole, gid); self.list_avail.addItem(it)

    def refresh_linked_list(self):
        self.list_linked.clear()
        if not self.db or not self.current_mid_id: return
        for rel_id, s_name, e_name, g_name, weight in self.db.get_relations(self.current_mid_id):
            it = QListWidgetItem(f"{e_name} → {g_name} [Вес: {weight}]")
            it.setData(Qt.UserRole, rel_id); self.list_linked.addItem(it)

    def add_mid(self):
        name, ok = QInputDialog.getText(self, "Создать", "Имя:")
        if ok and name:
            if self.current_mode == 0: self.db.add_section(name)
            else: self.db.add_event(name)
            self.refresh_mid_list()

    def del_mid(self):
        it = self.list_mid.currentItem()
        if it:
            if self.current_mode == 0: self.db.delete_section(it.data(Qt.UserRole))
            else: self.db.delete_event(it.data(Qt.UserRole))
            self.refresh_mid_list(); self.list_right.clear(); self.list_grads.clear()

    def add_right(self):
        if not self.current_mid_id: return
        name, ok = QInputDialog.getText(self, "Создать", "Имя:")
        if ok and name: self.db.add_property(self.current_mid_id, name); self.refresh_right_list()

    def del_right(self):
        it = self.list_right.currentItem()
        if it: self.db.delete_property(it.data(Qt.UserRole)); self.refresh_right_list(); self.list_grads.clear()

    # --- ЛОГИКА НОВОЙ ПАНЕЛИ ГРАДАЦИЙ ---
    def update_grad_ui(self):
        """Прячет или показывает поля чисел в зависимости от выбора в Combobox"""
        idx = self.grad_type_combo.currentIndex()
        if idx == 0: # Текст
            self.num_widget.hide()
        elif idx == 1: # Число
            self.num_widget.show()
            self.lbl_num1.setText("Число:")
            self.lbl_num2.hide()
            self.grad_spin2.hide()
        elif idx == 2: # Диапазон
            self.num_widget.show()
            self.lbl_num1.setText("От:")
            self.lbl_num2.show()
            self.grad_spin2.show()

    def accept_gradation(self):
        if not self.current_right_id:
            return QMessageBox.warning(self, "Ошибка", "Выберите свойство сверху справа!")
        
        name = self.grad_name_edit.text().strip()
        if not name: 
            return QMessageBox.warning(self, "Ошибка", "Введите название градации!")

        idx = self.grad_type_combo.currentIndex()
        if idx == 0:
            g_type = "text"; n1, n2 = None, None
        elif idx == 1:
            g_type = "numeric"; n1, n2 = self.grad_spin1.value(), None
        else:
            g_type = "range"; n1, n2 = self.grad_spin1.value(), self.grad_spin2.value()

        self.db.add_gradation(self.current_right_id, name, g_type, n1, n2)
        self.refresh_grads_list()
        self.cancel_gradation()

    def cancel_gradation(self):
        self.grad_name_edit.clear()
        self.grad_spin1.setValue(0)
        self.grad_spin2.setValue(0)
        self.grad_type_combo.setCurrentIndex(0)

    def del_gradation(self):
        it = self.list_grads.currentItem()
        if it: self.db.delete_gradation(it.data(Qt.UserRole)); self.refresh_grads_list()

    def link_gradation(self):
            if not self.current_mid_id: return QMessageBox.warning(self, "Ошибка", "Выберите Дистрибутив сверху!")
            it = self.list_avail.currentItem()
            if not it: return QMessageBox.warning(self, "Ошибка", "Выберите признак слева внизу!")
            
            # Запрашиваем предварительный вес (система его потом отнормирует)
            weight, ok = QInputDialog.getDouble(self, "Вес связи", "Укажите сырой вес (система его отнормирует):", 5.0, 0.0, 10.0, 1)
            if ok:
                try: 
                    # 1. Добавляем связь
                    self.db.add_relation(self.current_mid_id, it.data(Qt.UserRole), weight)
                    # 2. АВТОМАТИЧЕСКИ НОРМИРУЕМ БАЗУ
                    self.db.normalize_relations()
                    # 3. Обновляем список, чтобы показать уже отнормированные дробные веса
                    self.refresh_linked_list()
                except sqlite3.IntegrityError: 
                    QMessageBox.warning(self, "Внимание", "Эта градация уже привязана!")

    def unlink_gradation(self):
        it = self.list_linked.currentItem()
        if it: 
            # 1. Удаляем связь
            self.db.delete_relation(it.data(Qt.UserRole))
            # 2. АВТОМАТИЧЕСКИ ПЕРЕСЧИТЫВАЕМ НОРМИРОВКУ для оставшихся
            self.db.normalize_relations()
            # 3. Обновляем список
            self.refresh_linked_list()

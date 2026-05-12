from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class SolveDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.user_inputs = {}  
        self.current_event_id = None
        self.current_prop_id = None
        self.init_ui()
        self.load_events()

    def init_ui(self):
        self.setWindowTitle("Система выдвижения гипотез")
        self.setMinimumSize(850, 600)
        main_layout = QGridLayout(self)
        main_layout.setSpacing(10)

        left_layout = QVBoxLayout()
        btn_reset = QPushButton("Отменить весь выбор")
        btn_reset.clicked.connect(self.reset_all)
        left_layout.addWidget(btn_reset)
        
        self.img_label = QLabel("БЗ")
        self.img_label.setFixedSize(150, 150)
        self.img_label.setStyleSheet("background-color: purple; color: white; font-weight: bold; font-size: 40px;")
        self.img_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.img_label, alignment=Qt.AlignCenter)
        
        left_layout.addWidget(QLabel("Возможные решения"))
        self.res_list = QListWidget()
        left_layout.addWidget(self.res_list)
        
        btn_solve = QPushButton("Вывод гипотезы")
        btn_solve.clicked.connect(self.recalculate)
        left_layout.addWidget(btn_solve)
        main_layout.addLayout(left_layout, 0, 0, 2, 1)

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
        # ВКЛЮЧАЕМ МНОЖЕСТВЕННЫЙ ВЫБОР ОБРАТНО
        self.grad_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        mid_layout.addWidget(self.grad_list)
        
        btn_layout = QHBoxLayout()
        btn_unsel = QPushButton("Отменить")
        btn_sel = QPushButton("Выбрать")
        btn_sel.clicked.connect(self.select_gradation)
        btn_unsel.clicked.connect(self.deselect_gradation)
        btn_layout.addWidget(btn_unsel)
        btn_layout.addWidget(btn_sel)
        mid_layout.addLayout(btn_layout)
        main_layout.addLayout(mid_layout, 0, 1, 2, 1)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Связь гипотез с признаком", alignment=Qt.AlignCenter))
        self.info_list = QListWidget()
        right_layout.addWidget(self.info_list)
        main_layout.addLayout(right_layout, 1, 2, 1, 1)
        main_layout.setColumnStretch(1, 2)

    def load_events(self):
        self.ev_list.clear()
        for eid, name in self.db.get_events():
            item = QListWidgetItem(name); item.setData(Qt.UserRole, eid); self.ev_list.addItem(item)

    def on_event_clicked(self, item):
        self.current_event_id = item.data(Qt.UserRole)
        self.current_prop_id = None
        self.grad_list.clear(); self.prop_list.clear()
        for pid, name in self.db.get_properties(self.current_event_id):
            p_item = QListWidgetItem(name); p_item.setData(Qt.UserRole, pid); self.prop_list.addItem(p_item)

    def on_prop_clicked(self, item):
        self.current_prop_id = item.data(Qt.UserRole)
        self.grad_list.clear()
        for gid, name, g_type, _, _ in self.db.get_gradations(self.current_prop_id):
            g_item = QListWidgetItem(name); g_item.setData(Qt.UserRole, gid)
            is_selected = False
            if self.current_prop_id in self.user_inputs:
                for u in self.user_inputs[self.current_prop_id]:
                    if u["value"] == gid: is_selected = True; break
            if is_selected: g_item.setText(f"< {name} >")
            self.grad_list.addItem(g_item)
        self.grad_list.addItem("Пока неизвестно")

    def select_gradation(self):
        items = self.grad_list.selectedItems()
        if not items or not self.current_prop_id: return
        if self.current_prop_id not in self.user_inputs: self.user_inputs[self.current_prop_id] = []

        for item in items:
            if item.text() == "Пока неизвестно": self.deselect_gradation(); return
            gid = item.data(Qt.UserRole)
            raw_name = item.text().replace("< ", "").replace(" >", "")
            exists = any(x["value"] == gid for x in self.user_inputs[self.current_prop_id])
            if not exists:
                self.user_inputs[self.current_prop_id].append({"type": "exact_id", "value": gid, "name": raw_name})

        self.update_info_list()
        self.on_prop_clicked(self.prop_list.currentItem())
        self.recalculate()

    def deselect_gradation(self):
        items = self.grad_list.selectedItems()
        if not items or not self.current_prop_id: return
        for item in items:
            gid = item.data(Qt.UserRole)
            if self.current_prop_id in self.user_inputs:
                self.user_inputs[self.current_prop_id] = [x for x in self.user_inputs[self.current_prop_id] if x["value"] != gid]
        if self.current_prop_id in self.user_inputs and not self.user_inputs[self.current_prop_id]:
            del self.user_inputs[self.current_prop_id]
        self.update_info_list()
        if self.prop_list.currentItem(): self.on_prop_clicked(self.prop_list.currentItem())
        self.recalculate()

    def reset_all(self):
        self.user_inputs.clear(); self.update_info_list(); self.res_list.clear()
        if self.prop_list.currentItem(): self.on_prop_clicked(self.prop_list.currentItem())

    def update_info_list(self):
        self.info_list.clear()
        for prop_id, data_list in self.user_inputs.items():
            for data in data_list: self.info_list.addItem(f"• {data['name']}")

    def recalculate(self):
            from PyQt5.QtGui import QColor # Добавили импорт цвета внутри метода
            self.res_list.clear()
            if not self.user_inputs: return
            
            results = self.db.solve_interactive(self.user_inputs)
            
            if not results: 
                self.res_list.addItem("❌ Нет подходящих решений")
                return
                
            for sid, name, perc in results:
                item = QListWidgetItem(f"{name} ({perc:.1f}%)")
                
                # Логика раскраски по порогам из отчета
                if perc >= 70:
                    # Зеленый - Идеальное соответствие
                    item.setBackground(QColor(200, 255, 200)) 
                elif 40 <= perc < 70:
                    # Оранжевый - Частичное соответствие
                    item.setBackground(QColor(255, 230, 180)) 
                else:
                    # Красный - Низкое соответствие
                    item.setBackground(QColor(255, 210, 210))
                    
                self.res_list.addItem(item)

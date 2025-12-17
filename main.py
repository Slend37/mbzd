import tkinter as tk
from datetime import datetime
from collections import defaultdict

class CompactStopwatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Компактные секундомеры с сортировкой кругов")
        self.root.geometry("1050x650")  # Уменьшил ширину окна
        
        # Список для хранения всех секундомеров
        self.stopwatches = []
        self.current_large_view = None  # Текущий отображаемый крупно секундомер
        
        # Создаем основной интерфейс
        self.create_widgets()
        
    def create_widgets(self):
        # Основной контейнер с разделением на левую, центральную и правую части
        main_container = tk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ЛЕВАЯ ПАНЕЛЬ - список секундомеров (увеличил ширину)
        left_panel = tk.Frame(main_container, width=580)  # Увеличил ширину
        left_panel.pack(side="left", fill="both", expand=True)
        
        # Заголовок левой панели
        left_title = tk.Label(
            left_panel, 
            text="Список секундомеров",
            font=("Arial", 12, "bold")
        )
        left_title.pack(pady=5)
        
        # Кнопка для добавления нового секундомера
        add_button = tk.Button(
            left_panel,
            text="+ Добавить секундомер",
            command=self.add_stopwatch,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white",
            height=1,
            width=20
        )
        add_button.pack(pady=5)
        
        # Заголовки колонок (слегка изменил ширины)
        headers_frame = tk.Frame(left_panel)
        headers_frame.pack(fill="x", pady=5)
        
        # Колонки
        tk.Label(headers_frame, text="Название", font=("Arial", 10, "bold"), width=22).grid(row=0, column=0, padx=5)
        tk.Label(headers_frame, text="Время", font=("Arial", 10, "bold"), width=15).grid(row=0, column=1, padx=5)
        tk.Label(headers_frame, text="Управление", font=("Arial", 10, "bold"), width=42).grid(row=0, column=2, padx=5)  # Увеличил ширину
        
        # Фрейм для секундомеров с прокруткой
        self.canvas = tk.Canvas(left_panel)
        self.scrollbar = tk.Scrollbar(left_panel, orient="vertical", command=self.canvas.yview)
        self.stopwatches_frame = tk.Frame(self.canvas)
        
        self.stopwatches_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.stopwatches_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.scrollbar.pack(side="right", fill="y")
        
        # Кнопка сброса всех секундомеров
        reset_all_button = tk.Button(
            left_panel,
            text="Сбросить все",
            command=self.reset_all,
            font=("Arial", 10),
            bg="#f44336",
            fg="white",
            height=1,
            width=20
        )
        reset_all_button.pack(pady=10)
        
        # ЦЕНТРАЛЬНАЯ ПАНЕЛЬ - увеличенный вид выбранного секундомера
        center_panel = tk.Frame(main_container, width=320, relief="ridge", borderwidth=2, bg="#f0f0f0")  # Уменьшил ширину
        center_panel.pack(side="left", fill="both", expand=True, padx=(10, 5))
        
        # Заголовок центральной панели
        center_title = tk.Label(
            center_panel, 
            text="Увеличенный вид",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        )
        center_title.pack(pady=20)
        
        # Контейнер для увеличенного отображения
        self.large_view_container = tk.Frame(center_panel, bg="#f0f0f0")
        self.large_view_container.pack(fill="both", expand=True, padx=15, pady=10)  # Уменьшил отступы
        
        # Изначальное сообщение
        self.large_view_label = tk.Label(
            self.large_view_container,
            text="Выберите секундомер\nдля увеличенного отображения",
            font=("Arial", 11),  # Уменьшил шрифт
            bg="#f0f0f0",
            fg="#666",
            justify="center"
        )
        self.large_view_label.pack(expand=True)
        
        # ПРАВАЯ ПАНЕЛЬ - круги всех секундомеров, отсортированные по кругам и времени
        right_panel = tk.Frame(main_container, width=280, relief="ridge", borderwidth=2, bg="#e8f5e8")  # Уменьшил ширину
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Заголовок правой панели
        right_title = tk.Label(
            right_panel, 
            text="Круги (сортировка: номер → время)",
            font=("Arial", 12, "bold"),  # Уменьшил шрифт
            bg="#e8f5e8"
        )
        right_title.pack(pady=15)
        
        # Контейнер для отображения кругов с прокруткой
        self.laps_canvas = tk.Canvas(right_panel, bg="#e8f5e8")
        self.laps_scrollbar = tk.Scrollbar(right_panel, orient="vertical", command=self.laps_canvas.yview)
        self.laps_frame = tk.Frame(self.laps_canvas, bg="#e8f5e8")
        
        self.laps_frame.bind(
            "<Configure>",
            lambda e: self.laps_canvas.configure(scrollregion=self.laps_canvas.bbox("all"))
        )
        
        self.laps_canvas.create_window((0, 0), window=self.laps_frame, anchor="nw")
        self.laps_canvas.configure(yscrollcommand=self.laps_scrollbar.set, bg="#e8f5e8")
        
        self.laps_canvas.pack(side="left", fill="both", expand=True, padx=(8, 0))  # Уменьшил отступ
        self.laps_scrollbar.pack(side="right", fill="y")
        
        # Статистика кругов (более компактная)
        self.laps_stats_frame = tk.Frame(right_panel, bg="#e8f5e8")
        self.laps_stats_frame.pack(fill="x", pady=(5, 0), padx=8)
        
        self.total_laps_label = tk.Label(
            self.laps_stats_frame,
            text="Кругов: 0",
            font=("Arial", 9),  # Уменьшил шрифт
            bg="#e8f5e8",
            fg="#2E7D32"
        )
        self.total_laps_label.pack(side="left", padx=5)
        
        self.active_stopwatches_label = tk.Label(
            self.laps_stats_frame,
            text="Активных: 0",
            font=("Arial", 9),  # Уменьшил шрифт
            bg="#e8f5e8",
            fg="#2E7D32"
        )
        self.active_stopwatches_label.pack(side="left", padx=5)
        
        # Изначально создаем 3 секундомера
        for i in range(3):
            self.add_stopwatch()
        
    def add_stopwatch(self):
        """Добавляет новый секундомер"""
        stopwatch = CompactStopwatch(self.stopwatches_frame, len(self.stopwatches) + 1, self)
        self.stopwatches.append(stopwatch)
        
        # Обновляем нумерацию всех секундомеров
        self.renumber_stopwatches()
        self.update_all_laps_display()
        
    def remove_stopwatch(self, stopwatch):
        """Удаляет секундомер"""
        if len(self.stopwatches) > 1:  # Оставляем хотя бы один секундомер
            # Если удаляем тот, что отображается крупно
            if self.current_large_view == stopwatch:
                self.clear_large_view()
            
            stopwatch.destroy()
            self.stopwatches.remove(stopwatch)
            self.renumber_stopwatches()
            self.update_all_laps_display()
    
    def renumber_stopwatches(self):
        """Перенумеровывает все секундомеры"""
        for i, stopwatch in enumerate(self.stopwatches, 1):
            stopwatch.number = i
            stopwatch.update_name()
    
    def reset_all(self):
        """Сброс всех секундомеров"""
        for stopwatch in self.stopwatches:
            stopwatch.reset()
        
        # Очищаем увеличенный вид
        self.clear_large_view()
        self.update_all_laps_display()
    
    def show_large_view(self, stopwatch):
        """Показывает увеличенный вид выбранного секундомера"""
        self.current_large_view = stopwatch
        
        # Очищаем контейнер
        for widget in self.large_view_container.winfo_children():
            widget.destroy()
        
        # Отображаем имя секундомера
        selected_name_label = tk.Label(
            self.large_view_container,
            text=stopwatch.name_var.get(),
            font=("Arial", 13, "bold"),  # Уменьшил шрифт
            bg="#f0f0f0",
            fg="#2196F3"
        )
        selected_name_label.pack(pady=(10, 5))
        
        # Отображаем время крупным шрифтом
        large_time_label = tk.Label(
            self.large_view_container,
            text=stopwatch.time_label.cget("text"),
            font=("Courier New", 30, "bold"),  # Уменьшил шрифт
            bg="#f0f0f0",
            fg="#2196F3"
        )
        large_time_label.pack(pady=15)
        
        # Создаем кнопки управления (более компактные)
        large_buttons_frame = tk.Frame(self.large_view_container, bg="#f0f0f0")
        
        # Кнопка Старт для увеличенного вида
        large_start_btn = tk.Button(
            large_buttons_frame,
            text="СТАРТ",
            command=stopwatch.start,
            width=8,  # Уменьшил ширину
            height=1,  # Уменьшил высоту
            bg="#4CAF50" if not stopwatch.running else "#81C784",
            fg="white",
            font=("Arial", 10, "bold"),  # Уменьшил шрифт
            state="normal" if not stopwatch.running else "disabled"
        )
        large_start_btn.pack(side="left", padx=2, pady=5)
        
        # Кнопка Стоп для увеличенного вида
        large_stop_btn = tk.Button(
            large_buttons_frame,
            text="СТОП",
            command=stopwatch.stop,
            width=8,
            height=1,
            bg="#f44336" if stopwatch.running else "#E57373",
            fg="white",
            font=("Arial", 10, "bold"),
            state="normal" if stopwatch.running else "disabled"
        )
        large_stop_btn.pack(side="left", padx=2, pady=5)
        
        # Кнопка Круг для увеличенного вида
        large_lap_btn = tk.Button(
            large_buttons_frame,
            text="КРУГ",
            command=stopwatch.record_lap,
            width=8,
            height=1,
            bg="#FF9800",
            fg="white",
            font=("Arial", 10, "bold"),
            state="normal" if stopwatch.running else "disabled"
        )
        large_lap_btn.pack(side="left", padx=2, pady=5)
        
        large_buttons_frame.pack(pady=5)
        
        # Отображаем круги выбранного секундомера
        laps_label = tk.Label(
            self.large_view_container,
            text="Круги этого секундомера:",
            font=("Arial", 10, "bold"),  # Уменьшил шрифт
            bg="#f0f0f0",
            fg="#333"
        )
        laps_label.pack(pady=(15, 3), anchor="w")
        
        # Фрейм для кругов выбранного секундомера
        selected_laps_frame = tk.Frame(self.large_view_container, bg="#f0f0f0")
        selected_laps_frame.pack(fill="x", pady=3)
        
        # Отображаем круги
        if stopwatch.lap_times:
            for i, lap_time in enumerate(stopwatch.lap_times, 1):
                lap_text = f"Круг {i}: {stopwatch.format_time(lap_time)}"
                lap_label = tk.Label(
                    selected_laps_frame,
                    text=lap_text,
                    font=("Courier New", 8),  # Уменьшил шрифт
                    bg="#f0f0f0",
                    anchor="w"
                )
                lap_label.pack(fill="x", pady=1)
        else:
            no_laps_label = tk.Label(
                selected_laps_frame,
                text="Круги еще не зафиксированы",
                font=("Arial", 8),  # Уменьшил шрифт
                bg="#f0f0f0",
                fg="#666",
                anchor="w"
            )
            no_laps_label.pack(fill="x", pady=3)
        
        # Кнопка скрытия увеличенного вида
        hide_button = tk.Button(
            self.large_view_container,
            text="Скрыть увеличенный вид",
            command=self.clear_large_view,
            font=("Arial", 9),  # Уменьшил шрифт
            bg="#9E9E9E",
            fg="white"
        )
        hide_button.pack(pady=15)
        
        # Запускаем обновление времени в увеличенном виде
        self.update_large_view(large_time_label, stopwatch)
    
    def update_large_view(self, time_label, stopwatch):
        """Обновляет увеличенный вид"""
        if self.current_large_view == stopwatch:
            # Обновляем время
            if stopwatch.running:
                current_elapsed = (stopwatch.elapsed_time + 
                                  (datetime.now() - stopwatch.start_time).total_seconds())
                time_label.config(text=stopwatch.format_time(current_elapsed))
            
            # Планируем следующее обновление
            self.root.after(10, lambda: self.update_large_view(time_label, stopwatch))
    
    def clear_large_view(self):
        """Очищает увеличенный вид"""
        self.current_large_view = None
        
        # Очищаем контейнер
        for widget in self.large_view_container.winfo_children():
            widget.destroy()
        
        # Показываем первоначальное сообщение
        self.large_view_label = tk.Label(
            self.large_view_container,
            text="Выберите секундомер\nдля увеличенного отображения",
            font=("Arial", 11),
            bg="#f0f0f0",
            fg="#666",
            justify="center"
        )
        self.large_view_label.pack(expand=True)
    
    def get_all_laps_sorted_by_number_and_time(self):
        """Возвращает все круги всех секундомеров, сгруппированные по номеру круга и отсортированные по времени"""
        # Собираем все круги всех секундомеров
        all_laps = []
        
        for stopwatch in self.stopwatches:
            for lap_num, lap_time in enumerate(stopwatch.lap_times, 1):
                all_laps.append({
                    'stopwatch_name': stopwatch.name_var.get(),
                    'lap_number': lap_num,
                    'lap_time': lap_time,
                    'stopwatch_color': stopwatch.get_color()
                })
        
        # Сортируем по номеру круга
        all_laps.sort(key=lambda x: x['lap_number'])
        
        # Группируем по номеру круга
        laps_by_number = defaultdict(list)
        for lap in all_laps:
            laps_by_number[lap['lap_number']].append(lap)
        
        # Сортируем круги внутри каждой группы по времени (от меньшего к большему)
        for lap_number in laps_by_number:
            laps_by_number[lap_number].sort(key=lambda x: x['lap_time'])
        
        return laps_by_number
    
    def update_all_laps_display(self):
        """Обновляет отображение всех кругов в правой панели, сгруппированных по номеру круга и отсортированных по времени"""
        # Очищаем текущее отображение
        for widget in self.laps_frame.winfo_children():
            widget.destroy()
        
        # Получаем все круги, сгруппированные по номеру и отсортированные по времени
        laps_by_number = self.get_all_laps_sorted_by_number_and_time()
        
        # Подсчитываем статистику
        total_laps = sum(len(laps) for laps in laps_by_number.values())
        active_stopwatches = sum(1 for sw in self.stopwatches if sw.running)
        
        # Обновляем статистику
        self.total_laps_label.config(text=f"Кругов: {total_laps}")
        self.active_stopwatches_label.config(text=f"Активных: {active_stopwatches}")
        
        if laps_by_number:
            # Отображаем круги, сгруппированные по номеру
            for lap_number in sorted(laps_by_number.keys()):
                # Заголовок для группы кругов с одинаковым номером
                group_header = tk.Label(
                    self.laps_frame,
                    text=f"Круг №{lap_number}:",
                    font=("Arial", 10, "bold"),  # Уменьшил шрифт
                    bg="#e8f5e8",
                    fg="#2E7D32",
                    anchor="w"
                )
                group_header.pack(fill="x", pady=(8, 3), padx=5)  # Уменьшил отступы
                
                # Отображаем все круги с этим номером, отсортированные по времени
                for lap_info in laps_by_number[lap_number]:
                    # Форматируем время
                    time_str = self.format_lap_time(lap_info['lap_time'])
                    
                    # Создаем метку для круга с цветом секундомера
                    lap_text = f"  {lap_info['stopwatch_name']}: {time_str}"
                    lap_label = tk.Label(
                        self.laps_frame,
                        text=lap_text,
                        font=("Courier New", 8),  # Уменьшил шрифт
                        bg="#e8f5e8",
                        fg=lap_info['stopwatch_color'],
                        anchor="w"
                    )
                    lap_label.pack(fill="x", pady=1, padx=12)  # Уменьшил отступы
        
        # Если нет кругов ни у одного секундомера
        if not laps_by_number:
            no_laps_label = tk.Label(
                self.laps_frame,
                text="Круги еще не зафиксированы\nнажмите кнопку 'Круг'\nво время работы секундомера",
                font=("Arial", 9),  # Уменьшил шрифт
                bg="#e8f5e8",
                fg="#666",
                justify="center"
            )
            no_laps_label.pack(expand=True, pady=15)
    
    def format_lap_time(self, seconds):
        """Форматирование времени круга"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds - int(seconds)) * 100)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}.{centisecs:02d}"

class CompactStopwatch:
    def __init__(self, parent, number, app):
        self.parent = parent
        self.app = app
        self.number = number
        self.running = False
        self.start_time = None
        self.elapsed_time = 0
        self.lap_times = []  # Список для хранения времени кругов
        self.colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#FF5722", "#009688", "#795548", "#607D8B"]
        self.color = self.colors[(number - 1) % len(self.colors)]  # Назначаем цвет в зависимости от номера
        
        # Создаем фрейм для этого секундомера в одну строку
        self.frame = tk.Frame(parent, height=38)  # Уменьшил высоту
        self.frame.pack(fill="x", pady=2, padx=5)
        self.frame.pack_propagate(False)
        
        # Создаем элементы интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Поле для названия (22 символа) с возможностью выбора для увеличенного вида
        self.name_var = tk.StringVar(value=f"Секундомер {self.number}")
        self.name_entry = tk.Entry(
            self.frame,
            textvariable=self.name_var,
            width=22,  # Увеличил ширину
            font=("Arial", 9)  # Уменьшил шрифт
        )
        self.name_entry.grid(row=0, column=0, padx=5, sticky="w")
        self.name_entry.bind("<KeyRelease>", lambda e: self.app.update_all_laps_display())
        
        # Отображение времени (15 символов) - кликабельно для выбора в увеличенный вид
        self.time_label = tk.Label(
            self.frame,
            text="00:00:00.00",
            font=("Courier New", 10, "bold"),  # Уменьшил шрифт
            fg=self.color,
            width=15,
            anchor="w",
            cursor="hand2"
        )
        self.time_label.grid(row=0, column=1, padx=5, sticky="w")
        self.time_label.bind("<Button-1>", lambda e: self.select_for_large_view())
        
        # Фрейм для кнопок управления
        buttons_frame = tk.Frame(self.frame)
        buttons_frame.grid(row=0, column=2, padx=5, sticky="w")
        
        # Кнопка Старт (уменьшил ширину)
        self.start_btn = tk.Button(
            buttons_frame,
            text="Старт",
            command=self.start,
            width=7,  # Уменьшил ширину
            bg="#4CAF50",
            fg="white",
            font=("Arial", 8)  # Уменьшил шрифт
        )
        self.start_btn.pack(side="left", padx=1)  # Уменьшил отступ
        
        # Кнопка Круг (уменьшил ширину)
        self.lap_btn = tk.Button(
            buttons_frame,
            text="Круг",
            command=self.record_lap,
            width=7,
            bg="#FF9800",
            fg="white",
            font=("Arial", 8),
            state="disabled"
        )
        self.lap_btn.pack(side="left", padx=1)
        
        # Кнопка Стоп (уменьшил ширину)
        self.stop_btn = tk.Button(
            buttons_frame,
            text="Стоп",
            command=self.stop,
            width=7,
            bg="#f44336",
            fg="white",
            font=("Arial", 8),
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=1)
        
        # Кнопка Сброс (уменьшил ширину)
        reset_btn = tk.Button(
            buttons_frame,
            text="Сброс",
            command=self.reset,
            width=7,
            bg="#9E9E9E",
            fg="white",
            font=("Arial", 8)
        )
        reset_btn.pack(side="left", padx=1)
        
        # Кнопка "Увеличить" для отображения в центральной панели
        enlarge_btn = tk.Button(
            buttons_frame,
            text="🔍",
            command=self.select_for_large_view,
            width=3,
            bg=self.color,
            fg="white",
            font=("Arial", 8)  # Уменьшил шрифт
        )
        enlarge_btn.pack(side="left", padx=1)
        
        # Кнопка удаления
        remove_btn = tk.Button(
            buttons_frame,
            text="✕",
            command=self.remove,
            width=3,
            bg="#333",
            fg="white",
            font=("Arial", 8)  # Уменьшил шрифт
        )
        remove_btn.pack(side="left", padx=1)
        
        # Индикатор кругов (количество) - уменьшил ширину
        self.lap_indicator = tk.Label(
            self.frame,
            text="Круги: 0",
            font=("Arial", 8),  # Уменьшил шрифт
            fg=self.color,
            width=8  # Уменьшил ширину
        )
        self.lap_indicator.grid(row=0, column=3, padx=5, sticky="w")
        
    def get_color(self):
        """Возвращает цвет этого секундомера"""
        return self.color
    
    def start(self):
        """Запуск секундомера"""
        if not self.running:
            self.running = True
            self.start_time = datetime.now()
            self.start_btn.config(state="disabled", bg="#81C784")
            self.stop_btn.config(state="normal", bg="#f44336")
            self.lap_btn.config(state="normal", bg="#FF9800")
            self.update_time()
            
            # Обновляем увеличенный вид, если этот секундомер отображается
            if self.app.current_large_view == self:
                self.app.show_large_view(self)
            
            # Обновляем статистику
            self.app.update_all_laps_display()
    
    def stop(self):
        """Остановка секундомера"""
        if self.running:
            self.running = False
            if self.start_time:
                self.elapsed_time += (datetime.now() - self.start_time).total_seconds()
            self.start_btn.config(state="normal", bg="#4CAF50")
            self.stop_btn.config(state="disabled", bg="#E57373")
            self.lap_btn.config(state="disabled", bg="#FFB74D")
            
            # Обновляем увеличенный вид, если этот секундомер отображается
            if self.app.current_large_view == self:
                self.app.show_large_view(self)
            
            # Обновляем статистику
            self.app.update_all_laps_display()
    
    def update_time(self):
        """Обновление отображения времени"""
        if self.running:
            current_elapsed = self.elapsed_time + (datetime.now() - self.start_time).total_seconds()
            self.display_time(current_elapsed)
            self.frame.after(10, self.update_time)
    
    def display_time(self, seconds):
        """Отображение времени в формате ЧЧ:ММ:СС.сс"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds - int(seconds)) * 100)
        
        if hours > 0:
            time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
        else:
            time_str = f"{minutes:02d}:{secs:02d}.{centisecs:02d}"
            
        self.time_label.config(text=time_str)
    
    def reset(self):
        """Сброс секундомера"""
        self.running = False
        self.start_time = None
        self.elapsed_time = 0
        self.lap_times = []  # Очищаем список кругов
        self.time_label.config(text="00:00:00.00")
        self.start_btn.config(state="normal", bg="#4CAF50")
        self.stop_btn.config(state="disabled", bg="#E57373")
        self.lap_btn.config(state="disabled", bg="#FFB74D")
        self.lap_indicator.config(text="Круги: 0")
        
        # Обновляем отображение кругов
        self.app.update_all_laps_display()
        
        # Обновляем увеличенный вид, если этот секундомер отображается
        if self.app.current_large_view == self:
            self.app.show_large_view(self)
    
    def record_lap(self):
        """Запись времени круга"""
        if self.running and self.start_time:
            current_elapsed = self.elapsed_time + (datetime.now() - self.start_time).total_seconds()
            self.lap_times.append(current_elapsed)
            self.lap_indicator.config(text=f"Круги: {len(self.lap_times)}")
            
            print(f"{self.name_var.get()} - Круг {len(self.lap_times)}: {self.format_time(current_elapsed)}")
            
            # Обновляем отображение кругов
            self.app.update_all_laps_display()
            
            # Обновляем увеличенный вид, если этот секундомер отображается
            if self.app.current_large_view == self:
                self.app.show_large_view(self)
    
    def format_time(self, seconds):
        """Форматирование времени для вывода"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds - int(seconds)) * 100)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def update_name(self):
        """Обновление названия секундомера"""
        self.name_var.set(f"Секундомер {self.number}")
        self.app.update_all_laps_display()
    
    def remove(self):
        """Удаление этого секундомера"""
        if self.app:
            self.app.remove_stopwatch(self)
    
    def select_for_large_view(self):
        """Выбор этого секундомера для отображения в увеличенном виде"""
        self.app.show_large_view(self)
    
    def destroy(self):
        """Уничтожение виджета"""
        self.frame.destroy()

def main():
    root = tk.Tk()
    app = CompactStopwatchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

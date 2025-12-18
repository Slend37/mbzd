import tkinter as tk
from datetime import datetime
from collections import defaultdict
from stopwatch import Stopwatch

class StopwatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Компактные секундомеры с сортировкой кругов")
        self.root.geometry("1100x700")
        
        # Список для хранения всех секундомеров
        self.stopwatches = []
        self.current_large_view = None  # Текущий отображаемый крупно секундомер
        
        # Создаем основной интерфейс
        self.create_widgets()
        
    def create_widgets(self):
        """Создание интерфейса приложения"""
        # Основной контейнер с разделением на левую и правую части
        main_container = tk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ЛЕВАЯ ПАНЕЛЬ - список секундомеров (занимает всю левую сторону)
        left_panel = tk.Frame(main_container, width=650)
        left_panel.pack(side="left", fill="both", expand=True)
        
        self.create_left_panel(left_panel)
        
        # ПРАВАЯ ПАНЕЛЬ - разделена на верхнюю (увеличенный вид) и нижнюю (круги)
        right_panel = tk.Frame(main_container, width=400)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.create_top_right_panel(right_panel)
        self.create_bottom_right_panel(right_panel)
        
        # Изначально создаем 3 секундомера
        for i in range(3):
            self.add_stopwatch()
        
    def create_left_panel(self, parent):
        """Создание левой панели со списком секундомеров"""
        # Заголовок левой панели
        left_title = tk.Label(
            parent, 
            text="Список секундомеров",
            font=("Arial", 12, "bold")
        )
        left_title.pack(pady=5)
        
        # Кнопка для добавления нового секундомера
        add_button = tk.Button(
            parent,
            text="+ Добавить секундомер",
            command=self.add_stopwatch,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white",
            height=1,
            width=20
        )
        add_button.pack(pady=5)
        
        # Заголовки колонок
        headers_frame = tk.Frame(parent)
        headers_frame.pack(fill="x", pady=5)
        
        # Колонки
        tk.Label(headers_frame, text="Название", font=("Arial", 10, "bold"), width=22).grid(row=0, column=0, padx=5)
        tk.Label(headers_frame, text="Время", font=("Arial", 10, "bold"), width=15).grid(row=0, column=1, padx=5)
        tk.Label(headers_frame, text="Управление", font=("Arial", 10, "bold"), width=50).grid(row=0, column=2, padx=5)
        
        # Фрейм для секундомеров с прокруткой
        self.canvas = tk.Canvas(parent)
        self.scrollbar = tk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
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
            parent,
            text="Сбросить все",
            command=self.reset_all,
            font=("Arial", 10),
            bg="#f44336",
            fg="white",
            height=1,
            width=20
        )
        reset_all_button.pack(pady=10)
    
    def create_top_right_panel(self, parent):
        """Создание верхней правой панели (увеличенный вид)"""
        top_right_panel = tk.Frame(parent, height=320, relief="ridge", borderwidth=2, bg="#f0f0f0")
        top_right_panel.pack(side="top", fill="both", expand=True, pady=(0, 10))
        top_right_panel.pack_propagate(False)  # Фиксируем высоту
        
        # Заголовок верхней правой панели
        top_right_title = tk.Label(
            top_right_panel, 
            text="Увеличенный вид",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        )
        top_right_title.pack(pady=15)
        
        # Контейнер для увеличенного отображения
        self.large_view_container = tk.Frame(top_right_panel, bg="#f0f0f0")
        self.large_view_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Изначальное сообщение
        self.large_view_label = tk.Label(
            self.large_view_container,
            text="Выберите секундомер\nдля увеличенного отображения",
            font=("Arial", 12),
            bg="#f0f0f0",
            fg="#666",
            justify="center"
        )
        self.large_view_label.pack(expand=True)
    
    def create_bottom_right_panel(self, parent):
        """Создание нижней правой панели (круги всех секундомеров)"""
        bottom_right_panel = tk.Frame(parent, relief="ridge", borderwidth=2, bg="#e8f5e8")
        bottom_right_panel.pack(side="bottom", fill="both", expand=True)
        
        # Заголовок нижней правой панели
        bottom_right_title = tk.Label(
            bottom_right_panel, 
            text="Круги (сортировка: номер → время)",
            font=("Arial", 12, "bold"),
            bg="#e8f5e8"
        )
        bottom_right_title.pack(pady=10)
        
        # Статистика кругов
        self.laps_stats_frame = tk.Frame(bottom_right_panel, bg="#e8f5e8")
        self.laps_stats_frame.pack(fill="x", pady=(0, 5), padx=10)
        
        self.total_laps_label = tk.Label(
            self.laps_stats_frame,
            text="Кругов: 0",
            font=("Arial", 10),
            bg="#e8f5e8",
            fg="#2E7D32"
        )
        self.total_laps_label.pack(side="left", padx=5)
        
        self.active_stopwatches_label = tk.Label(
            self.laps_stats_frame,
            text="Активных: 0",
            font=("Arial", 10),
            bg="#e8f5e8",
            fg="#2E7D32"
        )
        self.active_stopwatches_label.pack(side="left", padx=5)
        
        # Контейнер для отображения кругов с прокруткой
        self.laps_canvas = tk.Canvas(bottom_right_panel, bg="#e8f5e8")
        self.laps_scrollbar = tk.Scrollbar(bottom_right_panel, orient="vertical", command=self.laps_canvas.yview)
        self.laps_frame = tk.Frame(self.laps_canvas, bg="#e8f5e8")
        
        self.laps_frame.bind(
            "<Configure>",
            lambda e: self.laps_canvas.configure(scrollregion=self.laps_canvas.bbox("all"))
        )
        
        self.laps_canvas.create_window((0, 0), window=self.laps_frame, anchor="nw")
        self.laps_canvas.configure(yscrollcommand=self.laps_scrollbar.set, bg="#e8f5e8")
        
        self.laps_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.laps_scrollbar.pack(side="right", fill="y")
        
    def add_stopwatch(self):
        """Добавляет новый секундомер"""
        stopwatch = Stopwatch(self.stopwatches_frame, len(self.stopwatches) + 1, self)
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
            text=stopwatch.get_name(),
            font=("Arial", 14, "bold"),
            bg="#f0f0f0",
            fg=stopwatch.get_color()  # Используем цвет секундомера
        )
        selected_name_label.pack(pady=(10, 5))
        
        # Отображаем время крупным шрифтом
        large_time_label = tk.Label(
            self.large_view_container,
            text=stopwatch.time_label.cget("text"),
            font=("Courier New", 32, "bold"),
            bg="#f0f0f0",
            fg=stopwatch.get_color()  # Используем цвет секундомера
        )
        large_time_label.pack(pady=15)
        
        # Создаем кнопки управления
        large_buttons_frame = tk.Frame(self.large_view_container, bg="#f0f0f0")
        
        # Кнопка Старт для увеличенного вида
        large_start_btn = tk.Button(
            large_buttons_frame,
            text="СТАРТ",
            command=stopwatch.start,
            width=9,
            height=1,
            bg="#4CAF50" if not stopwatch.running else "#81C784",
            fg="white",
            font=("Arial", 10, "bold"),
            state="normal" if not stopwatch.running else "disabled"
        )
        large_start_btn.pack(side="left", padx=3, pady=5)
        
        # Кнопка Стоп для увеличенного вида
        large_stop_btn = tk.Button(
            large_buttons_frame,
            text="СТОП",
            command=stopwatch.stop,
            width=9,
            height=1,
            bg="#f44336" if stopwatch.running else "#E57373",
            fg="white",
            font=("Arial", 10, "bold"),
            state="normal" if stopwatch.running else "disabled"
        )
        large_stop_btn.pack(side="left", padx=3, pady=5)
        
        # Кнопка Круг для увеличенного вида
        large_lap_btn = tk.Button(
            large_buttons_frame,
            text="КРУГ",
            command=stopwatch.record_lap,
            width=9,
            height=1,
            bg="#FF9800",
            fg="white",
            font=("Arial", 10, "bold"),
            state="normal" if stopwatch.running else "disabled"
        )
        large_lap_btn.pack(side="left", padx=3, pady=5)
        
        large_buttons_frame.pack(pady=5)
        
        # Информация о кругах этого секундомера
        laps_info_label = tk.Label(
            self.large_view_container,
            text=f"Зафиксировано кругов: {len(stopwatch.lap_times)}",
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="#666"
        )
        laps_info_label.pack(pady=10)
        
        # Кнопка скрытия увеличенного вида
        hide_button = tk.Button(
            self.large_view_container,
            text="Скрыть увеличенный вид",
            command=self.clear_large_view,
            font=("Arial", 9),
            bg="#9E9E9E",
            fg="white"
        )
        hide_button.pack(pady=10)
        
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
            font=("Arial", 12),
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
        """Обновляет отображение всех кругов в правой нижней панели, сгруппированных по номеру круга и отсортированных по времени"""
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
                    font=("Arial", 10, "bold"),
                    bg="#e8f5e8",
                    fg="#2E7D32",
                    anchor="w"
                )
                group_header.pack(fill="x", pady=(8, 3), padx=5)
                
                # Отображаем все круги с этим номером, отсортированные по времени
                for lap_info in laps_by_number[lap_number]:
                    # Форматируем время
                    time_str = self.format_lap_time(lap_info['lap_time'])
                    
                    # Создаем метку для круга с цветом секундомера
                    lap_text = f"  {lap_info['stopwatch_name']}: {time_str}"
                    lap_label = tk.Label(
                        self.laps_frame,
                        text=lap_text,
                        font=("Courier New", 9),
                        bg="#e8f5e8",
                        fg=lap_info['stopwatch_color'],
                        anchor="w"
                    )
                    lap_label.pack(fill="x", pady=1, padx=12)
        
        # Если нет кругов ни у одного секундомера
        if not laps_by_number:
            no_laps_label = tk.Label(
                self.laps_frame,
                text="Круги еще не зафиксированы\nнажмите кнопку 'Круг'\nво время работы секундомера",
                font=("Arial", 10),
                bg="#e8f5e8",
                fg="#666",
                justify="center"
            )
            no_laps_label.pack(expand=True, pady=20)
    
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
        
    def add_stopwatch(self):
        """Добавляет новый секундомер"""
        stopwatch = Stopwatch(self.stopwatches_frame, len(self.stopwatches) + 1, self)
        self.stopwatches.append(stopwatch)
        
        # Не вызываем renumber_stopwatches() здесь, чтобы не сбрасывать имена
        # Вместо этого просто обновляем отображение кругов
        self.update_all_laps_display()
    
    def renumber_stopwatches(self):
        """Перенумеровывает все секундомеры, сохраняя пользовательские имена"""
        for i, stopwatch in enumerate(self.stopwatches, 1):
            # Обновляем только номер, не трогаем пользовательское имя
            stopwatch.number = i
            # Не вызываем stopwatch.update_name() чтобы не сбрасывать имена
    
    def remove_stopwatch(self, stopwatch):
        """Удаляет секундомер"""
        if len(self.stopwatches) > 1:  # Оставляем хотя бы один секундомер
            # Если удаляем тот, что отображается крупно
            if self.current_large_view == stopwatch:
                self.clear_large_view()
            
            stopwatch.destroy()
            self.stopwatches.remove(stopwatch)
            # Перенумеровываем, но не сбрасываем имена
            for i, sw in enumerate(self.stopwatches, 1):
                sw.number = i
            self.update_all_laps_display()
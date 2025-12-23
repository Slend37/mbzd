import tkinter as tk
from datetime import datetime
from collections import defaultdict
from stopwatch import Stopwatch

class StopwatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система отсчета для лыжных гонок")
        self.root.geometry("1200x750")  # Увеличил размер окна
        
        # Список для хранения всех секундомеров (лыжников)
        self.stopwatches = []
        self.frozen_lap_data = None
        self.current_large_view = None  # Текущий отображаемый крупно лыжник
        
        # Для хранения информации об обратном отсчете
        self.countdown_target_time = 0  # Целевое время для обратного отсчета
        self.countdown_best_stopwatch_name = ""  # Имя лыжника с лучшим временем
        self.countdown_best_stopwatch_color = ""  # Цвет лыжника с лучшим временем
        self.show_post_lap_result = False  # Флаг показа результата после круга
        self.post_lap_start_time = None  # Время начала показа результата после круга
        self.post_lap_duration = 5  # Длительность показа результата после круга (сек)
        
        # Таймер для обновления таблицы
        self.table_update_interval = 1000  # Обновляем каждую секунду (1000 мс)
        
        # Создаем основной интерфейс
        self.create_widgets()
        
        # Изначально создаем 5 лыжников
        for i in range(5):
            self.add_stopwatch()
        
        # Запускаем таймер обновления таблицы
        self.start_table_update_timer()
        
    def start_table_update_timer(self):
        """Запускает таймер для периодического обновления таблицы соседей"""
        self.update_table_timer()
        
    def update_table_timer(self):
        """Периодическое обновление таблицы соседей"""
        if self.current_large_view:
            # Обновляем увеличенный вид (таблица будет обновлена внутри show_large_view)
            show_post_lap = False
            if self.current_large_view.just_completed_lap and self.current_large_view.lap_completion_time:
                elapsed = (datetime.now() - self.current_large_view.lap_completion_time).total_seconds()
                if elapsed < self.post_lap_duration:
                    show_post_lap = True
            
            # Получаем данные для обновления таблицы
            stopwatch = self.current_large_view
            current_lap = stopwatch.get_current_lap() + 1
            if show_post_lap:
                current_lap = len(stopwatch.lap_times)
            
            is_racing = stopwatch.running and (current_lap > len(stopwatch.lap_times))
            
            # Обновляем только таблицу соседей
            self.update_neighbors_table(stopwatch, current_lap, is_racing, show_post_lap)
        
        # Планируем следующее обновление
        self.root.after(self.table_update_interval, self.update_table_timer)
    
    def update_neighbors_table(self, stopwatch, current_lap, is_racing, show_post_lap=False):
        """Обновляет только таблицу соседей в увеличенном виде"""
        if not hasattr(self, 'table_frame') or not self.table_frame:
            return
            
        # Получаем обновленные данные для таблицы
        best_skier, display_skiers, position = self.get_display_neighbors(stopwatch, current_lap, is_racing)
        
        # Очищаем таблицу (кроме заголовков)
        for widget in self.table_frame.winfo_children():
            if widget.grid_info()['row'] > 0:  # Оставляем только заголовки (строка 0)
                widget.destroy()
        
        # Заполняем таблицу обновленными данными
        if display_skiers and len(display_skiers) > 0:
            # Есть данные для отображения
            for i in range(3):
                row = i + 1
                
                if i < len(display_skiers):
                    skier_info = display_skiers[i]
                    skier = skier_info['stopwatch']
                    lap_time = skier_info['lap_time']
                    position_num = skier_info['position']
                    is_current = (skier == stopwatch)
                    is_best = skier_info.get('is_best', False)
                    
                    # Получаем лучшее время на этом круге
                    best_time_for_lap, best_skier_for_lap, _ = self.get_best_time_for_current_lap(current_lap)
                    
                    # Место
                    place_label = tk.Label(
                        self.table_frame,
                        text=f"[{position_num}]",
                        font=("Arial", 11, "bold"),
                        bg="#f0f0f0",
                        fg=self.get_place_color(position_num)
                    )
                    place_label.grid(row=row, column=0, padx=8, pady=8, sticky="w")
                    
                    # Имя лыжника
                    name_text = skier.get_name()
                    if is_current:
                        name_text = f"→ {name_text}"
                        
                    name_label = tk.Label(
                        self.table_frame,
                        text=name_text,
                        font=("Arial", 11),
                        bg="#f0f0f0",
                        fg=skier.get_color()
                    )
                    name_label.grid(row=row, column=1, padx=8, pady=8, sticky="w")
                    
                    # Время или отставание
                    if is_best:
                        # Лучшее время круга
                        time_text = self.format_lap_time(lap_time)
                        time_color = "#2196F3"  # Синий для рекорда
                    elif is_racing and is_current:
                        # Текущий лыжник еще бежит - показываем его текущее время
                        if stopwatch.running:
                            current_time = (stopwatch.elapsed_time + 
                                        (datetime.now() - stopwatch.start_time).total_seconds())
                            if best_time_for_lap is not None:
                                time_diff = current_time - best_time_for_lap
                                if time_diff < 0:
                                    time_text = f"-{self.format_lap_time(abs(time_diff))}"
                                    time_color = "#4CAF50"
                                else:
                                    time_text = f"+{self.format_lap_time(time_diff)}"
                                    time_color = self.get_difference_color(time_diff)
                            else:
                                time_text = self.format_lap_time(current_time)
                                time_color = skier.get_color()
                        else:
                            time_text = self.format_lap_time(lap_time)
                            time_color = skier.get_color()
                    elif best_time_for_lap is not None:
                        # Отставание от лучшего времени
                        time_diff = lap_time - best_time_for_lap
                        if time_diff == 0:
                            time_text = self.format_lap_time(lap_time)
                            time_color = "#2196F3"  # Синий, если время совпадает с лучшим
                        else:
                            time_text = f"+{self.format_lap_time(time_diff)}"
                            time_color = self.get_difference_color(time_diff)
                    else:
                        time_text = self.format_lap_time(lap_time)
                        time_color = skier.get_color()
                    
                    time_label = tk.Label(
                        self.table_frame,
                        text=time_text,
                        font=("Courier New", 11),
                        bg="#f0f0f0",
                        fg=time_color
                    )
                    time_label.grid(row=row, column=2, padx=8, pady=8, sticky="w")
                else:
                    # Нет данных для этой строки
                    no_data_label = tk.Label(
                        self.table_frame,
                        text="---",
                        font=("Arial", 11),
                        bg="#f0f0f0",
                        fg="#666"
                    )
                    no_data_label.grid(row=row, column=0, columnspan=3, padx=8, pady=8, sticky="w")
        else:
            # Нет данных вообще - показываем сообщение
            for i in range(3):
                row = i + 1
                no_data_label = tk.Label(
                    self.table_frame,
                    text="Нет данных",
                    font=("Arial", 11),
                    bg="#f0f0f0",
                    fg="#666"
                )
                no_data_label.grid(row=row, column=0, columnspan=3, padx=8, pady=8, sticky="w")
        
    def create_widgets(self):
        """Создание интерфейса приложения"""
        # Основной контейнер с разделением на левую и правую части
        main_container = tk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ЛЕВАЯ ПАНЕЛЬ - список лыжников (уменьшаем ширину)
        left_panel = tk.Frame(main_container, width=800)  # Уменьшил ширину
        left_panel.pack(side="left", fill="both")
        left_panel.pack_propagate(False)  # Фиксируем ширину
        
        self.create_left_panel(left_panel)
        
        # ПРАВАЯ ПАНЕЛЬ - разделена на верхнюю (увеличенный вид) и нижнюю (круги)
        right_panel = tk.Frame(main_container, width=450)  # Увеличил ширину
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.create_top_right_panel(right_panel)
        self.create_bottom_right_panel(right_panel)
    
    def create_left_panel(self, parent):
        """Создание левой панели со списком лыжников"""
        # Заголовок левой панели
        left_title = tk.Label(
            parent, 
            text="Список лыжников",
            font=("Arial", 14, "bold")
        )
        left_title.pack(pady=5)
        
        # Кнопка для добавления нового лыжника
        add_button = tk.Button(
            parent,
            text="+ Добавить лыжника",
            command=self.add_stopwatch,
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white",
            height=1,
            width=20
        )
        add_button.pack(pady=5)
        
        # Заголовки колонок (уменьшаем ширины)
        headers_frame = tk.Frame(parent)
        headers_frame.pack(fill="x", pady=5)
        
        # Колонки с уменьшенными ширинами
        tk.Label(headers_frame, text="Номер и имя", font=("Arial", 11, "bold"), width=15).grid(row=0, column=0, padx=5)
        tk.Label(headers_frame, text="Время", font=("Arial", 11, "bold"), width=12).grid(row=0, column=1, padx=5)
        tk.Label(headers_frame, text="Управление", font=("Arial", 11, "bold"), width=25).grid(row=0, column=2, padx=5)
        
        # Фрейм для лыжников с прокруткой
        self.canvas = tk.Canvas(parent)
        self.scrollbar = tk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.stopwatches_frame = tk.Frame(self.canvas)
        
        self.stopwatches_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.stopwatches_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=(3, 0))
        self.scrollbar.pack(side="right", fill="y")
    
    def create_top_right_panel(self, parent):
        """Создание верхней правой панели (увеличенный вид)"""
        # Хромакейный зеленый цвет
        chroma_key_green = "#00FF00"
        
        # Увеличиваем высоту и делаем шире
        top_right_panel = tk.Frame(parent, height=450, relief="ridge", borderwidth=2, bg=chroma_key_green)
        top_right_panel.pack(side="top", fill="both", expand=True, pady=(0, 10))
        top_right_panel.pack_propagate(False)  # Фиксируем высоту
        
        # Заголовок верхней правой панели
        top_right_title = tk.Label(
            top_right_panel, 
            text="Увеличенный вид",
            font=("Arial", 18, "bold"),  # Увеличил шрифт
            bg=chroma_key_green,
            fg="white"
        )
        top_right_title.pack(pady=20)  # Увеличил отступ
        
        # Контейнер для увеличенного отображения (увеличиваем отступы)
        self.large_view_container = tk.Frame(top_right_panel, bg=chroma_key_green)
        self.large_view_container.pack(fill="both", expand=True, padx=40, pady=20)  # Увеличил отступы
    
    def create_bottom_right_panel(self, parent):
        """Создание нижней правой панели (круги всех лыжников)"""
        bottom_right_panel = tk.Frame(parent, relief="ridge", borderwidth=2, bg="#e8f5e8")
        bottom_right_panel.pack(side="bottom", fill="both", expand=True)
        
        # Заголовок нижней правой панели
        bottom_right_title = tk.Label(
            bottom_right_panel, 
            text="Круги (горизонтальный вид: лыжники ↓, круги →)",
            font=("Arial", 14, "bold"),
            bg="#e8f5e8"
        )
        bottom_right_title.pack(pady=10)
        
        # Статистика кругов
        self.laps_stats_frame = tk.Frame(bottom_right_panel, bg="#e8f5e8")
        self.laps_stats_frame.pack(fill="x", pady=(0, 5), padx=10)
        
        self.total_laps_label = tk.Label(
            self.laps_stats_frame,
            text="Кругов: 0",
            font=("Arial", 11),
            bg="#e8f5e8",
            fg="#2E7D32"
        )
        self.total_laps_label.pack(side="left", padx=5)
        
        self.active_stopwatches_label = tk.Label(
            self.laps_stats_frame,
            text="Активных: 0",
            font=("Arial", 11),
            bg="#e8f5e8",
            fg="#2E7D32"
        )
        self.active_stopwatches_label.pack(side="left", padx=5)
        
        # Контейнер для отображения кругов с ГОРИЗОНТАЛЬНОЙ прокруткой
        self.laps_canvas = tk.Canvas(bottom_right_panel, bg="#e8f5e8")
        self.laps_scrollbar = tk.Scrollbar(bottom_right_panel, orient="horizontal", command=self.laps_canvas.xview)
        self.laps_frame = tk.Frame(self.laps_canvas, bg="#e8f5e8")
        
        self.laps_frame.bind(
            "<Configure>",
            lambda e: self.laps_canvas.configure(scrollregion=self.laps_canvas.bbox("all"))
        )
        
        self.laps_canvas.create_window((0, 0), window=self.laps_frame, anchor="nw")
        self.laps_canvas.configure(xscrollcommand=self.laps_scrollbar.set, bg="#e8f5e8")
        
        self.laps_canvas.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 5))
        self.laps_scrollbar.pack(side="bottom", fill="x")
        
    def get_best_time_for_current_lap(self, lap_number):
        """Возвращает лучшее время на указанном круге"""
        best_time = None
        best_stopwatch = None
        best_stopwatch_color = ""
        
        for stopwatch in self.stopwatches:
            if lap_number <= len(stopwatch.lap_times):
                lap_time = stopwatch.lap_times[lap_number - 1]
                if best_time is None or lap_time < best_time:
                    best_time = lap_time
                    best_stopwatch = stopwatch
                    best_stopwatch_color = stopwatch.get_color()
        
        return best_time, best_stopwatch, best_stopwatch_color
    
    def get_skier_position_on_lap(self, selected_skier, lap_number):
        """Возвращает позицию лыжника на указанном круге"""
        if lap_number > len(selected_skier.lap_times):
            return None, None, None
        
        # Собираем всех лыжников, которые прошли этот круг
        skiers_on_lap = []
        
        for stopwatch in self.stopwatches:
            if lap_number <= len(stopwatch.lap_times):
                skiers_on_lap.append({
                    'stopwatch': stopwatch,
                    'lap_time': stopwatch.lap_times[lap_number - 1],
                    'position': None  # Будет вычислено
                })
        
        # Сортируем по времени круга
        skiers_on_lap.sort(key=lambda x: x['lap_time'])
        
        # Находим позицию выбранного лыжника
        selected_position = None
        for i, skier in enumerate(skiers_on_lap, 1):
            skier['position'] = i
            if skier['stopwatch'] == selected_skier:
                selected_position = i
        
        # Получаем соседей
        neighbors = []
        if selected_position is not None:
            # Лыжник перед выбранным
            if selected_position > 1:
                neighbors.append(skiers_on_lap[selected_position - 2])
            
            # Лыжник после выбранного
            if selected_position < len(skiers_on_lap):
                neighbors.append(skiers_on_lap[selected_position])
        
        return selected_position, skiers_on_lap, neighbors
    
    def get_display_neighbors(self, selected_skier, current_lap, is_racing=True):
        """Возвращает лыжников для отображения в таблице с виртуальными позициями"""
        # Получаем лучший результат на текущем круге
        best_time, best_skier, best_color = self.get_best_time_for_current_lap(current_lap)
        
        # Получаем всех лыжников, которые уже завершили этот круг
        completed_skiers = []
        for stopwatch in self.stopwatches:
            if current_lap <= len(stopwatch.lap_times):
                completed_skiers.append({
                    'stopwatch': stopwatch,
                    'lap_time': stopwatch.lap_times[current_lap - 1],
                    'position': None
                })
        
        # Сортируем по времени круга
        completed_skiers.sort(key=lambda x: x['lap_time'])
        
        # Назначаем позиции
        for i, skier in enumerate(completed_skiers, 1):
            skier['position'] = i
        
        # Если есть лыжники, завершившие круг, или есть лыжник, который еще бежит
        if completed_skiers or (selected_skier.running and is_racing):
            display_skiers = []
            added_stopwatches = set()
            
            # Вычисляем текущее время лыжника, если он еще бежит
            current_skier_time = None
            if selected_skier.running and current_lap > len(selected_skier.lap_times):
                current_skier_time = (selected_skier.elapsed_time + 
                                    (datetime.now() - selected_skier.start_time).total_seconds())
            
            # Если лыжник еще бежит (не завершил текущий круг)
            if is_racing:
                # Собираем всех "виртуальных" участников на этом круге
                virtual_skiers = completed_skiers.copy()
                
                # Добавляем текущего лыжника с его текущим временем
                if current_skier_time is not None:
                    virtual_skiers.append({
                        'stopwatch': selected_skier,
                        'lap_time': current_skier_time,
                        'position': None,
                        'is_current': True,
                        'is_virtual': True
                    })
                
                # Сортируем виртуальных участников по времени
                virtual_skiers.sort(key=lambda x: x['lap_time'])
                
                # Назначаем виртуальные позиции
                for i, skier in enumerate(virtual_skiers, 1):
                    skier['virtual_position'] = i
                
                # Находим виртуальную позицию текущего лыжника
                current_virtual_position = None
                for skier in virtual_skiers:
                    if skier.get('is_current'):
                        current_virtual_position = skier['virtual_position']
                        break
                
                if current_virtual_position:
                    # Собираем отображаемых лыжников вокруг текущей позиции
                    positions_to_show = []
                    
                    # Всегда показываем лучшего (если есть)
                    if best_skier:
                        positions_to_show.append(1)
                    
                    # Показываем лыжников вокруг текущей позиции
                    positions_to_show.append(current_virtual_position - 1)  # Перед текущим
                    positions_to_show.append(current_virtual_position)      # Текущий
                    positions_to_show.append(current_virtual_position + 1)  # После текущего
                    
                    # Убираем некорректные позиции (меньше 1 или больше максимума)
                    positions_to_show = [pos for pos in positions_to_show 
                                    if 1 <= pos <= len(virtual_skiers)]
                    
                    # Оставляем уникальные позиции
                    positions_to_show = list(set(positions_to_show))
                    positions_to_show.sort()
                    
                    # Берем до 3 позиций
                    positions_to_show = positions_to_show[:3]
                    
                    # Собираем лыжников для отображения
                    for pos in positions_to_show:
                        skier_info = virtual_skiers[pos - 1]
                        is_current = skier_info.get('is_current', False)
                        is_best = (skier_info['stopwatch'] == best_skier)
                        
                        display_skiers.append({
                            'stopwatch': skier_info['stopwatch'],
                            'lap_time': skier_info['lap_time'],
                            'position': skier_info.get('position', skier_info['virtual_position']),
                            'is_current': is_current,
                            'is_best': is_best,
                            'is_virtual': skier_info.get('is_virtual', False)
                        })
                    
                    return best_skier, display_skiers, current_virtual_position
            
            # Если лыжник уже завершил этот круг
            else:
                # Находим фактическую позицию текущего лыжника
                current_actual_position = None
                for skier in completed_skiers:
                    if skier['stopwatch'] == selected_skier:
                        current_actual_position = skier['position']
                        break
                
                if current_actual_position:
                    # Определяем, какие позиции показывать
                    positions_to_show = []
                    
                    # Всегда показываем лучшего (если есть и не текущий)
                    if best_skier and best_skier != selected_skier:
                        positions_to_show.append(1)
                    
                    # Показываем текущего лыжника
                    positions_to_show.append(current_actual_position)
                    
                    # Показываем лыжников вокруг текущего
                    positions_to_show.append(current_actual_position - 1)  # Перед текущим
                    positions_to_show.append(current_actual_position + 1)  # После текущего
                    
                    # Убираем некорректные позиции
                    positions_to_show = [pos for pos in positions_to_show 
                                    if 1 <= pos <= len(completed_skiers)]
                    
                    # Оставляем уникальные позиции
                    positions_to_show = list(set(positions_to_show))
                    positions_to_show.sort()
                    
                    # Берем до 3 позиций
                    positions_to_show = positions_to_show[:3]
                    
                    # Собираем лыжников для отображения
                    for pos in positions_to_show:
                        skier_info = completed_skiers[pos - 1]
                        is_current = (skier_info['stopwatch'] == selected_skier)
                        is_best = (skier_info['stopwatch'] == best_skier)
                        
                        display_skiers.append({
                            'stopwatch': skier_info['stopwatch'],
                            'lap_time': skier_info['lap_time'],
                            'position': skier_info['position'],
                            'is_current': is_current,
                            'is_best': is_best
                        })
                    
                    return best_skier, display_skiers, current_actual_position
        
        # Если нет данных для отображения
        return None, [], None
    
    def add_stopwatch(self):
        """Добавляет нового лыжника"""
        # Добавляем нового лыжника с номером, который на 1 больше текущего количества
        stopwatch = Stopwatch(self.stopwatches_frame, len(self.stopwatches) + 1, self)
        self.stopwatches.append(stopwatch)
        
        # Обновляем отображение кругов
        self.update_all_laps_display()
        
    def remove_stopwatch(self, stopwatch):
        """Удаляет лыжника"""
        if len(self.stopwatches) > 1:  # Оставляем хотя бы одного лыжника
            # Если удаляем того, что отображается крупно
            if self.current_large_view == stopwatch:
                self.clear_large_view()
            
            stopwatch.destroy()
            self.stopwatches.remove(stopwatch)
            
            # Обновляем номера оставшихся лыжников, сохраняя их имена
            for i, sw in enumerate(self.stopwatches, 1):
                sw.update_display_number(i)
            
            self.update_all_laps_display()
    
    def reset_all(self):
        """Сброс всех лыжников"""
        for stopwatch in self.stopwatches:
            stopwatch.reset()
        
        # Очищаем увеличенный вид
        self.clear_large_view()
        self.update_all_laps_display()
    
    def show_large_view(self, stopwatch):
        """Показывает увеличенный вид выбранного лыжника"""
        self.current_large_view = stopwatch
        
        # Хромакейный зеленый цвет
        chroma_key_green = "#00FF00"
        
        # Очищаем контейнер
        for widget in self.large_view_container.winfo_children():
            widget.destroy()
        
        # Основной контейнер для увеличенного вида
        main_large_frame = tk.Frame(self.large_view_container, bg=chroma_key_green)
        main_large_frame.pack(fill="both", expand=True)
        
        # Получаем текущий круг
        current_lap = stopwatch.get_current_lap() + 1
        is_racing = stopwatch.running and (current_lap > len(stopwatch.lap_times))
        
        # Проверяем, нужно ли показывать результат после круга
        show_post_lap = False
        if stopwatch.just_completed_lap and stopwatch.lap_completion_time:
            elapsed = (datetime.now() - stopwatch.lap_completion_time).total_seconds()
            if elapsed < self.post_lap_duration:
                show_post_lap = True
                # Замораживаем на только что завершенном круге
                current_lap = len(stopwatch.lap_times)  # Только что завершенный круг
                is_racing = False
                # Сохраняем данные этого круга для заморозки
                self.frozen_lap_data = {
                    'lap_number': current_lap,
                    'display_skiers': None,
                    'best_skier': None,
                    'position': None
                }
        
        # Получаем данные для отображения
        best_skier, display_skiers, position = self.get_display_neighbors(stopwatch, current_lap, is_racing)
        
        # Сохраняем замороженные данные если показываем результат
        if show_post_lap and hasattr(self, 'frozen_lap_data'):
            self.frozen_lap_data['display_skiers'] = display_skiers
            self.frozen_lap_data['best_skier'] = best_skier
            self.frozen_lap_data['position'] = position
        
        # Сохраняем ссылки на виджеты для обновления
        self.large_view_widgets = {
            'main_time_label': None,
            'timer_label': None,
            'table_labels': [],  # Будет хранить список виджетов таблицы
            'table_frame': None
        }
        
        # Основная строка: идентификатор, имя, время и таблица в одной строке
        main_row_frame = tk.Frame(main_large_frame, bg=chroma_key_green)
        main_row_frame.pack(fill="both", expand=True, pady=(0, 30))
        
        # Левый блок: идентификатор, имя и время в ОДНОЙ строке
        left_info_frame = tk.Frame(main_row_frame, bg=chroma_key_green)
        left_info_frame.pack(side="left", fill="y")
        
        # Контейнер для всей информации в одной строке
        info_container = tk.Frame(left_info_frame, bg=chroma_key_green)
        info_container.pack()
        
        # Идентификатор лыжника
        id_label = tk.Label(
            info_container,
            text=f"[{stopwatch.number}]",
            font=("Arial", 16, "bold"),
            bg=chroma_key_green,
            fg="white"  # Белый текст
        )
        id_label.pack(side="left", padx=(0, 10))
        
        # Имя лыжника
        name_label = tk.Label(
            info_container,
            text=stopwatch.get_name(),
            font=("Arial", 16, "bold"),
            bg=chroma_key_green,
            fg=stopwatch.get_color()
        )
        name_label.pack(side="left", padx=(0, 20))
        
        # Формируем текст для времени
        time_text = ""
        time_color = stopwatch.get_color()
        
        # Получаем лучшее время на текущем круге
        best_time_for_lap, best_skier_for_lap, _ = self.get_best_time_for_current_lap(current_lap)
        
        if best_skier_for_lap and best_time_for_lap is not None:
            if stopwatch.running and current_lap > len(stopwatch.lap_times):
                # Лыжник еще бежит текущий круг
                current_time = (stopwatch.elapsed_time + 
                               (datetime.now() - stopwatch.start_time).total_seconds())
                time_diff = current_time - best_time_for_lap
                
                if time_diff < 0:
                    time_text = f"-{self.format_lap_time(abs(time_diff))}"
                    time_color = "#4CAF50"  # Зеленый - опережение
                else:
                    time_text = f"+{self.format_lap_time(time_diff)}"
                    time_color = self.get_countdown_color(time_diff)
            elif not is_racing and current_lap <= len(stopwatch.lap_times):
                # Лыжник завершил круг
                skier_time = stopwatch.lap_times[current_lap - 1]
                time_diff = skier_time - best_time_for_lap
                
                if show_post_lap:
                    # Во время показа результата
                    if best_skier_for_lap == stopwatch:
                        # Если это лидер - показываем преимущество над 2-м местом
                        # Находим время второго места
                        second_place_time = None
                        # Получаем всех лыжников на этом круге
                        completed_skiers = []
                        for sw in self.stopwatches:
                            if current_lap <= len(sw.lap_times):
                                completed_skiers.append({
                                    'stopwatch': sw,
                                    'lap_time': sw.lap_times[current_lap - 1]
                                })
                        
                        # Сортируем по времени
                        completed_skiers.sort(key=lambda x: x['lap_time'])
                        
                        # Находим время второго места (если есть)
                        if len(completed_skiers) >= 2:
                            second_place_time = completed_skiers[1]['lap_time']
                            advantage = second_place_time - skier_time
                            time_text = f"-{self.format_lap_time(advantage)}"
                            time_color = "#4CAF50"  # Зеленый - преимущество
                        else:
                            # Нет второго места - показываем абсолютное время
                            time_text = self.format_lap_time(skier_time)
                            time_color = "#2196F3"  # Синий - рекорд
                    else:
                        # Если не лидер - показываем отставание от лидера
                        if time_diff < 0:
                            time_text = f"-{self.format_lap_time(abs(time_diff))}"
                            time_color = "#4CAF50"
                        else:
                            time_text = f"+{self.format_lap_time(time_diff)}"
                            time_color = self.get_difference_color(time_diff)
                else:
                    if time_diff < 0:
                        time_text = f"-{self.format_lap_time(abs(time_diff))}"
                        time_color = "#4CAF50"
                    elif time_diff == 0:
                        time_text = self.format_lap_time(skier_time)
                        time_color = "#2196F3"  # Синий - рекорд
                    else:
                        time_text = f"+{self.format_lap_time(time_diff)}"
                        time_color = self.get_difference_color(time_diff)
            else:
                time_text = stopwatch.time_label.cget("text")
        else:
            # Если нет лучшего времени на круге, показываем текущее время лыжника
            if stopwatch.running:
                current_time = (stopwatch.elapsed_time + 
                               (datetime.now() - stopwatch.start_time).total_seconds())
                time_text = stopwatch.format_time(current_time)
            else:
                time_text = stopwatch.time_label.cget("text")
        
        # Метка времени (в одной строке с идентификатором и именем)
        self.large_view_widgets['main_time_label'] = tk.Label(
            info_container,
            text=time_text,
            font=("Courier New", 20, "bold"),  # Уменьшил шрифт, чтобы влезало в строку
            bg=chroma_key_green,
            fg=time_color
        )
        self.large_view_widgets['main_time_label'].pack(side="left", padx=(0, 10))
        
        # Если показываем результат после круга, добавляем таймер
        if show_post_lap:
            elapsed = (datetime.now() - stopwatch.lap_completion_time).total_seconds()
            remaining = max(0, self.post_lap_duration - elapsed)
            
            self.large_view_widgets['timer_label'] = tk.Label(
                info_container,
                text=f"({remaining:.1f}с)",
                font=("Arial", 10),
                bg=chroma_key_green,
                fg="white"  # Белый текст
            )
            self.large_view_widgets['timer_label'].pack(side="right")
        
        # Правый блок: таблица сравнения (справа в той же строке)
        right_table_frame = tk.Frame(main_row_frame, bg=chroma_key_green)
        right_table_frame.pack(side="right", fill="y", padx=(20, 0))
        
        # Создаем таблицу 3x3
        self.large_view_widgets['table_frame'] = tk.Frame(right_table_frame, bg=chroma_key_green)
        self.large_view_widgets['table_frame'].pack()
        
        # Заголовки столбцов
        headers = ["#", "Лыжник", "Время"]
        for col, header in enumerate(headers):
            if header == "#":
                header_label = tk.Label(
                self.large_view_widgets['table_frame'],
                text=header,
                font=("Arial", 12, "bold"),
                bg=chroma_key_green,
                fg="white",
                width=4  # Уменьшил ширину
            )
            else:
                header_label = tk.Label(
                    self.large_view_widgets['table_frame'],
                    text=header,
                    font=("Arial", 12, "bold"),
                    bg=chroma_key_green,
                    fg="white",
                    width=12  # Уменьшил ширину
                )
            header_label.grid(row=0, column=col, padx=6, pady=6, sticky="w")  # Уменьшил отступы
        
        # Заполняем таблицу данными
        self.update_table_data(stopwatch, current_lap, is_racing, show_post_lap, display_skiers)
        
        # Строка с кнопками управления (ниже основной строки)
        buttons_frame = tk.Frame(main_large_frame, bg=chroma_key_green)
        buttons_frame.pack(fill="x", pady=10)
        
        # Создаем кнопки управления
        large_buttons_frame = tk.Frame(buttons_frame, bg=chroma_key_green)
        large_buttons_frame.pack()
        
        # Кнопка Старт
        self.large_start_btn = tk.Button(
            large_buttons_frame,
            text="СТАРТ",
            command=stopwatch.start,
            width=12,
            height=1,
            bg="#4CAF50" if not stopwatch.running else "#81C784",
            fg="white",
            font=("Arial", 12, "bold"),
            state="normal" if not stopwatch.running else "disabled"
        )
        self.large_start_btn.pack(side="left", padx=5, pady=5)
        
        # Кнопка Стоп
        self.large_stop_btn = tk.Button(
            large_buttons_frame,
            text="СТОП",
            command=stopwatch.stop,
            width=12,
            height=1,
            bg="#f44336" if stopwatch.running else "#E57373",
            fg="white",
            font=("Arial", 12, "bold"),
            state="normal" if stopwatch.running else "disabled"
        )
        self.large_stop_btn.pack(side="left", padx=5, pady=5)
        
        # Кнопка Круг
        self.large_lap_btn = tk.Button(
            large_buttons_frame,
            text="КРУГ",
            command=stopwatch.record_lap,
            width=12,
            height=1,
            bg="#FF9800",
            fg="white",
            font=("Arial", 12, "bold"),
            state="normal" if stopwatch.running else "disabled"
        )
        self.large_lap_btn.pack(side="left", padx=5, pady=5)
        
        # Кнопка скрытия увеличенного вида
        hide_button = tk.Button(
            main_large_frame,
            text="Скрыть увеличенный вид",
            command=self.clear_large_view,
            font=("Arial", 10),
            bg="#333333",
            fg="white"
        )
        hide_button.pack(pady=10)
        
        # Запускаем обновление времени в увеличенном виде
        self.update_large_view(stopwatch, show_post_lap)
    
    def update_table_data(self, stopwatch, current_lap, is_racing, show_post_lap=False, display_skiers=None):
        """Обновляет данные в таблице соседей"""
        # Хромакейный зеленый цвет
        chroma_key_green = "#00FF00"
        
        # Если данные не переданы, получаем их
        if display_skiers is None:
            # Если показываем результат после круга, используем замороженные данные
            if show_post_lap and hasattr(self, 'frozen_lap_data'):
                display_skiers = self.frozen_lap_data['display_skiers']
                best_skier = self.frozen_lap_data['best_skier']
                position = self.frozen_lap_data['position']
            else:
                best_skier, display_skiers, position = self.get_display_neighbors(stopwatch, current_lap, is_racing)
        
        # Очищаем предыдущие виджеты таблицы (кроме заголовков)
        for widget in self.large_view_widgets.get('table_labels', []):
            if widget and widget.winfo_exists():
                widget.destroy()
        
        self.large_view_widgets['table_labels'] = []
        
        # Заполняем таблицу данными
        if display_skiers and len(display_skiers) > 0:
            # Есть данные для отображения
            for i in range(3):
                row = i + 1
                
                if i < len(display_skiers):
                    skier_info = display_skiers[i]
                    skier = skier_info['stopwatch']
                    lap_time = skier_info['lap_time']
                    position_num = skier_info['position']
                    is_current = skier_info.get('is_current', False)
                    is_best = skier_info.get('is_best', False)
                    is_virtual = skier_info.get('is_virtual', False)
                    
                    # Получаем лучшее время на этом круге
                    best_time_for_lap, best_skier_for_lap, _ = self.get_best_time_for_current_lap(current_lap)
                    
                    # Место
                    place_text = f"[{position_num}]"
                    if is_virtual:
                        place_text = f"~{position_num}~"
                    
                    place_label = tk.Label(
                        self.large_view_widgets['table_frame'],
                        text=place_text,
                        font=("Arial", 11, "bold"),
                        bg=chroma_key_green,
                        fg=self.get_place_color(position_num) if not is_virtual else "white"
                    )
                    place_label.grid(row=row, column=0, padx=8, pady=8, sticky="w")
                    self.large_view_widgets['table_labels'].append(place_label)
                    
                    # Имя лыжника
                    name_text = skier.get_name()
                    if is_current:
                        name_text = f"→ {name_text}"
                    
                    name_label = tk.Label(
                        self.large_view_widgets['table_frame'],
                        text=name_text,
                        font=("Arial", 11),
                        bg=chroma_key_green,
                        fg=skier.get_color()
                    )
                    name_label.grid(row=row, column=1, padx=8, pady=8, sticky="w")
                    self.large_view_widgets['table_labels'].append(name_label)
                    
                    # Время или отставание
                    if is_best:
                        # Лучшее время круга
                        if show_post_lap and is_current:
                            # Если показываем результат и это текущий лыжник стал лидером
                            # Находим время второго места для расчета преимущества
                            second_place_time = None
                            for skier_info2 in display_skiers:
                                if skier_info2['position'] == 2:
                                    second_place_time = skier_info2['lap_time']
                                    break
                            
                            if second_place_time is not None:
                                advantage = second_place_time - lap_time
                                time_text = f"+{self.format_lap_time(advantage)}"
                                time_color = "#4CAF50"  # Зеленый - преимущество
                            else:
                                time_text = self.format_lap_time(lap_time)
                                time_color = "#2196F3"  # Синий для рекорда
                        else:
                            # Обычное отображение лучшего времени
                            time_text = self.format_lap_time(lap_time)
                            time_color = "#2196F3"  # Синий для рекорда
                    elif is_virtual and is_current:
                        # Виртуальное время текущего лыжника
                        if stopwatch.running:
                            current_time = (stopwatch.elapsed_time + 
                                           (datetime.now() - stopwatch.start_time).total_seconds())
                            if best_time_for_lap is not None:
                                time_diff = current_time - best_time_for_lap
                                if time_diff < 0:
                                    time_text = f"-{self.format_lap_time(abs(time_diff))}"
                                    time_color = "#4CAF50"
                                else:
                                    time_text = f"+{self.format_lap_time(time_diff)}"
                                    time_color = self.get_difference_color(time_diff)
                            else:
                                time_text = self.format_lap_time(current_time)
                                time_color = skier.get_color()
                        else:
                            time_text = self.format_lap_time(lap_time)
                            time_color = skier.get_color()
                    elif best_time_for_lap is not None:
                        # Отставание от лучшего времени
                        time_diff = lap_time - best_time_for_lap
                        if time_diff == 0:
                            time_text = self.format_lap_time(lap_time)
                            time_color = "#2196F3"  # Синий, если время совпадает с лучшим
                        else:
                            time_text = f"+{self.format_lap_time(time_diff)}"
                            time_color = self.get_difference_color(time_diff)
                    else:
                        time_text = self.format_lap_time(lap_time)
                        time_color = skier.get_color()
                    
                    time_label = tk.Label(
                        self.large_view_widgets['table_frame'],
                        text=time_text,
                        font=("Courier New", 11),
                        bg=chroma_key_green,
                        fg=time_color
                    )
                    time_label.grid(row=row, column=2, padx=8, pady=8, sticky="w")
                    self.large_view_widgets['table_labels'].append(time_label)
                else:
                    # Нет данных для этой строки
                    no_data_label = tk.Label(
                        self.large_view_widgets['table_frame'],
                        text="---",
                        font=("Arial", 11),
                        bg=chroma_key_green,
                        fg="white"  # Белый текст
                    )
                    no_data_label.grid(row=row, column=0, columnspan=3, padx=8, pady=8, sticky="w")
                    self.large_view_widgets['table_labels'].append(no_data_label)
        else:
            # Нет данных вообще - показываем сообщение
            for i in range(3):
                row = i + 1
                no_data_label = tk.Label(
                    self.large_view_widgets['table_frame'],
                    text="Нет данных",
                    font=("Arial", 11),
                    bg=chroma_key_green,
                    fg="white"  # Белый текст
                )
                no_data_label.grid(row=row, column=0, columnspan=3, padx=8, pady=8, sticky="w")
                self.large_view_widgets['table_labels'].append(no_data_label)
    
    def update_large_view(self, stopwatch, show_post_lap=False):
        """Обновляет увеличенный вид"""
        if self.current_large_view == stopwatch:
            # Проверяем, нужно ли показывать результат после круга
            if stopwatch.just_completed_lap and stopwatch.lap_completion_time:
                elapsed = (datetime.now() - stopwatch.lap_completion_time).total_seconds()
                if elapsed < self.post_lap_duration:
                    show_post_lap = True
                else:
                    stopwatch.just_completed_lap = False
                    show_post_lap = False
            
            if show_post_lap:
                # Режим показа результата - используем замороженный круг
                current_lap = len(stopwatch.lap_times)  # Только что завершенный круг
                is_racing = False
                
                # Обновляем таймер
                if self.large_view_widgets.get('timer_label'):
                    elapsed = (datetime.now() - stopwatch.lap_completion_time).total_seconds()
                    remaining = max(0, self.post_lap_duration - elapsed)
                    self.large_view_widgets['timer_label'].config(text=f"  ({remaining:.1f}с)")
                
                # НЕ обновляем таблицу и основное время - они заморожены
                # Пропускаем обновление данных
                pass
            else:
                # Обычный режим - обновляем всё
                current_lap = stopwatch.get_current_lap() + 1
                is_racing = stopwatch.running and (current_lap > len(stopwatch.lap_times))
                
                # Обновляем основное время
                if stopwatch.running and self.large_view_widgets.get('main_time_label'):
                    current_time = (stopwatch.elapsed_time + 
                                   (datetime.now() - stopwatch.start_time).total_seconds())
                    
                    best_time, best_skier, _ = self.get_best_time_for_current_lap(current_lap)
                    if best_skier and current_lap <= len(best_skier.lap_times):
                        time_diff = current_time - best_time
                        
                        if time_diff < 0:
                            time_text = f"-{self.format_lap_time(abs(time_diff))}"
                            time_color = "#4CAF50"
                        else:
                            time_text = f"+{self.format_lap_time(time_diff)}"
                            time_color = self.get_countdown_color(time_diff)
                    else:
                        time_text = stopwatch.format_time(current_time)
                        time_color = stopwatch.get_color()
                    
                    self.large_view_widgets['main_time_label'].config(text=time_text, fg=time_color)
                
                # Обновляем таблицу соседей
                if self.large_view_widgets.get('table_frame'):
                    self.update_table_data(stopwatch, current_lap, is_racing, show_post_lap)
            
            # Обновляем состояние кнопок (всегда)
            self.large_start_btn.config(
                state="normal" if not stopwatch.running else "disabled",
                bg="#4CAF50" if not stopwatch.running else "#81C784"
            )
            self.large_stop_btn.config(
                state="normal" if stopwatch.running else "disabled",
                bg="#f44336" if stopwatch.running else "#E57373"
            )
            self.large_lap_btn.config(
                state="normal" if stopwatch.running else "disabled",
                bg="#FF9800"
            )
            
            # Планируем следующее обновление
            self.root.after(100, lambda: self.update_large_view(stopwatch, show_post_lap))

    def clear_large_view(self):
        """Очищает увеличенный вид"""
        self.current_large_view = None
        self.show_post_lap_result = False
        
        # Хромакейный зеленый цвет
        chroma_key_green = "#00FF00"
        
        # Очищаем контейнер
        for widget in self.large_view_container.winfo_children():
            widget.destroy()
        
        # Показываем первоначальное сообщение
        self.large_view_label = tk.Label(
            self.large_view_container,
            text="Выберите лыжника\nдля увеличенного отображения",
            font=("Arial", 14),
            bg=chroma_key_green,
            fg="white",  # Белый текст
            justify="center"
        )
        self.large_view_label.pack(expand=True)

    def get_countdown_color(self, remaining_time):
        """Возвращает цвет для обратного отсчета"""
        if remaining_time < 5:
            return "#f44336"  # Красный
        elif remaining_time < 10:
            return "#FF9800"  # Оранжевый
        else:
            return "#795548"  # Коричневый (для отставания)
    
    def get_place_color(self, place):
        """Возвращает цвет для места"""
        if place == 1:
            return "#FFD700"  # Золотой
        elif place == 2:
            return "#C0C0C0"  # Серебряный
        elif place == 3:
            return "#CD7F32"  # Бронзовый
        else:
            return "#666"  # Серый
    
    def get_difference_color(self, difference):
        """Возвращает цвет для разницы во времени"""
        if difference <= 5:
            return "#FF9800"  # Оранжевый
        else:
            return "#f44336"  # Красный
    
    
    def clear_large_view(self):
        """Очищает увеличенный вид"""
        self.current_large_view = None
        self.show_post_lap_result = False
        
        # Очищаем контейнер
        for widget in self.large_view_container.winfo_children():
            widget.destroy()
        
        # Показываем первоначальное сообщение
        self.large_view_label = tk.Label(
            self.large_view_container,
            text="Выберите лыжника\nдля увеличенного отображения",
            font=("Arial", 14),
            bg="#f0f0f0",
            fg="#666",
            justify="center"
        )
        self.large_view_label.pack(expand=True)
    
    def get_all_laps_sorted_by_number_and_time(self):
        """Возвращает все круги всех лыжников, сгруппированные по номеру круга и отсортированные по времени"""
        # Собираем все круги всех лыжников
        all_laps = []
        
        for stopwatch in self.stopwatches:
            for lap_num, lap_time in enumerate(stopwatch.lap_times, 1):
                all_laps.append({
                    'stopwatch_name': stopwatch.get_name(),
                    'lap_number': lap_num,
                    'lap_time': lap_time,
                    'stopwatch_color': stopwatch.get_color(),
                    'stopwatch': stopwatch
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
        """Обновляет отображение всех кругов в правой нижней панели в горизонтальном формате"""
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
            # Создаем основной контейнер для горизонтального отображения кругов
            laps_container = tk.Frame(self.laps_frame, bg="#e8f5e8")
            laps_container.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Определяем максимальное количество лыжников на любом круге
            max_skiers_per_lap = max(len(laps) for laps in laps_by_number.values()) if laps_by_number else 0
            
            # Отображаем круги по горизонтали (вправо)
            for lap_number in sorted(laps_by_number.keys()):
                # Контейнер для одного круга (вертикальная колонка)
                lap_column = tk.Frame(laps_container, bg="#e8f5e8", relief="ridge", borderwidth=1)
                lap_column.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                
                # Заголовок круга
                lap_header = tk.Label(
                    lap_column,
                    text=f"Круг {lap_number}",
                    font=("Arial", 12, "bold"),
                    bg="#2E7D32",
                    fg="white",
                    width=15,
                    relief="raised"
                )
                lap_header.pack(fill="x", pady=(0, 5))
                
                # Получаем лыжников на этом круге
                lap_skiers = laps_by_number[lap_number]
                
                # Отображаем лыжников вертикально (сверху вниз)
                for skier_info in lap_skiers:
                    # Форматируем время
                    time_str = self.format_lap_time(skier_info['lap_time'])
                    
                    # Создаем фрейм для одного лыжника на круге
                    skier_frame = tk.Frame(lap_column, bg="#e8f5e8", relief="flat")
                    skier_frame.pack(fill="x", pady=2)
                    
                    # Имя лыжника (сокращаем если слишком длинное)
                    skier_name = skier_info['stopwatch_name']
                    if len(skier_name) > 15:
                        skier_name = skier_name[:12] + "..."
                    
                    name_label = tk.Label(
                        skier_frame,
                        text=skier_name,
                        font=("Arial", 10),
                        bg="#e8f5e8",
                        fg=skier_info['stopwatch_color'],
                        anchor="w",
                        width=12
                    )
                    name_label.pack(side="left", padx=(5, 2))
                    
                    # Время круга
                    time_label = tk.Label(
                        skier_frame,
                        text=time_str,
                        font=("Courier New", 9),
                        bg="#e8f5e8",
                        fg=skier_info['stopwatch_color'],
                        anchor="w"
                    )
                    time_label.pack(side="left", padx=(2, 5))
                
                # Если в этом круге меньше лыжников, чем в максимальном, добавляем пустые строки
                for _ in range(max_skiers_per_lap - len(lap_skiers)):
                    empty_frame = tk.Frame(lap_column, bg="#e8f5e8", height=25)
                    empty_frame.pack(fill="x", pady=2)
                    empty_frame.pack_propagate(False)
        
        else:
            # Если нет кругов ни у одного лыжника
            no_laps_label = tk.Label(
                self.laps_frame,
                text="Круги еще не зафиксированы\nнажмите кнопку 'Круг'\nво время работы секундомера",
                font=("Arial", 11),
                bg="#e8f5e8",
                fg="#666",
                justify="center"
            )
            no_laps_label.pack(expand=True, pady=20)
        
        # Обновляем увеличенный вид, если он активен
        if self.current_large_view:
            # Проверяем, не показывается ли результат после круга
            show_post_lap = False
            if self.current_large_view.just_completed_lap and self.current_large_view.lap_completion_time:
                elapsed = (datetime.now() - self.current_large_view.lap_completion_time).total_seconds()
                if elapsed < self.post_lap_duration:
                    show_post_lap = True
            
            # Если показывается результат после круга, НЕ обновляем таблицу
            if not show_post_lap:
                self.show_large_view(self.current_large_view)
    
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
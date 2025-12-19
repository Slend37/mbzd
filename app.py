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
        self.current_large_view = None  # Текущий отображаемый крупно лыжник
        
        # Для хранения информации об обратном отсчете
        self.countdown_target_time = 0  # Целевое время для обратного отсчета
        self.countdown_best_stopwatch_name = ""  # Имя лыжника с лучшим временем
        self.countdown_best_stopwatch_color = ""  # Цвет лыжника с лучшим временем
        self.show_post_lap_result = False  # Флаг показа результата после круга
        self.post_lap_start_time = None  # Время начала показа результата после круга
        self.post_lap_duration = 5  # Длительность показа результата после круга (сек)
        
        # Создаем основной интерфейс
        self.create_widgets()
        
    def create_widgets(self):
        """Создание интерфейса приложения"""
        # Основной контейнер с разделением на левую и правую части
        main_container = tk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ЛЕВАЯ ПАНЕЛЬ - список лыжников (занимает всю левую сторону)
        left_panel = tk.Frame(main_container, width=700)  # Увеличил ширину
        left_panel.pack(side="left", fill="both", expand=True)
        
        self.create_left_panel(left_panel)
        
        # ПРАВАЯ ПАНЕЛЬ - разделена на верхнюю (увеличенный вид) и нижнюю (круги)
        right_panel = tk.Frame(main_container, width=450)  # Увеличил ширину
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.create_top_right_panel(right_panel)
        self.create_bottom_right_panel(right_panel)
        
        # Изначально создаем 5 лыжников
        for i in range(5):
            self.add_stopwatch()
        
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
        
        # Заголовки колонок
        headers_frame = tk.Frame(parent)
        headers_frame.pack(fill="x", pady=5)
        
        # Колонки с увеличенными ширинами
        tk.Label(headers_frame, text="Номер и имя", font=("Arial", 11, "bold"), width=25).grid(row=0, column=0, padx=5)
        tk.Label(headers_frame, text="Время", font=("Arial", 11, "bold"), width=15).grid(row=0, column=1, padx=5)
        tk.Label(headers_frame, text="Управление", font=("Arial", 11, "bold"), width=55).grid(row=0, column=2, padx=5)
        
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
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.scrollbar.pack(side="right", fill="y")
        
        # Кнопка сброса всех лыжников
        reset_all_button = tk.Button(
            parent,
            text="Сбросить всех",
            command=self.reset_all,
            font=("Arial", 11),
            bg="#f44336",
            fg="white",
            height=1,
            width=20
        )
        reset_all_button.pack(pady=10)
    
    def create_top_right_panel(self, parent):
        """Создание верхней правой панели (увеличенный вид)"""
        top_right_panel = tk.Frame(parent, height=380, relief="ridge", borderwidth=2, bg="#f0f0f0")  # Увеличил высоту
        top_right_panel.pack(side="top", fill="both", expand=True, pady=(0, 10))
        top_right_panel.pack_propagate(False)  # Фиксируем высоту
        
        # Заголовок верхней правой панели
        top_right_title = tk.Label(
            top_right_panel, 
            text="Увеличенный вид",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0"
        )
        top_right_title.pack(pady=15)
        
        # Контейнер для увеличенного отображения
        self.large_view_container = tk.Frame(top_right_panel, bg="#f0f0f0")
        self.large_view_container.pack(fill="both", expand=True, padx=25, pady=10)  # Увеличил отступы
        
        # Изначальное сообщение
        self.large_view_label = tk.Label(
            self.large_view_container,
            text="Выберите лыжника\nдля увеличенного отображения",
            font=("Arial", 14),
            bg="#f0f0f0",
            fg="#666",
            justify="center"
        )
        self.large_view_label.pack(expand=True)
    
    def create_bottom_right_panel(self, parent):
        """Создание нижней правой панели (круги всех лыжников)"""
        bottom_right_panel = tk.Frame(parent, relief="ridge", borderwidth=2, bg="#e8f5e8")
        bottom_right_panel.pack(side="bottom", fill="both", expand=True)
        
        # Заголовок нижней правой панели
        bottom_right_title = tk.Label(
            bottom_right_panel, 
            text="Круги (сортировка: номер → время)",
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
        """Возвращает лыжников для отображения в таблице"""
        # Получаем лучший результат на текущем круге
        best_time, best_skier, best_color = self.get_best_time_for_current_lap(current_lap)
        
        if not best_skier:
            return None, [], None
        
        # Если лыжник еще не завершил круг
        if is_racing or selected_skier.get_current_lap() < current_lap:
            # Находим позицию лыжника среди тех, кто уже завершил круг
            position, all_skiers, neighbors = self.get_skier_position_on_lap(selected_skier, current_lap)
            
            if not all_skiers:
                # Никто еще не завершил круг
                return best_skier, [], None
            
            # Находим соседей для отображения
            display_skiers = []
            
            # 1. Лучший лыжник круга
            display_skiers.append({
                'stopwatch': best_skier,
                'lap_time': best_time,
                'position': 1,
                'is_best': True
            })
            
            # 2. Ближайший лыжник перед текущим (если есть)
            if position and position > 1:
                # Ищем лыжника на позиции перед текущим
                for skier in all_skiers:
                    if skier['position'] == position - 1:
                        display_skiers.append(skier)
                        break
            
            # 3. Ближайший лыжник после текущего (если есть)
            if position and position < len(all_skiers):
                # Ищем лыжника на позиции после текущего
                for skier in all_skiers:
                    if skier['position'] == position + 1:
                        display_skiers.append(skier)
                        break
            
            # Если не нашли соседей, берем следующих после лучшего
            while len(display_skiers) < 3 and len(display_skiers) < len(all_skiers):
                next_pos = len(display_skiers) + 1
                for skier in all_skiers:
                    if skier['position'] == next_pos and skier['stopwatch'] != best_skier:
                        display_skiers.append(skier)
                        break
            
            return best_skier, display_skiers, position
        
        else:
            # Лыжник завершил круг, показываем его результат
            position, all_skiers, neighbors = self.get_skier_position_on_lap(selected_skier, current_lap)
            
            if not all_skiers:
                return best_skier, [], None
            
            display_skiers = []
            
            # 1. Лучший лыжник круга
            display_skiers.append({
                'stopwatch': best_skier,
                'lap_time': best_time,
                'position': 1,
                'is_best': True
            })
            
            # 2. Текущий лыжник
            for skier in all_skiers:
                if skier['stopwatch'] == selected_skier:
                    display_skiers.append(skier)
                    break
            
            # 3. Лыжник после текущего (если есть)
            if position and position < len(all_skiers):
                for skier in all_skiers:
                    if skier['position'] == position + 1:
                        display_skiers.append(skier)
                        break
            
            return best_skier, display_skiers, position
    
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
        
        # Очищаем контейнер
        for widget in self.large_view_container.winfo_children():
            widget.destroy()
        
        # Основной контейнер для увеличенного вида
        main_large_frame = tk.Frame(self.large_view_container, bg="#f0f0f0")
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
                current_lap = len(stopwatch.lap_times)  # Только что завершенный круг
                is_racing = False
            else:
                stopwatch.just_completed_lap = False
        
        # Получаем данные для отображения
        best_skier, display_skiers, position = self.get_display_neighbors(stopwatch, current_lap, is_racing)
        
        # Первая строка: информация о лыжнике
        first_row_frame = tk.Frame(main_large_frame, bg="#f0f0f0")
        first_row_frame.pack(fill="x", pady=(0, 25))  # Увеличил отступ
        
        # Левый блок: основная информация о лыжнике
        left_info_frame = tk.Frame(first_row_frame, bg="#f0f0f0")
        left_info_frame.pack(side="left", fill="both", expand=True)
        
        # Идентификатор и название лыжника
        id_name_frame = tk.Frame(left_info_frame, bg="#f0f0f0")
        id_name_frame.pack(fill="x", pady=(0, 15))  # Увеличил отступ
        
        # Идентификатор лыжника
        id_label = tk.Label(
            id_name_frame,
            text=f"[{stopwatch.number}]",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0",
            fg="#666"
        )
        id_label.pack(side="left", padx=(0, 15))  # Увеличил отступ
        
        # Название лыжника
        name_label = tk.Label(
            id_name_frame,
            text=stopwatch.get_name(),
            font=("Arial", 16, "bold"),
            bg="#f0f0f0",
            fg=stopwatch.get_color()
        )
        name_label.pack(side="left", padx=(0, 30))  # Увеличил отступ
        
        # Время лыжника
        time_frame = tk.Frame(left_info_frame, bg="#f0f0f0")
        time_frame.pack(fill="x")
        
        # Формируем текст для основного времени
        time_text = ""
        time_color = stopwatch.get_color()
        
        if best_skier and best_skier.lap_times and current_lap <= len(best_skier.lap_times):
            best_time = best_skier.lap_times[current_lap - 1]
            
            if stopwatch.running and current_lap > len(stopwatch.lap_times):
                # Лыжник еще бежит текущий круг
                current_time = (stopwatch.elapsed_time + 
                               (datetime.now() - stopwatch.start_time).total_seconds())
                time_diff = current_time - best_time
                
                if time_diff < 0:
                    time_text = f"-{self.format_lap_time(abs(time_diff))}"
                    time_color = "#4CAF50"  # Зеленый - опережение
                else:
                    time_text = f"+{self.format_lap_time(time_diff)}"
                    time_color = self.get_countdown_color(time_diff)
            elif not is_racing and current_lap <= len(stopwatch.lap_times):
                # Лыжник завершил круг
                skier_time = stopwatch.lap_times[current_lap - 1]
                time_diff = skier_time - best_time
                
                if show_post_lap:
                    # Показываем абсолютное время в течение 5 секунд
                    time_text = self.format_lap_time(skier_time)
                    time_color = stopwatch.get_color()
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
            time_text = stopwatch.time_label.cget("text")
        
        self.main_time_label = tk.Label(
            time_frame,
            text=time_text,
            font=("Courier New", 28, "bold"),
            bg="#f0f0f0",
            fg=time_color
        )
        self.main_time_label.pack(side="left")
        
        # Если показываем результат после круга, добавляем таймер
        if show_post_lap:
            elapsed = (datetime.now() - stopwatch.lap_completion_time).total_seconds()
            remaining = max(0, self.post_lap_duration - elapsed)
            
            timer_label = tk.Label(
                time_frame,
                text=f"  ({remaining:.1f}с)",
                font=("Arial", 12),
                bg="#f0f0f0",
                fg="#666"
            )
            timer_label.pack(side="left", padx=(10, 0))
        
        # Правый блок: таблица сравнения
        right_table_frame = tk.Frame(first_row_frame, bg="#f0f0f0")
        right_table_frame.pack(side="right", fill="both", padx=(30, 0))  # Увеличил отступ
        
        # Создаем таблицу 3x3 с увеличенными размерами
        table_frame = tk.Frame(right_table_frame, bg="#f0f0f0")
        table_frame.pack()
        
        # Заголовки столбцов
        headers = ["Место", "Лыжник", "Время"]
        for col, header in enumerate(headers):
            header_label = tk.Label(
                table_frame,
                text=header,
                font=("Arial", 12, "bold"),
                bg="#f0f0f0",
                fg="#333",
                width=20  # Увеличил ширину
            )
            header_label.grid(row=0, column=col, padx=8, pady=8, sticky="w")  # Увеличил отступы
        
        # Заполняем таблицу данными
        for i in range(3):
            row = i + 1
            
            if i < len(display_skiers):
                skier_info = display_skiers[i]
                skier = skier_info['stopwatch']
                lap_time = skier_info['lap_time']
                position = skier_info['position']
                
                # Лучшее время на круге
                if best_skier and current_lap <= len(best_skier.lap_times):
                    best_time = best_skier.lap_times[current_lap - 1]
                    time_diff = lap_time - best_time
                    
                    # Место
                    place_label = tk.Label(
                        table_frame,
                        text=f"[{position}]",
                        font=("Arial", 11, "bold"),
                        bg="#f0f0f0",
                        fg=self.get_place_color(position)
                    )
                    place_label.grid(row=row, column=0, padx=8, pady=8, sticky="w")
                    
                    # Имя лыжника
                    name_label = tk.Label(
                        table_frame,
                        text=skier.get_name(),
                        font=("Arial", 11),
                        bg="#f0f0f0",
                        fg=skier.get_color()
                    )
                    name_label.grid(row=row, column=1, padx=8, pady=8, sticky="w")
                    
                    # Время или отставание
                    if position == 1:
                        # Лучшее время круга
                        time_text = self.format_lap_time(lap_time)
                        time_color = "#2196F3"  # Синий для рекорда
                    else:
                        # Отставание от лучшего времени
                        time_text = f"+{self.format_lap_time(time_diff)}"
                        time_color = self.get_difference_color(time_diff)
                    
                    time_label = tk.Label(
                        table_frame,
                        text=time_text,
                        font=("Courier New", 11),
                        bg="#f0f0f0",
                        fg=time_color
                    )
                    time_label.grid(row=row, column=2, padx=8, pady=8, sticky="w")
            else:
                # Нет данных
                no_data_label = tk.Label(
                    table_frame,
                    text="---",
                    font=("Arial", 11),
                    bg="#f0f0f0",
                    fg="#666",
                    width=20
                )
                no_data_label.grid(row=row, column=0, columnspan=3, padx=8, pady=8, sticky="w")
        
        # Вторая строка: кнопки управления
        second_row_frame = tk.Frame(main_large_frame, bg="#f0f0f0")
        second_row_frame.pack(fill="x", pady=30)  # Увеличил отступ
        
        # Создаем кнопки управления
        large_buttons_frame = tk.Frame(second_row_frame, bg="#f0f0f0")
        large_buttons_frame.pack()
        
        # Кнопка Старт
        self.large_start_btn = tk.Button(
            large_buttons_frame,
            text="СТАРТ",
            command=stopwatch.start,
            width=12,  # Увеличил ширину
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
            bg="#9E9E9E",
            fg="white"
        )
        hide_button.pack(pady=10)
        
        # Запускаем обновление времени в увеличенном виде
        self.update_large_view(stopwatch, show_post_lap)
    
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
    
    def update_large_view(self, stopwatch, show_post_lap=False):
        """Обновляет увеличенный вид"""
        if self.current_large_view == stopwatch:
            # Получаем текущий круг
            current_lap = stopwatch.get_current_lap() + 1
            if show_post_lap:
                current_lap = len(stopwatch.lap_times)
            
            is_racing = stopwatch.running and (current_lap > len(stopwatch.lap_times))
            
            # Получаем данные для отображения
            best_skier, display_skiers, position = self.get_display_neighbors(stopwatch, current_lap, is_racing)
            
            # Обновляем основное время
            if stopwatch.running and not show_post_lap:
                current_time = (stopwatch.elapsed_time + 
                               (datetime.now() - stopwatch.start_time).total_seconds())
                
                if best_skier and current_lap <= len(best_skier.lap_times):
                    best_time = best_skier.lap_times[current_lap - 1]
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
                
                self.main_time_label.config(text=time_text, fg=time_color)
            
            # Обновляем состояние кнопок
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
            
            # Проверяем, не истекло ли время показа результата после круга
            if stopwatch.just_completed_lap and stopwatch.lap_completion_time:
                elapsed = (datetime.now() - stopwatch.lap_completion_time).total_seconds()
                if elapsed >= self.post_lap_duration:
                    stopwatch.just_completed_lap = False
                    # Обновляем вид
                    self.show_large_view(stopwatch)
            
            # Планируем следующее обновление
            self.root.after(10, lambda: self.update_large_view(stopwatch, show_post_lap))
    
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
                    font=("Arial", 11, "bold"),
                    bg="#e8f5e8",
                    fg="#2E7D32",
                    anchor="w"
                )
                group_header.pack(fill="x", pady=(8, 3), padx=5)
                
                # Отображаем все круги с этим номером, отсортированные по времени
                for lap_info in laps_by_number[lap_number]:
                    # Форматируем время
                    time_str = self.format_lap_time(lap_info['lap_time'])
                    
                    # Создаем метку для круга с цветом лыжника
                    lap_text = f"  {lap_info['stopwatch_name']}: {time_str}"
                    lap_label = tk.Label(
                        self.laps_frame,
                        text=lap_text,
                        font=("Courier New", 10),
                        bg="#e8f5e8",
                        fg=lap_info['stopwatch_color'],
                        anchor="w"
                    )
                    lap_label.pack(fill="x", pady=1, padx=15)  # Увеличил отступы
        
        # Если нет кругов ни у одного лыжника
        if not laps_by_number:
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
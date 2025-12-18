import tkinter as tk
from datetime import datetime, timedelta
from collections import defaultdict
from stopwatch import Stopwatch

class StopwatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Компактные секундомеры с обратным отсчетом")
        self.root.geometry("1100x700")
        
        # Список для хранения всех секундомеров
        self.stopwatches = []
        self.current_large_view = None  # Текущий отображаемый крупно секундомер
        
        # Для хранения информации об обратном отсчете
        self.countdown_target_time = 0  # Целевое время для обратного отсчета
        self.countdown_best_stopwatch_name = ""  # Имя секундомера с лучшим временем
        self.countdown_best_stopwatch_color = ""  # Цвет секундомера с лучшим временем
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
        
    def get_best_time_for_next_lap(self, stopwatch):
        """Возвращает лучшее время на следующем круге для выбранного секундомера"""
        current_lap = stopwatch.get_current_lap()  # Текущий номер круга
        next_lap_number = current_lap + 1  # Номер следующего круга
        
        # Получаем все круги всех секундомеров
        all_laps = []
        
        for sw in self.stopwatches:
            for lap_num, lap_time in enumerate(sw.lap_times, 1):
                all_laps.append({
                    'stopwatch_name': sw.get_name(),
                    'stopwatch_color': sw.get_color(),
                    'lap_number': lap_num,
                    'lap_time': lap_time
                })
        
        # Находим лучший результат на следующем круге
        best_time = None
        best_stopwatch_name = ""
        best_stopwatch_color = ""
        
        for lap in all_laps:
            if lap['lap_number'] == next_lap_number:
                if best_time is None or lap['lap_time'] < best_time:
                    best_time = lap['lap_time']
                    best_stopwatch_name = lap['stopwatch_name']
                    best_stopwatch_color = lap['stopwatch_color']
        
        return best_time, best_stopwatch_name, best_stopwatch_color
    
    def add_stopwatch(self):
        """Добавляет новый секундомер"""
        # Добавляем новый секундомер с номером, который на 1 больше текущего количества
        stopwatch = Stopwatch(self.stopwatches_frame, len(self.stopwatches) + 1, self)
        self.stopwatches.append(stopwatch)
        
        # Обновляем отображение кругов
        self.update_all_laps_display()
        
    def remove_stopwatch(self, stopwatch):
        """Удаляет секундомер"""
        if len(self.stopwatches) > 1:  # Оставляем хотя бы один секундомер
            # Если удаляем тот, что отображается крупно
            if self.current_large_view == stopwatch:
                self.clear_large_view()
            
            stopwatch.destroy()
            self.stopwatches.remove(stopwatch)
            
            # Обновляем номера оставшихся секундомеров, сохраняя их имена
            for i, sw in enumerate(self.stopwatches, 1):
                sw.update_display_number(i)
            
            self.update_all_laps_display()
    
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
        
        # Основной контейнер для увеличенного вида
        main_large_frame = tk.Frame(self.large_view_container, bg="#f0f0f0")
        main_large_frame.pack(fill="both", expand=True)
        
        # Верхняя часть: имя и текущее время секундомера
        top_frame = tk.Frame(main_large_frame, bg="#f0f0f0")
        top_frame.pack(fill="x", pady=(0, 15))
        
        # Отображаем имя секундомера
        selected_name_label = tk.Label(
            top_frame,
            text=stopwatch.get_name(),
            font=("Arial", 14, "bold"),
            bg="#f0f0f0",
            fg=stopwatch.get_color()
        )
        selected_name_label.pack(pady=(5, 5))
        
        # Отображаем время крупным шрифтом
        self.large_time_label = tk.Label(
            top_frame,
            text=stopwatch.time_label.cget("text"),
            font=("Courier New", 32, "bold"),
            bg="#f0f0f0",
            fg=stopwatch.get_color()
        )
        self.large_time_label.pack(pady=10)
        
        # Создаем кнопки управления
        large_buttons_frame = tk.Frame(top_frame, bg="#f0f0f0")
        
        # Кнопка Старт для увеличенного вида
        self.large_start_btn = tk.Button(
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
        self.large_start_btn.pack(side="left", padx=3, pady=5)
        
        # Кнопка Стоп для увеличенного вида
        self.large_stop_btn = tk.Button(
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
        self.large_stop_btn.pack(side="left", padx=3, pady=5)
        
        # Кнопка Круг для увеличенного вида
        self.large_lap_btn = tk.Button(
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
        self.large_lap_btn.pack(side="left", padx=3, pady=5)
        
        large_buttons_frame.pack(pady=10)
        
        # Нижняя часть: обратный отсчет до лучшего времени на следующем круге
        self.bottom_frame = tk.Frame(main_large_frame, bg="#f0f0f0")
        self.bottom_frame.pack(fill="both", expand=True)
        
        # Проверяем, нужно ли показывать результат после круга
        if stopwatch.just_completed_lap and stopwatch.lap_completion_time:
            elapsed = (datetime.now() - stopwatch.lap_completion_time).total_seconds()
            if elapsed < self.post_lap_duration:
                # Показываем результат после круга
                self.show_post_lap_result = True
                self.post_lap_start_time = datetime.now()
                self.show_post_lap_view(stopwatch)
            else:
                # Время показа результата истекло
                stopwatch.just_completed_lap = False
                self.show_post_lap_result = False
                self.show_countdown_view(stopwatch)
        else:
            # Обычный режим - показываем обратный отсчет
            self.show_post_lap_result = False
            self.show_countdown_view(stopwatch)
        
        # Кнопка скрытия увеличенного вида
        hide_button = tk.Button(
            main_large_frame,
            text="Скрыть увеличенный вид",
            command=self.clear_large_view,
            font=("Arial", 9),
            bg="#9E9E9E",
            fg="white"
        )
        hide_button.pack(pady=20)
        
        # Запускаем обновление времени в увеличенном виде
        self.update_large_view(stopwatch)
    
    def show_countdown_view(self, stopwatch):
        """Показывает вид с обратным отсчетом до лучшего времени"""
        # Очищаем нижнюю часть
        for widget in self.bottom_frame.winfo_children():
            widget.destroy()
        
        # Получаем лучшее время на следующем круге
        best_time, best_name, best_color = self.get_best_time_for_next_lap(stopwatch)
        
        if best_time is not None:
            # Сохраняем информацию для обратного отсчета
            self.countdown_target_time = best_time
            self.countdown_best_stopwatch_name = best_name
            self.countdown_best_stopwatch_color = best_color
            
            # Заголовок для обратного отсчета
            countdown_title = tk.Label(
                self.bottom_frame,
                text=f"До лучшего времени {stopwatch.get_current_lap() + 1}-го круга:",
                font=("Arial", 11, "bold"),
                bg="#f0f0f0",
                fg="#333",
                wraplength=350
            )
            countdown_title.pack(pady=(5, 5))
            
            # Отображаем имя лучшего секундомера в новом формате
            best_info_label = tk.Label(
                self.bottom_frame,
                text=f"{best_name}",
                font=("Arial", 12, "bold"),
                bg="#f0f0f0",
                fg=best_color
            )
            best_info_label.pack(pady=(0, 10))
            
            # Отображаем обратный отсчет
            self.countdown_label = tk.Label(
                self.bottom_frame,
                text=f"{best_name}"+"--:--.--",
                font=("Courier New", 28, "bold"),
                bg="#f0f0f0",
                fg="#FF5722"  # Оранжевый цвет для обратного отсчета
            )
            self.countdown_label.pack(pady=10)
            
            # Обновляем обратный отсчет
            self.update_countdown(stopwatch)
        else:
            # Нет данных для следующего круга
            no_data_label = tk.Label(
                self.bottom_frame,
                text=f"Нет данных для {stopwatch.get_current_lap() + 1}-го круга\nНачните замер времени на следующем круге",
                font=("Arial", 11),
                bg="#f0f0f0",
                fg="#666",
                justify="center"
            )
            no_data_label.pack(expand=True, pady=20)
    
    def show_post_lap_view(self, stopwatch):
        """Показывает результат после завершения круга"""
        # Очищаем нижнюю часть
        for widget in self.bottom_frame.winfo_children():
            widget.destroy()
        
        # Получаем лучший результат на только что завершенном круге
        current_lap = stopwatch.get_current_lap()  # Только что завершенный круг
        best_time, best_name, best_color = self.get_best_time_for_completed_lap(stopwatch, current_lap)
        
        if best_time is not None:
            # Вычисляем разницу между временем выбранного секундомера и лучшим временем
            time_difference = stopwatch.last_lap_time - best_time
            
            # Заголовок для результата после круга
            result_title = tk.Label(
                self.bottom_frame,
                text=f"Результат {current_lap}-го круга:",
                font=("Arial", 11, "bold"),
                bg="#f0f0f0",
                fg="#333"
            )
            result_title.pack(pady=(5, 5))
            
            # Отображаем сравнение с лучшим временем
            comparison_label = tk.Label(
                self.bottom_frame,
                text=f"Сравнение с лучшим кругом:",
                font=("Arial", 10),
                bg="#f0f0f0",
                fg="#666"
            )
            comparison_label.pack(pady=(0, 5))
            
            # Лучший результат
            best_result_label = tk.Label(
                self.bottom_frame,
                text=f"{best_name}: {self.format_lap_time(best_time)}",
                font=("Arial", 11, "bold"),
                bg="#f0f0f0",
                fg=best_color
            )
            best_result_label.pack(pady=(0, 5))
            
            # Результат выбранного секундомера
            selected_result_label = tk.Label(
                self.bottom_frame,
                text=f"{stopwatch.get_name()}: {self.format_lap_time(stopwatch.last_lap_time)}",
                font=("Arial", 11),
                bg="#f0f0f0",
                fg=stopwatch.get_color()
            )
            selected_result_label.pack(pady=(0, 10))
            
            # Отображаем разницу
            self.result_label = tk.Label(
                self.bottom_frame,
                text=self.format_difference(stopwatch.get_name(),time_difference),
                font=("Courier New", 28, "bold"),
                bg="#f0f0f0",
                fg=self.get_difference_color(time_difference)
            )
            self.result_label.pack(pady=10)
            
            # Таймер показа результата
            self.post_lap_timer_label = tk.Label(
                self.bottom_frame,
                text=f"Показ результата: {self.post_lap_duration:.0f}с",
                font=("Arial", 9),
                bg="#f0f0f0",
                fg="#666"
            )
            self.post_lap_timer_label.pack(pady=5)
            
            # Обновляем таймер показа результата
            self.update_post_lap_timer(stopwatch)
        else:
            # Нет данных для сравнения
            no_comparison_label = tk.Label(
                self.bottom_frame,
                text="Нет данных для сравнения\nЭто первый круг",
                font=("Arial", 11),
                bg="#f0f0f0",
                fg="#666",
                justify="center"
            )
            no_comparison_label.pack(expand=True, pady=20)
    
    def get_best_time_for_completed_lap(self, stopwatch, lap_number):
        """Возвращает лучшее время на указанном круге (исключая только что завершенный круг выбранного секундомера)"""
        # Получаем все круги всех секундомеров
        all_laps = []
        
        for sw in self.stopwatches:
            for lap_num, lap_time in enumerate(sw.lap_times, 1):
                # Исключаем только что завершенный круг выбранного секундомера
                if not (sw == stopwatch and lap_num == lap_number):
                    all_laps.append({
                        'stopwatch_name': sw.get_name(),
                        'stopwatch_color': sw.get_color(),
                        'lap_number': lap_num,
                        'lap_time': lap_time
                    })
        
        # Находим лучший результат на указанном круге
        best_time = None
        best_stopwatch_name = ""
        best_stopwatch_color = ""
        
        for lap in all_laps:
            if lap['lap_number'] == lap_number:
                if best_time is None or lap['lap_time'] < best_time:
                    best_time = lap['lap_time']
                    best_stopwatch_name = lap['stopwatch_name']
                    best_stopwatch_color = lap['stopwatch_color']
        
        return best_time, best_stopwatch_name, best_stopwatch_color
    
    def update_large_view(self, stopwatch):
        """Обновляет увеличенный вид"""
        if self.current_large_view == stopwatch:
            # Обновляем время
            if stopwatch.running:
                current_elapsed = (stopwatch.elapsed_time + 
                                  (datetime.now() - stopwatch.start_time).total_seconds())
                self.large_time_label.config(text=stopwatch.format_time(current_elapsed))
            
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
            
            # Проверяем, нужно ли переключиться с показа результата после круга на обычный вид
            if stopwatch.just_completed_lap and stopwatch.lap_completion_time:
                elapsed = (datetime.now() - stopwatch.lap_completion_time).total_seconds()
                if elapsed >= self.post_lap_duration:
                    # Время показа результата истекло
                    stopwatch.just_completed_lap = False
                    self.show_post_lap_result = False
                    # Переключаемся на обычный вид
                    self.show_countdown_view(stopwatch)
            
            # Планируем следующее обновление
            self.root.after(10, lambda: self.update_large_view(stopwatch))
    
    def update_countdown(self, stopwatch):
        """Обновляет обратный отсчет до лучшего времени"""
        if self.current_large_view == stopwatch and not self.show_post_lap_result:
            if stopwatch.running:
                # Текущее время секундомера
                current_elapsed = (stopwatch.elapsed_time + 
                                  (datetime.now() - stopwatch.start_time).total_seconds())
                
                # Вычисляем оставшееся время до лучшего результата
                remaining_time = self.countdown_target_time - current_elapsed
                
                # Если время еще не достигло лучшего результата
                if remaining_time > 0:
                    # Форматируем оставшееся время
                    remaining_str = self.format_lap_time(remaining_time)
                    self.countdown_label.config(text=remaining_str)
                    
                    # Меняем цвет в зависимости от близости к цели
                    if remaining_time < 5:  # Меньше 5 секунд
                        self.countdown_label.config(fg="#f44336")  # Красный
                    elif remaining_time < 10:  # Меньше 10 секунд
                        self.countdown_label.config(fg="#FF9800")  # Оранжевый
                    else:
                        self.countdown_label.config(fg="#4CAF50")  # Зеленый
                else:
                    # Лучший результат достигнут или превышен
                    exceeded_time = abs(remaining_time)
                    exceeded_str = f"+{self.format_lap_time(exceeded_time)}"
                    self.countdown_label.config(text=exceeded_str, fg="#9C27B0")  # Фиолетовый
            
            # Планируем следующее обновление
            self.root.after(10, lambda: self.update_countdown(stopwatch))
    
    def update_post_lap_timer(self, stopwatch):
        """Обновляет таймер показа результата после круга"""
        if self.current_large_view == stopwatch and self.show_post_lap_result:
            if self.post_lap_start_time:
                elapsed = (datetime.now() - self.post_lap_start_time).total_seconds()
                remaining = max(0, self.post_lap_duration - elapsed)
                
                # Обновляем таймер
                self.post_lap_timer_label.config(text=f"Показ результата: {remaining:.1f}с")
                
                # Если время истекло, переключаемся на обычный вид
                if elapsed >= self.post_lap_duration:
                    stopwatch.just_completed_lap = False
                    self.show_post_lap_result = False
                    self.show_countdown_view(stopwatch)
                else:
                    # Планируем следующее обновление
                    self.root.after(100, lambda: self.update_post_lap_timer(stopwatch))
    
    def format_difference(self, name, difference):
        """Форматирует разницу во времени"""
        if difference > 0:
            return f"+{self.format_lap_time(difference)}"
        elif difference < 0:
            return f"-{self.format_lap_time(abs(difference))}"
        else:
            return "±00:00.00"
    
    def get_difference_color(self, difference):
        """Возвращает цвет для разницы во времени"""
        if difference < 0:  # Лучше лучшего времени
            return "#4CAF50"  # Зеленый
        elif difference == 0:  # Равно лучшему времени
            return "#2196F3"  # Синий
        elif difference <= 5:  # Немного хуже (до 5 секунд)
            return "#FF9800"  # Оранжевый
        else:  # Значительно хуже
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
        
        # Обновляем увеличенный вид, если он активен
        if self.current_large_view:
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
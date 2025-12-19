import tkinter as tk
from datetime import datetime

class Stopwatch:
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
        self.is_editing_name = False  # Флаг режима редактирования имени
        self.just_completed_lap = False  # Флаг только что завершенного круга
        self.lap_completion_time = None  # Время завершения круга
        self.last_lap_time = 0  # Время последнего круга
        
        # Создаем фрейм для этого лыжника в одну строку
        self.frame = tk.Frame(parent, height=45)  # Увеличил высоту
        self.frame.pack(fill="x", pady=3, padx=5)  # Увеличил отступы
        self.frame.pack_propagate(False)
        
        # Создаем элементы интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        """Создание виджетов для лыжника"""
        # Контейнер для названия
        self.name_container = tk.Frame(self.frame)
        self.name_container.grid(row=0, column=0, padx=5, sticky="w")
        
        # По умолчанию показываем метку с именем
        self.default_name = f"Лыжник {self.number}"
        self.name_label = tk.Label(
            self.name_container,
            text=self.default_name,
            font=("Arial", 10),  # Увеличил шрифт
            width=25,  # Увеличил ширину
            anchor="w",
            cursor="hand2"
        )
        self.name_label.pack(side="left")
        self.name_label.bind("<Button-1>", lambda e: self.start_name_editing())
        
        # Поле для редактирования имени (изначально скрыто)
        self.name_var = tk.StringVar(value=self.default_name)
        self.name_entry = tk.Entry(
            self.name_container,
            textvariable=self.name_var,
            width=25,  # Увеличил ширину
            font=("Arial", 10)  # Увеличил шрифт
        )
        
        # Кнопка сохранения имени (изначально скрыта)
        self.save_name_btn = tk.Button(
            self.name_container,
            text="✓",
            command=self.save_name,
            width=3,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 9)  # Увеличил шрифт
        )
        
        # Кнопка отмены редактирования (изначально скрыта)
        self.cancel_edit_btn = tk.Button(
            self.name_container,
            text="✕",
            command=self.cancel_name_editing,
            width=3,
            bg="#f44336",
            fg="white",
            font=("Arial", 9)  # Увеличил шрифт
        )
        
        # Отображение времени - кликабельно для выбора в увеличенный вид
        self.time_label = tk.Label(
            self.frame,
            text="00:00:00.00",
            font=("Courier New", 11, "bold"),  # Увеличил шрифт
            fg=self.color,
            width=18,  # Увеличил ширину
            anchor="w",
            cursor="hand2"
        )
        self.time_label.grid(row=0, column=1, padx=5, sticky="w")
        self.time_label.bind("<Button-1>", lambda e: self.select_for_large_view())
        
        # Фрейм для кнопок управления
        buttons_frame = tk.Frame(self.frame)
        buttons_frame.grid(row=0, column=2, padx=5, sticky="w")
        
        # Кнопка Старт
        self.start_btn = tk.Button(
            buttons_frame,
            text="Старт",
            command=self.start,
            width=8,  # Увеличил ширину
            bg="#4CAF50",
            fg="white",
            font=("Arial", 9)  # Увеличил шрифт
        )
        self.start_btn.pack(side="left", padx=2)  # Увеличил отступ
        
        # Кнопка Круг
        self.lap_btn = tk.Button(
            buttons_frame,
            text="Круг",
            command=self.record_lap,
            width=8,
            bg="#FF9800",
            fg="white",
            font=("Arial", 9),
            state="disabled"
        )
        self.lap_btn.pack(side="left", padx=2)
        
        # Кнопка Стоп
        self.stop_btn = tk.Button(
            buttons_frame,
            text="Стоп",
            command=self.stop,
            width=8,
            bg="#f44336",
            fg="white",
            font=("Arial", 9),
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=2)
        
        # Кнопка Сброс
        reset_btn = tk.Button(
            buttons_frame,
            text="Сброс",
            command=self.reset,
            width=8,
            bg="#9E9E9E",
            fg="white",
            font=("Arial", 9)
        )
        reset_btn.pack(side="left", padx=2)
        
        # Кнопка "Увеличить" для отображения в верхней правой панели
        enlarge_btn = tk.Button(
            buttons_frame,
            text="🔍",
            command=self.select_for_large_view,
            width=4,  # Увеличил ширину
            bg=self.color,
            fg="white",
            font=("Arial", 9)
        )
        enlarge_btn.pack(side="left", padx=2)
        
        # Кнопка удаления
        remove_btn = tk.Button(
            buttons_frame,
            text="✕",
            command=self.remove,
            width=4,
            bg="#333",
            fg="white",
            font=("Arial", 9)
        )
        remove_btn.pack(side="left", padx=2)
        
        # Индикатор кругов (количество)
        self.lap_indicator = tk.Label(
            self.frame,
            text="Круги: 0",
            font=("Arial", 9),
            fg=self.color,
            width=10  # Увеличил ширину
        )
        self.lap_indicator.grid(row=0, column=3, padx=5, sticky="w")
        
    def start_name_editing(self):
        """Начинает редактирование имени лыжника"""
        if not self.is_editing_name:
            self.is_editing_name = True
            
            # Скрываем метку
            self.name_label.pack_forget()
            
            # Показываем поле ввода и кнопки
            self.name_entry.pack(side="left")
            self.save_name_btn.pack(side="left", padx=3)  # Увеличил отступ
            self.cancel_edit_btn.pack(side="left", padx=3)
            
            # Фокус на поле ввода
            self.name_entry.focus_set()
            self.name_entry.select_range(0, tk.END)
            
            # Бинд нажатия Enter для сохранения и Escape для отмены
            self.name_entry.bind("<Return>", lambda e: self.save_name())
            self.name_entry.bind("<Escape>", lambda e: self.cancel_name_editing())
    
    def save_name(self):
        """Сохраняет новое имя лыжника"""
        new_name = self.name_var.get().strip()
        
        # Проверяем, что имя не пустое
        if new_name:
            # Сохраняем новое имя
            self.default_name = new_name
            
            # Обновляем метку
            self.name_label.config(text=new_name)
            
            # Обновляем отображение кругов
            self.app.update_all_laps_display()
            
            # Обновляем увеличенный вид, если этот лыжник отображается
            if self.app.current_large_view == self:
                self.app.show_large_view(self)
        
        # Завершаем редактирование
        self.finish_name_editing()
    
    def cancel_name_editing(self):
        """Отменяет редактирование имени"""
        # Восстанавливаем старое имя в поле ввода
        self.name_var.set(self.default_name)
        
        # Завершаем редактирование
        self.finish_name_editing()
    
    def finish_name_editing(self):
        """Завершает редактирование имени"""
        if self.is_editing_name:
            self.is_editing_name = False
            
            # Убираем бинды клавиш
            self.name_entry.unbind("<Return>")
            self.name_entry.unbind("<Escape>")
            
            # Скрываем поле ввода и кнопки
            self.name_entry.pack_forget()
            self.save_name_btn.pack_forget()
            self.cancel_edit_btn.pack_forget()
            
            # Показываем метку
            self.name_label.pack(side="left")
    
    def get_name(self):
        """Возвращает текущее имя лыжника"""
        return self.default_name
    
    def get_color(self):
        """Возвращает цвет этого лыжника"""
        return self.color
    
    def get_current_lap(self):
        """Возвращает текущий номер круга для этого лыжника"""
        return len(self.lap_times)
    
    def start(self):
        """Запуск лыжника"""
        if not self.running:
            self.running = True
            self.start_time = datetime.now()
            self.just_completed_lap = False
            self.start_btn.config(state="disabled", bg="#81C784")
            self.stop_btn.config(state="normal", bg="#f44336")
            self.lap_btn.config(state="normal", bg="#FF9800")
            self.update_time()
            
            # Обновляем увеличенный вид, если этот лыжник отображается
            if self.app.current_large_view == self:
                self.app.show_large_view(self)
            
            # Обновляем статистику
            self.app.update_all_laps_display()
    
    def stop(self):
        """Остановка лыжника"""
        if self.running:
            self.running = False
            if self.start_time:
                self.elapsed_time += (datetime.now() - self.start_time).total_seconds()
            self.start_btn.config(state="normal", bg="#4CAF50")
            self.stop_btn.config(state="disabled", bg="#E57373")
            self.lap_btn.config(state="disabled", bg="#FFB74D")
            
            # Обновляем увеличенный вид, если этот лыжник отображается
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
        """Сброс лыжника"""
        self.running = False
        self.start_time = None
        self.elapsed_time = 0
        self.lap_times = []  # Очищаем список кругов
        self.just_completed_lap = False
        self.time_label.config(text="00:00:00.00")
        self.start_btn.config(state="normal", bg="#4CAF50")
        self.stop_btn.config(state="disabled", bg="#E57373")
        self.lap_btn.config(state="disabled", bg="#FFB74D")
        self.lap_indicator.config(text="Круги: 0")
        
        # Обновляем отображение кругов
        self.app.update_all_laps_display()
        
        # Обновляем увеличенный вид, если этот лыжник отображается
        if self.app.current_large_view == self:
            self.app.show_large_view(self)
    
    def record_lap(self):
        """Запись времени круга"""
        if self.running and self.start_time:
            current_elapsed = self.elapsed_time + (datetime.now() - self.start_time).total_seconds()
            self.lap_times.append(current_elapsed)
            self.last_lap_time = current_elapsed
            self.lap_indicator.config(text=f"Круги: {len(self.lap_times)}")
            
            # Устанавливаем флаг только что завершенного круга
            self.just_completed_lap = True
            self.lap_completion_time = datetime.now()
            
            print(f"{self.get_name()} - Круг {len(self.lap_times)}: {self.format_time(current_elapsed)}")
            
            # Обновляем отображение кругов
            self.app.update_all_laps_display()
            
            # Обновляем увеличенный вид, если этот лыжник отображается
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
    
    def update_display_number(self, new_number):
        """Обновляет только номер лыжника, сохраняя пользовательское имя"""
        self.number = new_number
        
        # Если имя было по умолчанию (например, "Лыжник 1"), обновляем его
        if self.default_name.startswith("Лыжник "):
            try:
                # Проверяем, заканчивается ли имя на число
                import re
                if re.search(r'\d+$', self.default_name):
                    # Обновляем имя по умолчанию с новым номером
                    self.default_name = f"Лыжник {new_number}"
                    self.name_var.set(self.default_name)
                    self.name_label.config(text=self.default_name)
            except:
                # Если что-то пошло не так, просто обновляем имя
                self.default_name = f"Лыжник {new_number}"
                self.name_var.set(self.default_name)
                self.name_label.config(text=self.default_name)
        
        # Если находимся в режиме редактирования, завершаем его
        if self.is_editing_name:
            self.finish_name_editing()
        
        # Обновляем цвет в зависимости от нового номера
        self.color = self.colors[(new_number - 1) % len(self.colors)]
        self.time_label.config(fg=self.color)
        self.lap_indicator.config(fg=self.color)
        
        # Обновляем цвет кнопки "Увеличить"
        for widget in self.frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, tk.Button) and btn.cget("text") == "🔍":
                        btn.config(bg=self.color)
                        break
        
        # Обновляем отображение кругов
        self.app.update_all_laps_display()
    
    def remove(self):
        """Удаление этого лыжника"""
        if self.app:
            self.app.remove_stopwatch(self)
    
    def select_for_large_view(self):
        """Выбор этого лыжника для отображения в увеличенном виде"""
        self.app.show_large_view(self)
    
    def destroy(self):
        """Уничтожение виджета"""
        self.frame.destroy()
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import re
from parsing import SFTPChatMonitor
from command_templates import get_skier_commands, get_all_command_examples, should_ignore_command, extract_command_parts

class ParserIntegration:
    def __init__(self, app):
        """
        Инициализация интеграции парсера с приложением
        
        Args:
            app: Экземпляр StopwatchApp (основного приложения)
        """
        self.app = app
        self.root = app.root
        self.parser = None
        self.parser_thread = None
        self.running = False
        self.message_queue = queue.Queue()
        self.active_commands = {}
        
        # Окно настроек парсера
        self.settings_window = None
        
        # Автоматический режим (автоматически выполняет команды)
        self.auto_mode = True
        
        # Кэш имен лыжников
        self.skier_names_cache = []
        
        # Статистика
        self.commands_processed = 0
        self.commands_ignored = 0
        
        # Создаем UI элементы для управления парсером
        self.create_ui_elements()
        
        # Инициализируем команды
        self.update_skier_commands()

    def execute_command_from_text(self, text):
        """
        Выполняет команду на основе текста сообщения
        
        ОБНОВЛЕНИЕ: Лучшая обработка контекстных команд
        """
        text_lower = text.lower()
        
        # Обновляем команды на случай, если имена изменились
        self.update_skier_commands()
        
        # Проверяем все активные команды
        best_match = None
        best_priority = -1
        
        for command_key, command_data in self.active_commands.items():
            regex = command_data.get('regex', '')
            action = command_data.get('action', '')
            skier_name = command_data.get('skier_name', '')
            extract_number = command_data.get('extract_number', False)
            exact_match = command_data.get('exact_match', False)
            priority = command_data.get('priority', 0)
            
            if regex:
                # Ищем совпадение (учитываем, что могут быть дополнительные слова)
                match = re.search(regex, text_lower, re.IGNORECASE)
                if match:
                    # Проверяем приоритет
                    if priority > best_priority:
                        best_priority = priority
                        best_match = {
                            'action': action,
                            'skier_name': skier_name,
                            'extract_number': extract_number,
                            'match': match,
                            'command_key': command_key,
                            'full_text': text
                        }
        
        # Если нашли совпадение
        if best_match:
            # Проверяем, нужно ли игнорировать команду (ТОЛЬКО критические случаи)
            if best_match['skier_name'] and should_ignore_command(text, best_match['skier_name']):
                self.commands_ignored += 1
                self.log_message(f"[Игнорировано] '{text}' (содержит критические слова)", "ignored")
                self.update_stats_display()
                return
            
            # Извлекаем номер круга, если нужно
            lap_number = None
            if best_match['extract_number']:
                numbers = [g for g in best_match['match'].groups() if g]
                if numbers:
                    lap_number = int(numbers[0])
            
            # Выполняем действие
            self.perform_action(
                best_match['action'], 
                best_match['skier_name'], 
                lap_number, 
                text
            )
            
            self.commands_processed += 1
            self.update_stats_display()
        else:
            # Если не нашли команду по регуляркам, пробуем интеллектуальный парсинг
            self.smart_command_parsing(text)
    
    def smart_command_parsing(self, text):
        """
        Интеллектуальный парсинг команд с учетом контекста
        
        ОБНОВЛЕНИЕ: Разбирает команды даже с дополнительным контекстом
        """
        text_lower = text.lower()
        
        # Ищем имя лыжника в тексте
        found_skiers = []
        for stopwatch in self.app.stopwatches:
            skier_name = stopwatch.get_name().lower()
            
            # Ищем имя как отдельное слово
            pattern = r'\b' + re.escape(skier_name) + r'\b'
            if re.search(pattern, text_lower):
                found_skiers.append((stopwatch, skier_name))
        
        if not found_skiers:
            # Не нашли ни одного лыжника
            self.commands_ignored += 1
            self.log_message(f"[Игнорировано] '{text}' (не найдено имя лыжника)", "ignored")
            self.update_stats_display()
            return
        
        # Для каждого найденного лыжника проверяем команды
        for stopwatch, skier_name in found_skiers:
            # Проверяем критические слова (дисквалификация и т.д.)
            if should_ignore_command(text, skier_name):
                self.commands_ignored += 1
                self.log_message(f"[Игнорировано] '{text}' (содержит критические слова)", "ignored")
                self.update_stats_display()
                continue
            
            # Извлекаем команду и контекст
            command, context = extract_command_parts(text, skier_name)
            
            if not command:
                # Не нашли команду
                continue
            
            # Определяем действие по команде
            if command in ['стартовал', 'старт', 'запуск']:
                if not stopwatch.running:
                    stopwatch.start()
                    self.commands_processed += 1
                    self.log_message(f"[Авто] Запущен: {skier_name} ({context})", "success")
                    self.update_stats_display()
                return
            
            elif command in ['финишировал', 'финиш']:
                if stopwatch.running:
                    stopwatch.stop()
                    self.commands_processed += 1
                    self.log_message(f"[Авто] Остановлен: {skier_name} ({context})", "success")
                    self.update_stats_display()
                return
            
            elif command in ['подошел', 'прошел', 'вышел', 'круг']:
                if stopwatch.running:
                    # Проверяем, есть ли номер круга в контексте
                    lap_number_match = re.search(r'(\d+)', text_lower)
                    lap_number = None
                    if lap_number_match:
                        lap_number = int(lap_number_match.group(1))
                    
                    stopwatch.record_lap()
                    self.commands_processed += 1
                    
                    if lap_number:
                        self.log_message(f"[Авто] Круг {lap_number}: {skier_name} ({context})", "success")
                    else:
                        self.log_message(f"[Авто] Круг: {skier_name} ({context})", "success")
                    self.update_stats_display()
                return
        
        # Проверяем общие команды
        self.parse_general_commands(text)
    
    def parse_general_commands(self, text):
        """Парсит общие команды для всех лыжников"""
        text_lower = text.lower()
        
        # Проверяем команды для всех лыжников
        if re.search(r'^старт\s+всех|^все\s+старт', text_lower):
            self.app.start_all_stopwatches()
            self.commands_processed += 1
            self.log_message("[Авто] Запущены все лыжники", "success")
            self.update_stats_display()
        elif re.search(r'^стоп\s+всех|^все\s+стоп', text_lower):
            self.app.stop_all_stopwatches()
            self.commands_processed += 1
            self.log_message("[Авто] Остановлены все лыжники", "success")
            self.update_stats_display()
        elif re.search(r'^круг\s+всех|^все\s+круг', text_lower):
            lap_count = 0
            for stopwatch in self.app.stopwatches:
                if stopwatch.running:
                    stopwatch.record_lap()
                    lap_count += 1
            if lap_count > 0:
                self.commands_processed += 1
                self.log_message(f"[Авто] Круг для {lap_count} лыжников", "success")
                self.update_stats_display()
        
    def update_skier_commands(self):
        """Обновляет команды на основе текущих имен лыжников"""
        # Получаем актуальные имена лыжников
        current_names = [sw.get_name() for sw in self.app.stopwatches]
        
        # Если имена изменились, обновляем команды
        if current_names != self.skier_names_cache:
            self.skier_names_cache = current_names
            self.active_commands = get_skier_commands(self.app)
            self.log_message(f"[Система] Обновлены команды для {len(current_names)} лыжников")
    
    def create_ui_elements(self):
        """Создает элементы интерфейса для управления парсером"""
        # Добавляем меню в главное окно
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        parser_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Парсер Minecraft", menu=parser_menu)
        
        parser_menu.add_command(
            label="Запустить парсер",
            command=self.start_parser_dialog
        )
        
        parser_menu.add_command(
            label="Остановить парсер",
            command=self.stop_parser,
            state="disabled"
        )
        
        parser_menu.add_separator()
        
        parser_menu.add_command(
            label="Обновить команды",
            command=self.update_skier_commands
        )
        
        parser_menu.add_command(
            label="Показать примеры команд",
            command=self.show_command_examples
        )
        
        parser_menu.add_separator()
        
        parser_menu.add_command(
            label="Статус парсера",
            command=self.show_parser_status
        )
        
        parser_menu.add_command(
            label="Статистика",
            command=self.show_statistics
        )
        
        # Сохраняем ссылки на меню для обновления состояния
        self.parser_menu = parser_menu
        
        # Создаем отдельное окно для управления парсером
        self.create_control_window()
        
        # Запускаем обработчик очереди сообщений
        self.root.after(100, self.process_message_queue)
    
    def create_control_window(self):
        """Создает отдельное окно для управления парсером"""
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Управление парсером Minecraft")
        self.control_window.geometry("500x350")
        
        # Позиционируем окно в правом верхнем углу
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 500
        window_height = 350
        x = screen_width - window_width - 50
        y = 50
        self.control_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Заголовок
        title_label = tk.Label(
            self.control_window,
            text="Управление парсером Minecraft",
            font=("Arial", 12, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Статус
        self.status_label = tk.Label(
            self.control_window,
            text="Статус: НЕ АКТИВЕН",
            font=("Arial", 10),
            fg="#666",
            pady=5
        )
        self.status_label.pack()
        
        # Информация о лыжниках
        self.skiers_label = tk.Label(
            self.control_window,
            text="Лыжники: загрузка...",
            font=("Arial", 9),
            fg="#666",
            pady=2
        )
        self.skiers_label.pack()
        
        # Статистика
        self.stats_label = tk.Label(
            self.control_window,
            text="Команд: 0 обработано, 0 проигнорировано",
            font=("Arial", 8),
            fg="#888",
            pady=2
        )
        self.stats_label.pack()
        
        # Кнопки
        buttons_frame = tk.Frame(self.control_window, pady=10)
        buttons_frame.pack()
        
        self.parser_start_btn = tk.Button(
            buttons_frame,
            text="▶ Запустить парсер",
            command=self.start_parser_dialog,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10),
            width=20
        )
        self.parser_start_btn.pack(pady=5)
        
        self.parser_stop_btn = tk.Button(
            buttons_frame,
            text="■ Остановить парсер",
            command=self.stop_parser,
            bg="#f44336",
            fg="white",
            font=("Arial", 10),
            width=20,
            state="disabled"
        )
        self.parser_stop_btn.pack(pady=5)
        
        # Лог сообщений
        log_frame = tk.Frame(self.control_window)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        tk.Label(log_frame, text="Лог сообщений:", font=("Arial", 9)).pack(anchor="w")
        
        self.log_text = tk.Text(
            log_frame,
            height=8,
            width=55,
            font=("Consolas", 8),
            bg="#f8f8f8",
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.insert("1.0", "Лог сообщений парсера...\n")
        self.log_text.config(state="disabled")
        
        # Кнопки управления логом
        log_buttons_frame = tk.Frame(self.control_window)
        log_buttons_frame.pack(pady=5)
        
        tk.Button(
            log_buttons_frame,
            text="Очистить лог",
            command=self.clear_log,
            font=("Arial", 8),
            width=15
        ).pack(side="left", padx=5)
        
        tk.Button(
            log_buttons_frame,
            text="Показать статистику",
            command=self.show_statistics,
            font=("Arial", 8),
            width=15
        ).pack(side="left", padx=5)
    
    def update_stats_display(self):
        """Обновляет отображение статистики"""
        self.stats_label.config(
            text=f"Команд: {self.commands_processed} обработано, {self.commands_ignored} проигнорировано"
        )
    
    def update_skiers_info(self):
        """Обновляет информацию о лыжниках"""
        names = [sw.get_name() for sw in self.app.stopwatches]
        self.skiers_label.config(text=f"Лыжники: {', '.join(names)}")
    
    def clear_log(self):
        """Очищает лог сообщений"""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", "Лог очищен\n")
        self.log_text.config(state="disabled")
    
    def log_message(self, message, level="info"):
        """Добавляет сообщение в лог"""
        self.log_text.config(state="normal")
        
        # Цвета для разных уровней сообщений
        colors = {
            "info": "black",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#f44336",
            "ignored": "#888888"
        }
        
        color = colors.get(level, "black")
        
        # Вставляем сообщение с тегом для цвета
        self.log_text.insert("end", f"{message}\n", level)
        self.log_text.tag_config(level, foreground=color)
        
        self.log_text.see("end")  # Прокручиваем вниз
        self.log_text.config(state="disabled")
    
    def start_parser_dialog(self):
        """Показывает диалог для запуска парсера"""
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Настройки парсера Minecraft")
        self.settings_window.geometry("500x400")
        self.settings_window.resizable(False, False)
        
        # Делаем окно модальным
        self.settings_window.transient(self.root)
        self.settings_window.grab_set()
        
        # Центрируем окно
        self.center_window(self.settings_window)
        
        # Заголовок
        title_label = tk.Label(
            self.settings_window,
            text="Настройки подключения к серверу Minecraft",
            font=("Arial", 14, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Фрейм для полей ввода
        input_frame = tk.Frame(self.settings_window, padx=20, pady=10)
        input_frame.pack(fill="both", expand=True)
        
        # Поля ввода
        fields = [
            ("Хост сервера (IP/домен):", "host", "d22.joinserver.xyz"),
            ("Порт SSH:", "port", "7477"),
            ("Имя пользователя:", "username", "jgixek78.7343820e"),
            ("Пароль:", "password", "", True),
            ("Путь к файлу логов:", "remote_path", "/logs/latest.log"),
        ]
        
        self.input_vars = {}
        
        for i, (label_text, var_name, default_value, *extra) in enumerate(fields):
            is_password = len(extra) > 0 and extra[0]
            
            label = tk.Label(input_frame, text=label_text, anchor="w")
            label.grid(row=i, column=0, sticky="w", pady=5)
            
            var = tk.StringVar(value=default_value)
            self.input_vars[var_name] = var
            
            if is_password:
                entry = tk.Entry(input_frame, textvariable=var, show="*", width=40)
            else:
                entry = tk.Entry(input_frame, textvariable=var, width=40)
            
            entry.grid(row=i, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Фрейм для кнопок
        button_frame = tk.Frame(self.settings_window, pady=20)
        button_frame.pack()
        
        # Кнопка запуска
        start_btn = tk.Button(
            button_frame,
            text="Запустить парсер",
            command=self.start_parser_from_dialog,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11),
            width=15
        )
        start_btn.pack(side="left", padx=10)
        
        # Кнопка отмены
        cancel_btn = tk.Button(
            button_frame,
            text="Отмена",
            command=self.settings_window.destroy,
            bg="#9E9E9E",
            fg="white",
            font=("Arial", 11),
            width=15
        )
        cancel_btn.pack(side="left", padx=10)
    
    def start_parser_from_dialog(self):
        """Запускает парсер с настройками из диалога"""
        try:
            # Получаем значения из полей ввода
            host = self.input_vars['host'].get().strip()
            port = int(self.input_vars['port'].get().strip())
            username = self.input_vars['username'].get().strip()
            password = self.input_vars['password'].get().strip()
            remote_path = self.input_vars['remote_path'].get().strip()
            
            # Проверяем обязательные поля
            if not all([host, username, remote_path]):
                messagebox.showerror("Ошибка", "Заполните все обязательные поля!")
                return
            
            # Закрываем диалог
            self.settings_window.destroy()
            
            # Запускаем парсер
            self.start_parser(host, port, username, password, remote_path)
            
        except ValueError:
            messagebox.showerror("Ошибка", "Порт должен быть числом!")
    
    def start_parser(self, host, port, username, password, remote_path):
        """Запускает парсер в отдельном потоке"""
        if self.running:
            messagebox.showwarning("Внимание", "Парсер уже запущен!")
            return
        
        try:
            # Создаем экземпляр парсера
            self.parser = SFTPChatMonitor(
                host=host,
                port=port,
                username=username,
                password=password,
                remote_path=remote_path
            )
            
            # Подключаемся к серверу
            if not self.parser.connect():
                messagebox.showerror("Ошибка", "Не удалось подключиться к серверу!")
                return
            
            # Запускаем парсер в отдельном потоке
            self.running = True
            self.parser_thread = threading.Thread(
                target=self.run_parser,
                daemon=True
            )
            self.parser_thread.start()
            
            # Обновляем UI
            self.update_ui_state(True)
            self.update_skiers_info()
            
            self.log_message(f"[✓] Парсер запущен на {host}:{port}")
            messagebox.showinfo("Успех", "Парсер успешно запущен!")
            
        except Exception as e:
            self.log_message(f"[✗] Ошибка запуска парсера: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось запустить парсера: {str(e)}")
    
    def run_parser(self):
        """Основной цикл работы парсера"""
        try:
            while self.running and self.parser and self.parser.connected:
                # Читаем новые данные
                new_data = self.parser.read_new_data()
                
                if new_data:
                    # Обрабатываем сообщения
                    messages = self.parser.process_messages(new_data)
                    
                    for message in messages:
                        # Выводим сообщение в консоль
                        self.parser.print_message(message)
                        
                        # Добавляем сообщение в очередь для обработки
                        self.message_queue.put(message)
                
                # Небольшая пауза
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Ошибка в парсере: {e}")
            self.message_queue.put({"type": "error", "error": str(e)})
        finally:
            self.running = False
            if self.parser:
                self.parser.disconnect()
            self.update_ui_state(False)
    
    def process_message_queue(self):
        """Обрабатывает сообщения из очереди"""
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                
                if message.get('type') == 'error':
                    # Ошибка парсера
                    self.show_parser_error(message.get('error', 'Неизвестная ошибка'))
                elif message.get('type') == 'command_block':
                    # Сообщение от командного блока
                    self.process_command_block_message(message)
                
                self.message_queue.task_done()
                
        except queue.Empty:
            pass
        
        # Планируем следующую проверку
        self.root.after(100, self.process_message_queue)
    
    def process_command_block_message(self, message):
        """Обрабатывает сообщение от командного блока"""
        text = message.get('message', '').strip()
        location = message.get('location', 'unknown')
        timestamp = message.get('timestamp', '')
        
        log_msg = f"[Minecraft] {timestamp} [{location}]: {text}"
        self.log_message(log_msg, "info")
        
        # Если включен автоматический режим, анализируем команду
        if self.auto_mode:
            self.execute_command_from_text(text)
    
    def execute_command_from_text(self, text):
        """
        Выполняет команду на основе текста сообщения
        
        Сначала проверяет, нужно ли игнорировать сообщение,
        затем ищет точные совпадения с командами
        """
        text_lower = text.lower()
        
        # Обновляем команды на случай, если имена изменились
        self.update_skier_commands()
        
        # Проверяем все активные команды
        best_match = None
        best_priority = -1
        
        for command_key, command_data in self.active_commands.items():
            regex = command_data.get('regex', '')
            action = command_data.get('action', '')
            skier_name = command_data.get('skier_name', '')
            extract_number = command_data.get('extract_number', False)
            exact_match = command_data.get('exact_match', True)
            priority = command_data.get('priority', 0)
            
            if regex:
                # Ищем точное совпадение
                match = re.search(regex, text_lower, re.IGNORECASE)
                if match:
                    # Проверяем приоритет (выбираем самый точный матч)
                    if priority > best_priority:
                        best_priority = priority
                        best_match = {
                            'action': action,
                            'skier_name': skier_name,
                            'extract_number': extract_number,
                            'match': match,
                            'command_key': command_key
                        }
        
        # Если нашли совпадение
        if best_match:
            # Проверяем, нужно ли игнорировать команду
            if best_match['skier_name'] and should_ignore_command(text, best_match['skier_name']):
                self.commands_ignored += 1
                self.log_message(f"[Игнорировано] '{text}' (содержит игнорируемые слова)", "ignored")
                self.update_stats_display()
                return
            
            # Извлекаем номер круга, если нужно
            lap_number = None
            if best_match['extract_number']:
                numbers = [g for g in best_match['match'].groups() if g]
                if numbers:
                    lap_number = int(numbers[0])
            
            # Выполняем действие
            self.perform_action(
                best_match['action'], 
                best_match['skier_name'], 
                lap_number, 
                text
            )
            
            self.commands_processed += 1
            self.update_stats_display()
        else:
            # Если не нашли команду, пробуем общий парсинг (с осторожностью)
            self.parse_general_command_with_caution(text)
    
    def parse_general_command_with_caution(self, text):
        """
        Парсит общие команды с дополнительными проверками
        
        Более осторожный подход, чтобы не реагировать на случайные сообщения
        """
        text_lower = text.lower()
        
        # Игнорируем слишком длинные сообщения
        if len(text.split()) > 8:
            self.commands_ignored += 1
            self.log_message(f"[Игнорировано] '{text}' (слишком длинное)", "ignored")
            self.update_stats_display()
            return
        
        # Ищем имена лыжников
        found_skiers = []
        for stopwatch in self.app.stopwatches:
            skier_name = stopwatch.get_name().lower()
            if skier_name in text_lower:
                # Проверяем, что имя стоит отдельно (не часть другого слова)
                pattern = r'\b' + re.escape(skier_name) + r'\b'
                if re.search(pattern, text_lower):
                    found_skiers.append((stopwatch, skier_name))
        
        # Если нашли лыжников, проверяем команды
        for stopwatch, skier_name in found_skiers:
            # Проверяем, нужно ли игнорировать
            if should_ignore_command(text, skier_name):
                self.commands_ignored += 1
                self.log_message(f"[Игнорировано] '{text}' (содержит игнорируемые слова для {skier_name})", "ignored")
                self.update_stats_display()
                continue
            
            # Проверяем ключевые слова для старта (только в начале сообщения)
            start_pattern = r'^' + re.escape(skier_name) + r'\s+(?:старт|стартовал|запуск)\b'
            if re.search(start_pattern, text_lower):
                if not stopwatch.running:
                    stopwatch.start()
                    self.commands_processed += 1
                    self.log_message(f"[Авто] Запущен: {skier_name}", "success")
                    self.update_stats_display()
                return
            
            # Проверяем ключевые слова для остановки
            stop_pattern = r'^' + re.escape(skier_name) + r'\s+(?:стоп|финиш|финишировал)\b'
            if re.search(stop_pattern, text_lower):
                if stopwatch.running:
                    stopwatch.stop()
                    self.commands_processed += 1
                    self.log_message(f"[Авто] Остановлен: {skier_name}", "success")
                    self.update_stats_display()
                return
            
            # Проверяем ключевые слова для круга (только конкретные)
            lap_pattern = r'^' + re.escape(skier_name) + r'\s+(?:подошел|прошел|вышел)\b'
            if re.search(lap_pattern, text_lower):
                if stopwatch.running:
                    stopwatch.record_lap()
                    self.commands_processed += 1
                    self.log_message(f"[Авто] Круг: {skier_name}", "success")
                    self.update_stats_display()
                return
        
        # Проверяем общие команды
        if re.search(r'^старт\s+всех\b|^все\s+старт\b', text_lower):
            self.app.start_all_stopwatches()
            self.commands_processed += 1
            self.log_message("[Авто] Запущены все лыжники", "success")
            self.update_stats_display()
        elif re.search(r'^стоп\s+всех\b|^все\s+стоп\b', text_lower):
            self.app.stop_all_stopwatches()
            self.commands_processed += 1
            self.log_message("[Авто] Остановлены все лыжники", "success")
            self.update_stats_display()
        elif re.search(r'^круг\s+всех\b|^все\s+круг\b', text_lower):
            lap_count = 0
            for stopwatch in self.app.stopwatches:
                if stopwatch.running:
                    stopwatch.record_lap()
                    lap_count += 1
            if lap_count > 0:
                self.commands_processed += 1
                self.log_message(f"[Авто] Круг для {lap_count} лыжников", "success")
                self.update_stats_display()
    
    def perform_action(self, action, skier_name, lap_number, original_text):
        """
        Выполняет конкретное действие
        
        Args:
            action: Тип действия (start_skier, stop_skier, lap_skier и т.д.)
            skier_name: Имя лыжника (может быть пустым для общих команд)
            lap_number: Номер круга (если указан)
            original_text: Оригинальный текст команды
        """
        # Находим лыжника по имени
        skier = None
        if skier_name:
            skier = self.find_skier_by_name(skier_name)
        
        if action == 'start_skier':
            if skier and not skier.running:
                skier.start()
                self.log_message(f"[Авто] Запущен: {skier_name}", "success")
        
        elif action == 'stop_skier':
            if skier and skier.running:
                skier.record_lap()
                skier.stop()
                self.log_message(f"[Авто] Остановлен: {skier_name}", "success")
        
        elif action == 'lap_skier':
            if skier and skier.running:
                skier.record_lap()
                if lap_number:
                    self.log_message(f"[Авто] Круг {lap_number}: {skier_name}", "success")
                else:
                    self.log_message(f"[Авто] Круг: {skier_name}", "success")
        
        elif action == 'lap_skier_with_number':
            if skier and skier.running:
                skier.record_lap()
                self.log_message(f"[Авто] Круг {lap_number}: {skier_name}", "success")
        
        elif action == 'select_skier':
            if skier:
                self.app.show_large_view(skier)
                self.log_message(f"[Авто] Выбран: {skier_name}", "success")
        
        elif action == 'start_all':
            self.app.start_all_stopwatches()
            self.log_message("[Авто] Запущены все лыжники", "success")
        
        elif action == 'stop_all':
            self.app.stop_all_stopwatches()
            self.log_message("[Авто] Остановлены все лыжники", "success")
        
        elif action == 'lap_all':
            lap_count = 0
            for stopwatch in self.app.stopwatches:
                if stopwatch.running:
                    stopwatch.record_lap()
                    lap_count += 1
            if lap_count > 0:
                self.log_message(f"[Авто] Круг для {lap_count} лыжников", "success")
        
        elif action == 'reset_all':
            self.app.reset_all_stopwatches()
            self.log_message("[Авто] Сброшены все лыжники", "success")
    
    def find_skier_by_name(self, name):
        """Находит лыжника по имени"""
        for stopwatch in self.app.stopwatches:
            if stopwatch.get_name().lower() == name.lower():
                return stopwatch
        return None
    
    def show_statistics(self):
        """Показывает статистику работы парсера"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Статистика парсера")
        stats_window.geometry("400x300")
        
        # Делаем окно модальным
        stats_window.transient(self.root)
        stats_window.grab_set()
        
        title_label = tk.Label(
            stats_window,
            text="Статистика работы парсера",
            font=("Arial", 14, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Статистика
        stats_text = f"""
        Обработано команд: {self.commands_processed}
        Проигнорировано: {self.commands_ignored}
        Всего сообщений: {self.commands_processed + self.commands_ignored}
        
        Точность распознавания: {self.calculate_accuracy():.1f}%
        
        Активных лыжников: {sum(1 for sw in self.app.stopwatches if sw.running)}
        Всего лыжников: {len(self.app.stopwatches)}
        
        Состояние парсера: {'АКТИВЕН' if self.running else 'НЕ АКТИВЕН'}
        """
        
        stats_label = tk.Label(
            stats_window,
            text=stats_text,
            font=("Arial", 10),
            justify="left",
            padx=20,
            pady=10
        )
        stats_label.pack()
        
        # Кнопка сброса статистики
        tk.Button(
            stats_window,
            text="Сбросить статистику",
            command=self.reset_statistics,
            bg="#FF9800",
            fg="white",
            width=15
        ).pack(side="left", padx=20, pady=10)
        
        # Кнопка закрытия
        tk.Button(
            stats_window,
            text="Закрыть",
            command=stats_window.destroy,
            bg="#2196F3",
            fg="white",
            width=15
        ).pack(side="right", padx=20, pady=10)
        
        self.center_window(stats_window)
    
    def calculate_accuracy(self):
        """Рассчитывает точность распознавания"""
        total = self.commands_processed + self.commands_ignored
        if total > 0:
            return (self.commands_processed / total) * 100
        return 100.0
    
    def reset_statistics(self):
        """Сбрасывает статистику"""
        self.commands_processed = 0
        self.commands_ignored = 0
        self.update_stats_display()
        self.log_message("[Система] Статистика сброшена", "info")
    
    def show_command_examples(self):
        """Показывает примеры команд"""
        examples_window = tk.Toplevel(self.root)
        examples_window.title("Примеры команд для парсера")
        examples_window.geometry("650x450")
        
        # Делаем окно модальным
        examples_window.transient(self.root)
        examples_window.grab_set()
        
        # Заголовок
        title_label = tk.Label(
            examples_window,
            text="Примеры команд для управления лыжниками",
            font=("Arial", 14, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Создаем Notebook (вкладки)
        notebook = ttk.Notebook(examples_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Вкладка 1: Рабочие команды
        working_frame = tk.Frame(notebook)
        notebook.add(working_frame, text="Рабочие команды")
        
        working_text = tk.Text(
            working_frame,
            font=("Courier New", 10),
            wrap="word",
            padx=10,
            pady=10
        )
        working_text.pack(fill="both", expand=True)
        
        working_examples = """
=== КОМАНДЫ ДЛЯ КОНКРЕТНЫХ ЛЫЖНИКОВ ===
Slend37 стартовал      - запуск Slend37
Slend37 финишировал    - остановка Slend37
Slend37 подошел        - фиксация круга
Slend37 прошел 1       - круг номер 1
старт Slend37          - альтернативный формат
финиш Slend37          - альтернативный формат
круг Slend37           - альтернативный формат

=== КОМАНДЫ ДЛЯ ВСЕХ ЛЫЖНИКОВ ===
старт всех             - запуск всех
стоп всех              - остановка всех
круг всех              - круг для всех активных
сброс всех             - сброс всех

=== ВАЖНО ===
• Команды работают независимо от регистра
• Имя лыжника должно точно совпадать
• После команды не должно быть других слов
"""
        working_text.insert("1.0", working_examples)
        working_text.config(state="disabled")
        
        # Вкладка 2: Игнорируемые фразы
        ignore_frame = tk.Frame(notebook)
        notebook.add(ignore_frame, text="Игнорируемые фразы")
        
        ignore_text = tk.Text(
            ignore_frame,
            font=("Courier New", 10),
            wrap="word",
            padx=10,
            pady=10
        )
        ignore_text.pack(fill="both", expand=True)
        
        ignore_examples = """
=== ФРАЗЫ, КОТОРЫЕ НЕ РАБОТАЮТ ===
Slend37 зашел на штрафной круг
Slend37 упал на повороте
Slend37 сбил стойку
Slend37 оступился и упал
Slend37 дисквалифицирован
Slend37 снят с дистанции

=== ПРИЧИНЫ ИГНОРИРОВАНИЯ ===
1. Содержат слова: "зашел", "упал", "сбил", "оступился"
2. Слишком длинные (более 4 слов)
3. Содержат контекстные слова: "штрафной", "наказание"
4. Не являются точными командами управления

=== КАК ИСПРАВИТЬ ===
Используйте только команды из вкладки "Рабочие команды"
Сообщения должны быть короткими и точными
"""
        ignore_text.insert("1.0", ignore_examples)
        ignore_text.config(state="disabled")
        
        # Вкладка 3: Настройка
        setup_frame = tk.Frame(notebook)
        notebook.add(setup_frame, text="Настройка")
        
        setup_text = tk.Text(
            setup_frame,
            font=("Courier New", 10),
            wrap="word",
            padx=10,
            pady=10
        )
        setup_text.pack(fill="both", expand=True)
        
        setup_info = """
=== КАК НАСТРОИТЬ СИСТЕМУ ===

1. ИЗМЕНИТЬ ИМЕНА ЛЫЖНИКОВ:
   • Дважды кликните на имя лыжника в основном окне
   • Введите новое имя
   • Нажмите Enter или кнопку "✓"

2. ОБНОВИТЬ КОМАНДЫ:
   • В меню выберите "Парсер Minecraft → Обновить команды"
   • Система автоматически создаст команды для новых имен

3. ИЗМЕНИТЬ ФИЛЬТРЫ:
   • Откройте файл command_templates.py
   • Измените список IGNORE_WORDS
   • Добавьте слова, которые нужно игнорировать

4. ДОБАВИТЬ НОВЫЕ КОМАНДЫ:
   • Откройте файл command_templates.py
   • Добавьте новые шаблоны в create_skier_command_patterns()
   • Укажите регулярные выражения для новых команд

=== СОВЕТЫ ===
• Используйте \b в регулярных выражениях для точных совпадений
• Команды должны начинаться с имени лыжника или действия
• Избегайте двусмысленных фраз
"""
        setup_text.insert("1.0", setup_info)
        setup_text.config(state="disabled")
        
        # Кнопка закрытия
        tk.Button(
            examples_window,
            text="Закрыть",
            command=examples_window.destroy,
            bg="#2196F3",
            fg="white",
            width=15
        ).pack(pady=10)
        
        self.center_window(examples_window)
    
    def show_parser_status(self):
        """Показывает статус парсера"""
        status_window = tk.Toplevel(self.root)
        status_window.title("Статус парсера Minecraft")
        status_window.geometry("400x300")
        
        # Делаем окно модальным
        status_window.transient(self.root)
        status_window.grab_set()
        
        title_label = tk.Label(
            status_window,
            text="Статус парсера командных блоков",
            font=("Arial", 14, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Статус
        skier_names = [sw.get_name() for sw in self.app.stopwatches]
        status_text = f"""
        Состояние: {'АКТИВЕН' if self.running else 'НЕ АКТИВЕН'}
        
        Автоматический режим: {'ВКЛЮЧЕН' if self.auto_mode else 'ВЫКЛЮЧЕН'}
        
        Лыжники: {', '.join(skier_names)}
        
        Парсер ожидает сообщения от командных блоков...
        
        Формат сообщений:
        [@] текст_команды
        
        Пример: [@] Slend37 стартовал
        """
        
        status_label = tk.Label(
            status_window,
            text=status_text,
            font=("Arial", 10),
            justify="left",
            padx=20,
            pady=10
        )
        status_label.pack()
        
        # Кнопка закрытия
        tk.Button(
            status_window,
            text="Закрыть",
            command=status_window.destroy,
            bg="#2196F3",
            fg="white",
            width=15
        ).pack(pady=20)
        
        self.center_window(status_window)
    
    def stop_parser(self):
        """Останавливает парсер"""
        if self.running and self.parser:
            self.running = False
            if self.parser_thread:
                self.parser_thread.join(timeout=2)
            
            self.update_ui_state(False)
            self.log_message("[✗] Парсер остановлен")
            messagebox.showinfo("Информация", "Парсер остановлен")
    
    def update_ui_state(self, running):
        """Обновляет состояние UI элементов"""
        state = "disabled" if running else "normal"
        inverse_state = "normal" if running else "disabled"
        
        # Обновляем меню
        self.parser_menu.entryconfig("Запустить парсер", state=state)
        self.parser_menu.entryconfig("Остановить парсер", state=inverse_state)
        
        # Обновляем кнопки
        self.parser_start_btn.config(state=state)
        self.parser_stop_btn.config(state=inverse_state)
        
        # Обновляем статус
        if running:
            self.status_label.config(text="Статус: АКТИВЕН", fg="#4CAF50")
        else:
            self.status_label.config(text="Статус: НЕ АКТИВЕН", fg="#666")
    
    def show_parser_error(self, error_message):
        """Показывает ошибку парсера"""
        self.log_message(f"[✗] Ошибка парсера: {error_message}")
        messagebox.showerror("Ошибка парсера", f"Парсер столкнулся с ошибкой:\n\n{error_message}")
        self.running = False
        self.update_ui_state(False)
    
    def center_window(self, window):
        """Центрирует окно на экране"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
# [file name]: parsing.py (обновленная версия)
import os
import sys
import time
import re
import threading
from datetime import datetime
import paramiko
import hashlib

class SFTPChatMonitor:
    """
    Полный мониторинг чата Minecraft через SFTP
    Только для командных блоков
    """
    
    def __init__(self, host, username, password, remote_path, port=22):
        """
        Инициализация SFTP монитора
        
        Args:
            host: SSH сервер (IP или домен)
            username: Имя пользователя SSH
            password: Пароль SSH
            remote_path: Полный путь к файлу latest.log на сервере
            port: Порт SSH (по умолчанию 22)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_path = remote_path
        
        # SSH/SFTP соединение
        self.ssh_client = None
        self.sftp_client = None
        self.connected = False
        
        # Мониторинг
        self.last_position = 0
        self.last_size = 0
        self.running = False
        self.message_count = 0
        
        # Статистика
        self.stats = {
            'locations': {},  # Для разных местоположений командных блоков
            'total_messages': 0,
            'start_time': None,
            'last_message_time': None
        }
        
        # История сообщений
        self.chat_history = []
        self.max_history = 1000
        
        # Паттерны для парсинга (командные блоки)
        self.patterns = [
            # Формат: [HH:MM:SS] [Server thread/INFO]: [@] сообщение
            # Пример: [03:18:20] [Server thread/INFO]: [@] Прошел кт
            r'\[(\d{2}:\d{2}:\d{2})\]\s+\[[^\]]+\]:\s*\[\s*@\s*\]\s*(.+)',
            
            # Формат с координатами: [HH:MM:SS] [Server thread/INFO]: [@ X Y Z] сообщение
            r'\[(\d{2}:\d{2}:\d{2})\]\s+\[[^\]]+\]:\s*\[\s*@\s+[^\]]+\]\s*(.+)',
            
            # Альтернативный формат: [HH:MM:SS INFO]: [@] сообщение
            r'\[(\d{2}:\d{2}:\d{2})\][^\]]*INFO[^\]]*]:\s*\[\s*@\s*\]\s*(.+)',
            
            # Формат Paper: [HH:MM:SS INFO]: [@] сообщение
            r'\[(\d{2}:\d{2}:\d{2})\s+INFO\]:\s*\[\s*@\s*\]\s*(.+)',
        ]
        
        print(f"[SFTP Monitor] Инициализация подключения к {host}:{port}")
    
    def connect(self):
        """Устанавливает соединение с SSH/SFTP сервером"""
        try:
            print(f"[SFTP Monitor] Подключение к SSH {self.host}:{self.port}...")
            
            # Создаем SSH клиент
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Подключаемся с таймаутом
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30,
                banner_timeout=30,
                auth_timeout=30
            )
            
            # Создаем SFTP клиент
            self.sftp_client = self.ssh_client.open_sftp()
            
            # Проверяем доступ к файлу
            try:
                file_stat = self.sftp_client.stat(self.remote_path)
                self.last_size = file_stat.st_size
                self.last_position = max(0, self.last_size - 5000)  # Начинаем с последних 5KB
                print(f"[SFTP Monitor] Файл найден. Размер: {self.last_size} байт")
            except IOError:
                print(f"[SFTP Monitor] Файл не найден: {self.remote_path}")
                return False
            
            self.connected = True
            print("[SFTP Monitor] SSH/SFTP подключение установлено")
            return True
            
        except paramiko.AuthenticationException:
            print("[SFTP Monitor] Ошибка аутентификации: неверный логин или пароль")
            return False
        except paramiko.SSHException as e:
            print(f"[SFTP Monitor] Ошибка SSH: {e}")
            return False
        except Exception as e:
            print(f"[SFTP Monitor] Ошибка подключения: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Закрывает SSH/SFTP соединение"""
        if self.sftp_client:
            try:
                self.sftp_client.close()
            except:
                pass
            self.sftp_client = None
        
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
            self.ssh_client = None
        
        self.connected = False
        print("[SFTP Monitor] SSH/SFTP соединение закрыто")
    
    def reconnect(self):
        """Переподключается к SSH/SFTP серверу"""
        self.disconnect()
        time.sleep(5)  # Ждем перед повторной попыткой
        
        for attempt in range(3):  # 3 попытки
            print(f"[SFTP Monitor] Попытка переподключения {attempt + 1}/3...")
            if self.connect():
                return True
            time.sleep(5)
        
        print("[SFTP Monitor] Не удалось переподключиться")
        return False
    
    def read_new_data(self):
        """Читает новые данные из лог-файла через SFTP"""
        if not self.connected or not self.sftp_client:
            return None
        
        try:
            # Проверяем текущий размер файла
            file_stat = self.sftp_client.stat(self.remote_path)
            current_size = file_stat.st_size
            
            # Если файл был перезаписан (например, log rotation)
            if current_size < self.last_position:
                print("[SFTP Monitor] Обнаружена перезапись файла (новый день?)")
                self.last_position = 0
            
            # Если есть новые данные
            if current_size > self.last_position:
                # Вычисляем сколько данных нужно прочитать
                bytes_to_read = current_size - self.last_position
                
                # Ограничиваем максимальный размер за один раз (100KB)
                if bytes_to_read > 100 * 1024:
                    print(f"[SFTP Monitor] Большой объем данных ({bytes_to_read} байт), читаю первые 100KB")
                    bytes_to_read = 100 * 1024
                    self.last_position = current_size - bytes_to_read
                
                # Открываем файл для чтения
                with self.sftp_client.open(self.remote_path, 'rb') as f:
                    # Переходим на последнюю позицию
                    f.seek(self.last_position)
                    
                    # Читаем новые данные
                    new_data = f.read(bytes_to_read)
                    
                    # Обновляем позицию
                    self.last_position += len(new_data)
                    
                    if new_data:
                        # Декодируем данные
                        try:
                            decoded_data = new_data.decode('utf-8', errors='ignore')
                        except:
                            # Пробуем другие кодировки
                            try:
                                decoded_data = new_data.decode('cp1251', errors='ignore')
                            except:
                                decoded_data = new_data.decode('latin-1', errors='ignore')
                        
                        return decoded_data
            
            return None
            
        except Exception as e:
            print(f"[SFTP Monitor] Ошибка при чтении данных: {e}")
            self.connected = False
            return None
    
    def parse_command_block_message(self, line):
        """Парсит строку лога и извлекает сообщение от командного блока"""
        line = line.strip()
        if not line:
            return None
        
        # Проверяем, содержит ли строка маркер командного блока [@]
        if not ('[@' in line or '[ @' in line):
            return None
        
        # Пробуем все паттерны для командных блоков
        for pattern in self.patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                
                if len(groups) >= 2:
                    timestamp = groups[0]
                    message = groups[1].strip()
                    
                    # Определяем местоположение (если есть координаты)
                    location = "unknown"
                    coord_match = re.search(r'\[\s*@\s+([-\d]+)\s+([-\d]+)\s+([-\d]+)\s*\]', line)
                    if coord_match:
                        x, y, z = coord_match.groups()
                        location = f"X{x}Y{y}Z{z}"
                    else:
                        location = "global"
                    
                    return {
                        'type': 'command_block',
                        'timestamp': timestamp,
                        'location': location,
                        'message': message,
                        'raw': line
                    }
        
        # Если не нашли по паттернам, пробуем вручную
        # Ищем время
        time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
        if not time_match:
            return None
        
        timestamp = time_match.group(1)
        
        # Ищем сообщение после [@]
        at_pos = line.find('[@')
        if at_pos == -1:
            at_pos = line.find('[ @')
        
        if at_pos == -1:
            return None
        
        # Находим конец маркера командного блока
        end_pos = line.find(']', at_pos)
        if end_pos == -1:
            return None
        
        # Сообщение начинается после закрывающей скобки
        message = line[end_pos + 1:].strip()
        if not message:
            return None
        
        # Определяем местоположение
        location = "unknown"
        if line[at_pos:end_pos + 1].strip() == '[@]':
            location = "global"
        else:
            # Пробуем извлечь координаты
            coord_match = re.search(r'([-\d]+)\s+([-\d]+)\s+([-\d]+)', line[at_pos:end_pos + 1])
            if coord_match:
                x, y, z = coord_match.groups()
                location = f"X{x}Y{y}Z{z}"
        
        return {
            'type': 'command_block',
            'timestamp': timestamp,
            'location': location,
            'message': message,
            'raw': line
        }
    
    def process_messages(self, data):
        """Обрабатывает данные и извлекает сообщения только от командных блоков"""
        if not data:
            return []
        
        messages = []
        lines = data.split('\n')
        
        for line in lines:
            # Игнорируем пустые строки
            if not line.strip():
                continue
            
            # Проверяем, является ли строка сообщением от командного блока
            if '[@' in line or '[ @' in line:
                message = self.parse_command_block_message(line)
                if message:
                    messages.append(message)
        
        return messages
    
    def update_stats(self, message):
        """Обновляет статистику"""
        location = message['location']
        
        # Общая статистика
        self.stats['total_messages'] += 1
        self.stats['last_message_time'] = datetime.now()
        
        # Статистика по местоположениям
        if location not in self.stats['locations']:
            self.stats['locations'][location] = {
                'message_count': 0,
                'first_seen': datetime.now(),
                'last_seen': datetime.now(),
                'messages': []
            }
        
        self.stats['locations'][location]['message_count'] += 1
        self.stats['locations'][location]['last_seen'] = datetime.now()
        
        # Сохраняем последние 10 сообщений для каждой локации
        self.stats['locations'][location]['messages'].append({
            'timestamp': message['timestamp'],
            'message': message['message']
        })
        if len(self.stats['locations'][location]['messages']) > 10:
            self.stats['locations'][location]['messages'] = \
                self.stats['locations'][location]['messages'][-10:]
    
    def save_to_history(self, message):
        """Сохраняет сообщение в историю"""
        self.chat_history.append({
            'timestamp': message['timestamp'],
            'location': message['location'],
            'message': message['message'],
            'type': 'command_block',
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Ограничиваем размер истории
        if len(self.chat_history) > self.max_history:
            self.chat_history = self.chat_history[-self.max_history:]
    
    def print_message(self, message):
        """Красиво выводит сообщение от командного блока"""
        timestamp = message['timestamp']
        location = message['location']
        text = message['message']
        
        # Специальный цвет для командных блоков (фиолетовый/пурпурный)
        color_code = 35  # ANSI код для пурпурного цвета
        
        # Форматированный вывод с маркером командного блока
        if location == "global":
            print(f"\033[1;{color_code}m[{timestamp}]\033[0m \033[1;35m[@]\033[0m {text}")
        else:
            print(f"\033[1;{color_code}m[{timestamp}]\033[0m \033[1;35m[{location}]\033[0m {text}")
        
        # Также сохраняем в лог файл
        self.log_to_file(f"[{timestamp}] [{location}] {text}")
    
    def log_to_file(self, text):
        """Сохраняет сообщения в локальный файл"""
        try:
            log_filename = f"command_blocks_history_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(log_filename, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")
        except:
            pass
    
    def monitor(self, interval=0.1):
        """
        Основной цикл мониторинга
        
        Args:
            interval: Интервал проверки в секундах
        """
        print("[SFTP Monitor] Запуск мониторинга командных блоков...")
        
        self.stats['start_time'] = datetime.now()
        self.running = True
        
        try:
            while self.running:
                if not self.connected:
                    if not self.reconnect():
                        print("[SFTP Monitor] Не удалось восстановить соединение, завершение...")
                        break
                
                # Читаем новые данные
                new_data = self.read_new_data()
                
                if new_data:
                    # Обрабатываем сообщения только от командных блоков
                    messages = self.process_messages(new_data)
                    
                    # Выводим новые сообщения
                    for message in messages:
                        self.message_count += 1
                        self.update_stats(message)
                        self.save_to_history(message)
                        self.print_message(message)
                
                # Пауза между проверками
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n[SFTP Monitor] Получен сигнал остановки...")
        except Exception as e:
            print(f"\n[SFTP Monitor] Критическая ошибка: {e}")
        finally:
            self.running = False
            self.disconnect()
            
            print(f"[SFTP Monitor] Мониторинг завершен. Обработано команд: {self.message_count}")
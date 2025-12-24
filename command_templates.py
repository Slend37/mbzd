"""
ШАБЛОН КОМАНД ДЛЯ УПРАВЛЕНИЯ СЕКУНДОМЕРАМИ ИЗ MINECRAFT

Настройте эти регулярные выражения под свои нужды.
Команды ищутся в сообщениях командных блоков формата [@] сообщение

ОБНОВЛЕНИЕ: Теперь команды могут содержать дополнительные слова после ключевых слов
"""

import re

def create_skier_command_patterns():
    """
    Создает динамические шаблоны команд для имен лыжников
    
    ОБНОВЛЕНИЕ: Паттерны разрешают дополнительные слова после ключевых команд
    """
    templates = {
        # КОМАНДЫ ЗАПУСКА - разрешаем дополнительные слова после команды
        'start_skier': {
            'template': r'^{skier_name}\s+стартовал(?:\s+.+)?$|^{skier_name}\s+старт(?:\s+.+)?$|^старт\s+{skier_name}(?:\s+.+)?$|^запуск\s+{skier_name}(?:\s+.+)?$',
            'description': 'Запуск конкретного лыжника',
            'action': 'start_skier',
            'exact_match': False  # Разрешаем дополнительные слова
        },
        
        # КОМАНДЫ ОСТАНОВКИ - разрешаем дополнительные слова после команды
        'stop_skier': {
            'template': r'^{skier_name}\s+финишировал(?:\s+.+)?$|^{skier_name}\s+финиш(?:\s+.+)?$|^финиш\s+{skier_name}(?:\s+.+)?$',
            'description': 'Остановка конкретного лыжника',
            'action': 'stop_skier',
            'exact_match': False
        },
        
        # КОМАНДЫ ФИКСАЦИИ КРУГА - разрешаем дополнительные слова после команды
        'lap_skier': {
            'template': r'^{skier_name}\s+подошел(?:\s+.+)?$|^{skier_name}\s+прошел\s +1(?:\s+.+)?$|^{skier_name}\s+прошел\s +2(?:\s+.+)?$|^{skier_name}\s+вышел\s +с\s +огневого(?:\s+.+)?$|^круг\s+{skier_name}(?:\s+.+)?$',
            'description': 'Фиксация круга у конкретного лыжника',
            'action': 'lap_skier',
            'exact_match': False
        },
        
        # КОМАНДЫ ВЫБОРА ДЛЯ УВЕЛИЧЕННОГО ВИДА
        'select_skier': {
            'template': r'^смотреть\s+{skier_name}(?:\s+.+)?$|^показать\s+{skier_name}(?:\s+.+)?$|^выбрать\s+{skier_name}(?:\s+.+)?$',
            'description': 'Выбор лыжника для увеличенного вида',
            'action': 'select_skier',
            'exact_match': False
        }
    }
    
    return templates

# БАЗОВЫЕ КОМАНДЫ (без указания имени) - разрешаем дополнительные слова
BASE_COMMANDS = {
    'start_all': {
        'regex': r'^старт\s+всех(?:\s+.+)?$|^все\s+старт(?:\s+.+)?$|^общий\s+старт(?:\s+.+)?$|^поехали\s+все(?:\s+.+)?$',
        'description': 'Запуск всех лыжников',
        'action': 'start_all',
        'exact_match': False
    },
    
    'stop_all': {
        'regex': r'^стоп\s+всех(?:\s+.+)?$|^все\s+стоп(?:\s+.+)?$|^общий\s+стоп(?:\s+.+)?$|^финиш\s+всех(?:\s+.+)?$',
        'description': 'Остановка всех лыжников',
        'action': 'stop_all',
        'exact_match': False
    },
    
    'lap_all': {
        'regex': r'^круг\s+всех(?:\s+.+)?$|^все\s+круг(?:\s+.+)?$|^общий\s+круг(?:\s+.+)?$',
        'description': 'Фиксация круга у всех активных',
        'action': 'lap_all',
        'exact_match': False
    },
    
    'reset_all': {
        'regex': r'^сброс\s+всех(?:\s+.+)?$|^все\s+сброс(?:\s+.+)?$|^общий\s+сброс(?:\s+.+)?$',
        'description': 'Сброс всех лыжников',
        'action': 'reset_all',
        'exact_match': False
    }
}

# СПЕЦИАЛЬНЫЕ ФИЛЬТРЫ - слова, которые ОТМЕНЯЮТ обработку команды
# ОБНОВЛЕНИЕ: Только слова, которые НИКОГДА не должны быть командами
IGNORE_WORDS = {
    'дисквалифицирован': [],  # Полностью игнорировать
    'снят': ['с', 'дистанции'],  # Игнорировать только в контексте
    'нарушил': ['правила'],  # Игнорировать только в контексте
}

def should_ignore_command(text, skier_name):
    """
    Проверяет, нужно ли игнорировать команду
    
    ВАЖНОЕ ИЗМЕНЕНИЕ: Теперь игнорируем ТОЛЬКО сообщения, которые 
    определенно НЕ являются командами (дисквалификация, нарушения и т.д.)
    """
    text_lower = text.lower()
    skier_name_lower = skier_name.lower()
    
    # Убираем имя лыжника из текста для анализа
    text_without_name = text_lower.replace(skier_name_lower, '').strip()
    
    # Проверяем ТОЛЬКО критические слова, которые никогда не должны быть командами
    for ignore_word, context_words in IGNORE_WORDS.items():
        if ignore_word in text_without_name:
            # Если есть контекстные слова, проверяем их
            if context_words:
                for context_word in context_words:
                    if context_word in text_without_name:
                        return True
            else:
                return True
    
    # НЕ игнорируем сообщения с "зашел", "упал", "сбил" и т.д.
    # если они содержат ключевые слова команд
    
    return False

def extract_command_parts(text, skier_name):
    """
    Извлекает ключевые части команды из текста
    
    Возвращает кортеж: (команда, контекст)
    Пример: ("подошел", "к огневому рубежу")
    """
    text_lower = text.lower()
    skier_name_lower = skier_name.lower()
    
    # Убираем имя лыжника
    text_without_name = text_lower.replace(skier_name_lower, '').strip()
    
    # Определяем ключевые слова команд
    command_keywords = [
        'стартовал', 'старт', 'запуск',
        'финишировал', 'финиш',
        'подошел', 'прошел 1 кт', 'прошел 2 кт', 'вышел с огневого рубежа'
    ]
    
    # Ищем ключевое слово
    for keyword in command_keywords:
        if keyword in text_without_name:
            # Разделяем на команду и контекст
            parts = text_without_name.split(keyword, 1)
            command = keyword.strip()
            context = parts[1].strip() if len(parts) > 1 and parts[1] else ""
            
            return command, context
    
    return None, ""

def get_skier_commands(app_instance=None):
    """
    Генерирует команды для текущих имен лыжников
    """
    # Получаем имена лыжников из приложения
    skier_names = []
    if app_instance and hasattr(app_instance, 'stopwatches'):
        skier_names = [sw.get_name() for sw in app_instance.stopwatches]
    else:
        skier_names = ['Slend37', 'Ivanov', 'Petrov', 'Sidorov']
    
    # Создаем шаблоны
    templates = create_skier_command_patterns()
    all_commands = BASE_COMMANDS.copy()
    
    # Для каждого лыжника создаем команды
    for skier_name in skier_names:
        escaped_name = re.escape(skier_name)
        
        for cmd_key, cmd_template in templates.items():
            regex = cmd_template['template'].format(skier_name=escaped_name)
            command_key = f"{cmd_key}_{skier_name}"
            
            all_commands[command_key] = {
                'regex': regex,
                'description': f"{cmd_template['description']}: {skier_name}",
                'action': cmd_template['action'],
                'skier_name': skier_name,
                'extract_number': cmd_template.get('extract_number', False),
                'exact_match': cmd_template.get('exact_match', False),
                'priority': 1
            }
    
    return all_commands

# ПРИМЕРЫ КОМАНД, КОТОРЫЕ РАБОТАЮТ (с контекстом):
"""
Slend37 стартовал на дистанции          ✓ (запуск)
Slend37 финишировал первым              ✓ (остановка)
Slend37 подошел к огневому рубежу       ✓ (круг)
Slend37 вышел с огневого рубежа         ✓ (круг)
Slend37 прошел 1 круг                   ✓ (круг 1)
старт Slend37 сейчас                    ✓ (запуск)
финиш Slend37 успешно                   ✓ (остановка)
"""

# ПРИМЕРЫ, КОТОРЫЕ НЕ РАБОТАЮТ (игнорируются):
"""
Slend37 дисквалифицирован за фальстарт  ✗ (дисквалификация)
Slend37 снят с дистанции                ✗ (снятие)
Slend37 нарушил правила                 ✗ (нарушение)
"""

def get_all_command_examples():
    """Возвращает примеры всех команд"""
    examples = []
    
    examples.append("=== КОМАНДЫ ДЛЯ КОНКРЕТНЫХ ЛЫЖНИКОВ (РАБОТАЮТ С КОНТЕКСТОМ) ===")
    examples.append("Запуск:         'Slend37 стартовал' или 'Slend37 стартовал на дистанции'")
    examples.append("Остановка:      'Slend37 финишировал' или 'Slend37 финишировал первым'")
    examples.append("Круг:           'Slend37 подошел' или 'Slend37 подошел к огневому рубежу'")
    examples.append("Круг:           'Slend37 вышел' или 'Slend37 вышел с огневого рубежа'")
    examples.append("Круг с номером: 'Slend37 прошел 1' или 'Slend37 прошел 1 круг'")
    
    examples.append("\n=== КОМАНДЫ ДЛЯ ВСЕХ ЛЫЖНИКОВ ===")
    examples.append("Запуск всех:    'старт всех' или 'все старт сейчас'")
    examples.append("Остановка всех: 'стоп всех' или 'все стоп на финише'")
    examples.append("Круг всех:      'круг всех' или 'все круг завершили'")
    examples.append("Сброс всех:     'сброс всех' или 'все сброс результатов'")
    
    examples.append("\n=== ФРАЗЫ, КОТОРЫЕ ИГНОРИРУЮТСЯ ===")
    examples.append("'Slend37 дисквалифицирован'")
    examples.append("'Slend37 снят с дистанции'")
    examples.append("'Slend37 нарушил правила'")
    
    return "\n".join(examples)
def format_time(seconds):
    """
    Форматирует время в секундах в строку формата ЧЧ:ММ:СС.сс или ММ:СС.сс
    
    Args:
        seconds: Время в секундах (может быть float)
        
    Returns:
        str: Отформатированная строка времени
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds - int(seconds)) * 100)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}.{centisecs:02d}"

def get_stopwatch_color(number, color_palette=None):
    """
    Возвращает цвет для секундомера на основе его номера
    
    Args:
        number: Номер секундомера (начинается с 1)
        color_palette: Пользовательская палитра цветов (опционально)
        
    Returns:
        str: HEX-код цвета
    """
    if color_palette is None:
        color_palette = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", 
                         "#FF5722", "#009688", "#795548", "#607D8B"]
    
    return color_palette[(number - 1) % len(color_palette)]

def validate_time_input(time_str):
    """
    Проверяет, является ли строка корректным временем
    
    Args:
        time_str: Строка времени
        
    Returns:
        bool: True если строка корректна, False в противном случае
    """
    # Простая проверка формата времени
    import re
    pattern = r'^(\d{1,2}:)?\d{1,2}:\d{2}\.\d{2}$'
    return bool(re.match(pattern, time_str))
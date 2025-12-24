import tkinter as tk
from app import StopwatchApp
from integration import ParserIntegration  # Импортируем интеграционный модуль

def main():
    """Главная функция приложения"""
    # Создаем главное окно
    root = tk.Tk()
    
    # Создаем экземпляр приложения
    app = StopwatchApp(root)
    
    # Инициализируем интеграцию с парсером
    parser_integration = ParserIntegration(app)
    
    # Запускаем главный цикл
    root.mainloop()

if __name__ == "__main__":
    main()
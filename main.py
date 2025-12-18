import tkinter as tk
from app import StopwatchApp

def main():
    """Главная функция приложения"""
    # Создаем главное окно
    root = tk.Tk()
    
    # Создаем экземпляр приложения
    app = StopwatchApp(root)
    
    # Запускаем главный цикл
    root.mainloop()

if __name__ == "__main__":
    main()
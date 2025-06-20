#!/usr/bin/env python3
"""
Скрипт запуска бота для ремонта компьютеров
"""
import sys
import asyncio
from pathlib import Path

# Добавляем текущую директорию в PYTHONPATH
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from app.main import main
    
    if __name__ == "__main__":
        print("🚀 Запуск Computer Repair Bot...")
        asyncio.run(main())
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в правильной директории и установили зависимости:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n👋 Бот остановлен пользователем")
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    sys.exit(1)
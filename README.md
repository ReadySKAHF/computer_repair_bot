# Computer Repair Telegram Bot

Современный Telegram бот для сервиса ремонта компьютеров с ИИ консультантом, системой заказов и административной панелью.

## Содержание

- [Возможности](#возможности)
- [Технологии](#технологии)
- [Быстрый старт](#быстрый-старт)
- [Конфигурация](#конфигурация)
- [Структура проекта](#структура-проекта)
- [API и интеграции](#api-и-интеграции)
- [Администрирование](#администрирование)
- [Разработка](#разработка)
- [Деплой](#деплой)
- [FAQ](#faq)

## Возможности

### Для клиентов
- **Умная регистрация** с валидацией данных
- **Создание заказов** с выбором услуг, времени и даты
- **ИИ консультант** на базе Google Gemini для диагностики проблем
- **Каталог услуг** с подробными описаниями и ценами
- **Информация о мастерах** с рейтингами и опытом
- **Система отзывов** с оценками и комментариями
- **Управление профилем** и редактирование данных
- **История заказов** с отслеживанием статусов
- **Техническая поддержка** с FAQ и обратной связью

### Для администраторов
- **Панель аналитики** с детальной статистикой
- **Управление заказами** (просмотр, обновление статусов)
- **Система поддержки** с ответами на обращения
- **Управление пользователями**
- **Резервное копирование** базы данных
- **Системные команды** для администрирования

### Технические особенности
- Полная валидация пользовательских данных
- Безопасная архитектура с обработкой ошибок
- Подробное логирование всех операций
- Модульная структура для легкого расширения
- Асинхронная работа для высокой производительности

## Технологии

| Компонент | Технология | Версия |
|-----------|------------|---------|
| **Backend** | Python | 3.8+ |
| **Bot Framework** | aiogram | 3.4.1 |
| **База данных** | SQLite | aiosqlite 0.19.0 |
| **ИИ** | Google Gemini | google-generativeai 0.8.3 |
| **Валидация** | Pydantic | 2.5.3 |
| **Тестирование** | pytest | 7.4.3 |

## Быстрый старт

### Предварительные требования
- Python 3.8 или выше
- Telegram Bot Token (от @BotFather)
- Google Gemini API Key (от Google AI Studio)

### 1. Установка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/computer-repair-bot.git
cd computer-repair-bot

# Создание виртуального окружения
python -m venv venv

# Активация окружения
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Конфигурация

Создайте файл `config.txt` в корневой папке:

```ini
# Обязательные параметры
BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here

# Дополнительные настройки
DB_PATH=repair_bot.db
LOG_LEVEL=INFO
MAX_SERVICES_PER_ORDER=10
MAX_MESSAGE_LENGTH=1000
RATE_LIMIT_MESSAGES=30
RATE_LIMIT_WINDOW=60

# ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321
```

### 3. Запуск

```bash
python -m app.main
```

## Конфигурация

### Получение токенов

#### Telegram Bot Token
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте полученный токен в `config.txt`

#### Google Gemini API Key
1. Перейдите на Google AI Studio
2. Создайте новый API ключ
3. Скопируйте ключ в `config.txt`

### Параметры конфигурации

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | **Обязательно** |
| `GEMINI_API_KEY` | API ключ Google Gemini | **Обязательно** |
| `DB_PATH` | Путь к файлу базы данных | `repair_bot.db` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `ADMIN_IDS` | Список ID администраторов | Пусто |
| `MAX_SERVICES_PER_ORDER` | Максимум услуг в заказе | `10` |
| `RATE_LIMIT_MESSAGES` | Лимит сообщений | `30` |

## Структура проекта

```
computer_repair_bot/
├── app/                          # Основное приложение
│   ├── main.py                   # Точка входа
│   ├── config.py                 # Управление конфигурацией
│   │
│   ├── handlers/                 # Обработчики сообщений
│   │   ├── registration.py       # Регистрация пользователей
│   │   ├── orders.py            # Управление заказами
│   │   ├── services.py          # Каталог услуг
│   │   ├── profile.py           # Профиль пользователя
│   │   ├── reviews.py           # Система отзывов
│   │   ├── ai_consultation.py   # ИИ консультации
│   │   ├── support.py           # Техподдержка
│   │   └── admin.py             # Админ панель
│   │
│   ├── database/                 # Работа с базой данных
│   │   ├── connection.py        # Подключение и схема БД
│   │   ├── queries.py           # SQL запросы
│   │   └── models.py            # Модели данных
│   │
│   ├── services/                 # Бизнес-логика
│   │   ├── ai_service.py        # Сервис ИИ консультаций
│   │   ├── validation_service.py # Валидация данных
│   │   └── order_service.py     # Управление заказами
│   │
│   ├── keyboards/               # Интерфейсы пользователя
│   │   ├── main_menu.py         # Главное меню
│   │   ├── order_keyboards.py   # Клавиатуры заказов
│   │   └── profile_keyboards.py # Клавиатуры профиля
│   │
│   └── utils/                   # Утилиты
│       ├── constants.py         # Константы
│       └── validators.py        # Валидаторы данных
│
├── config.txt                   # Конфигурация
├── requirements.txt             # Python зависимости
├── .gitignore                   # Исключения Git
└── README.md                    # Документация
```

## API и интеграции

### Google Gemini AI
Бот интегрирован с Google Gemini для интеллектуальных консультаций:

**Возможности ИИ:**
- Анализ проблем по описанию
- Подбор подходящих услуг
- Объяснения простым языком
- Резервная логика при недоступности

**Пример работы:**
```
Пользователь: "Компьютер стал медленно работать и шумит"
ИИ: "Проблемы с производительностью обычно связаны с пылью и перегревом. 
     Рекомендую: диагностику, чистку от пыли, замену термопасты."
```

### База данных
SQLite с оптимизированной схемой:

| Таблица | Описание |
|---------|----------|
| `users` | Данные пользователей |
| `services` | Каталог услуг |
| `masters` | Информация о мастерах |
| `orders` | Заказы клиентов |
| `order_services` | Связь заказов с услугами |
| `reviews` | Отзывы и оценки |
| `support_requests` | Обращения в поддержку |

## Администрирование

### Получение прав администратора
1. Узнайте свой Telegram ID командой `/get_id`
2. Добавьте ID в `config.txt`: `ADMIN_IDS=your_telegram_id`
3. Перезапустите бота

### Админские команды
```bash
/admin              # Главная админ панель
/admin_orders       # Просмотр заказов
/admin_complete 15  # Завершить заказ №15
/admin_cancel 20    # Отменить заказ №20
/get_id            # Узнать свой Telegram ID
```

### Функции админ панели
- **Статистика:** пользователи, заказы, отзывы
- **Управление заказами:** просмотр, изменение статусов
- **Поддержка:** ответы на обращения пользователей
- **Бэкапы:** создание резервных копий БД

## Разработка

### Настройка среды разработки

```bash
# Установка инструментов разработки
pip install black isort flake8 pytest pytest-asyncio

# Форматирование кода
black app/
isort app/

# Проверка стиля кода
flake8 app/ --max-line-length=100

# Запуск тестов
pytest tests/ -v
```

### Архитектурные принципы
- **Модульность:** каждый компонент в отдельном модуле
- **Async/await:** для высокой производительности
- **Валидация:** проверка всех пользовательских данных
- **Логирование:** детальное отслеживание операций
- **Обработка ошибок:** graceful degradation

### Добавление новых функций

#### 1. Новый обработчик
```python
# app/handlers/my_handler.py
from aiogram import Router, F
from aiogram.types import Message

my_router = Router()

@my_router.message(F.text == "Моя кнопка")
async def my_handler(message: Message, db_queries, user):
    await message.answer("Привет!")
```

#### 2. Новая клавиатура
```python
# app/keyboards/my_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_my_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Кнопка", callback_data="my_action")]
    ])
```

#### 3. Новый сервис
```python
# app/services/my_service.py
class MyService:
    def __init__(self, db_queries):
        self.db_queries = db_queries
    
    async def do_something(self):
        return "Результат"
```

## Деплой

### Системные требования
- **ОС:** Linux Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **RAM:** минимум 512MB, рекомендуется 1GB+
- **Диск:** минимум 1GB свободного места
- **Python:** 3.8+

### Production деплой

#### 1. Подготовка сервера
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и pip
sudo apt install python3 python3-pip python3-venv -y

# Создание пользователя для бота
sudo useradd -m -s /bin/bash repairbot
sudo su - repairbot
```

#### 2. Установка приложения
```bash
# Клонирование и настройка
git clone https://github.com/your-repo/computer-repair-bot.git
cd computer-repair-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка конфигурации
cp config.txt.example config.txt
nano config.txt  # Заполните токены
```

#### 3. Systemd сервис
```ini
# /etc/systemd/system/repair-bot.service
[Unit]
Description=Computer Repair Telegram Bot
After=network.target

[Service]
Type=simple
User=repairbot
WorkingDirectory=/home/repairbot/computer-repair-bot
Environment=PATH=/home/repairbot/computer-repair-bot/venv/bin
ExecStart=/home/repairbot/computer-repair-bot/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable repair-bot
sudo systemctl start repair-bot

# Проверка статуса
sudo systemctl status repair-bot
```

#### 4. Мониторинг
```bash
# Логи сервиса
sudo journalctl -u repair-bot -f

# Логи приложения
tail -f /home/repairbot/computer-repair-bot/bot.log
```

### Docker деплой

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "-m", "app.main"]
```

#### docker-compose.yml
```yaml
version: '3.8'
services:
  repair-bot:
    build: .
    restart: unless-stopped
    volumes:
      - ./config.txt:/app/config.txt
      - ./data:/app/data
    environment:
      - LOG_LEVEL=INFO
```

```bash
# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f repair-bot
```

## Устранение неполадок

### Частые проблемы

#### "Некорректный токен бота"
```bash
# Проверка токена
python3 -c "
from app.config import ConfigLoader
config = ConfigLoader.load_from_file()
print(f'Token length: {len(config.bot_token)}')
"
```

**Решение:**
- Убедитесь, что токен скопирован полностью
- Проверьте отсутствие лишних пробелов
- Проверьте кодировку файла `config.txt` (должна быть UTF-8)

#### "ИИ сервис недоступен"
```bash
# Проверка API ключа
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_API_KEY"
```

**Решение:**
- Проверьте корректность API ключа Gemini
- Убедитесь в наличии интернет-соединения
- Проверьте квоты использования API

#### "Ошибка базы данных"
```bash
# Проверка БД
sqlite3 repair_bot.db ".tables"
sqlite3 repair_bot.db ".schema users"
```

**Решение:**
- Удалите файл БД для пересоздания: `rm repair_bot.db`
- Проверьте права доступа к файлу и папке
- Убедитесь в наличии свободного места на диске

### Отладка

#### Детальное логирование
```bash
# Запуск с подробными логами
LOG_LEVEL=DEBUG python -m app.main
```

#### Проверка конфигурации
```python
from app.config import ConfigLoader, validate_config

config = ConfigLoader.load_from_file()
print(f"Конфигурация валидна: {validate_config(config)}")
print(f"Админы: {config.admin_ids}")
```

## FAQ

**Как добавить нового администратора?**

1. Пользователь должен написать боту `/get_id`
2. Добавьте полученный ID в `config.txt`:
   ```
   ADMIN_IDS=123456789,новый_id,987654321
   ```
3. Перезапустите бота

**Как изменить список услуг?**

Услуги находятся в базе данных. Для изменения:
1. Подключитесь к БД: `sqlite3 repair_bot.db`
2. Просмотрите услуги: `SELECT * FROM services;`
3. Добавьте новую: `INSERT INTO services (name, price, duration_minutes, description) VALUES ('Новая услуга', 1000, 60, 'Описание');`

**Как настроить резервное копирование?**

Автоматическое создание бэкапов через cron:
```bash
# Добавить в crontab
0 2 * * * cp /path/to/repair_bot.db /path/to/backups/repair_bot_$(date +\%Y\%m\%d).db
```

**Можно ли использовать другую базу данных?**

Да, можно адаптировать код для работы с PostgreSQL или MySQL, изменив модуль `database/connection.py` и драйвер в `requirements.txt`.

**Как масштабировать бота для большой нагрузки?**

Рекомендации:
- Использовать PostgreSQL вместо SQLite
- Настроить Redis для кэширования
- Использовать webhook вместо polling
- Настроить балансировщик нагрузки

## Поддержка

- **Баги:** Создать Issue в репозитории
- **Предложения:** Открыть Discussion
- **Другие вопросы:** support@yourcompany.com

## Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле LICENSE.

## Roadmap

- [ ] Веб-панель администратора
- [ ] Интеграция с платежными системами
- [ ] Email и SMS уведомления
- [ ] Геолокация для выбора ближайшего мастера
- [ ] REST API для внешних интеграций
- [ ] Мультиязычность интерфейса
- [ ] Расширенная аналитика и дашборды
- [ ] Улучшенный ИИ с обучением на истории

---

**Готов к продакшену!** | **Вклад приветствуется**
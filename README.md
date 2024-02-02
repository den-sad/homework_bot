# Проект телеграм бота для уведомления о стаусах проверик заданий на Yandex Практикум

## Запуск проекта

Склонируйте репозиторий, активируйте виртуальное окружение и установите зависимости:

```
git clone git@github.com:den-sad/homework_bot.git
cd homework_bot
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

Создайте файл переменных окружения в директории проекта:

```
vi .env
```

В файле задейте необходимые переменные

```
PRACTICUM_TOKEN=<PRACTICUM_TOKEN>
TELEGRAM_TOKEN=<TELEGRAM_TOKEN>
TELEGRAM_CHAT_ID=<TELEGRAM_CHAT_ID>
```

Запуск приложения

```
python3 homework_bot.py
```
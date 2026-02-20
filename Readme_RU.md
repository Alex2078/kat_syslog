# kat_syslog

📡 **Syslog-сервер с веб-интерфейсом на Python/Flask**

Легковесный сервер для приёма, сохранения и просмотра syslog-сообщений через UDP с удобным веб-интерфейсом для мониторинга логов в реальном времени.

## ✨ Возможности

- 🔄 Приём syslog-сообщений по протоколу UDP (порт 514 по умолчанию)
- 🌐 Веб-интерфейс для просмотра логов в браузере
- ⚡ Обновление логов в реальном времени через Server-Sent Events (SSE)
- 🔍 Фильтрация сообщений по IP-адресу отправителя
- ⬇️ Скачивание полного файла лога
- 🧵 Асинхронная работа: syslog-слушатель запущен в отдельном процессе
- ⚙️ Гибкая настройка через файл `config.py`

## 🛠 Технологии

- **Python 3.x**
- **Flask** — веб-фреймворк
- **Socket** — работа с UDP
- **HTML/CSS/JS** — фронтенд веб-интерфейса

## 📦 Структура проекта

    kat_syslog/
    ├── app.py              # Основное Flask-приложение (веб-интерфейс)
    ├── syslog_listener.py  # Модуль приёма syslog-сообщений (UDP-сервер)
    ├── config.py           # Файл конфигурации
    ├── maketest.py         # Скрипт для генерации тестовых сообщений
    ├── templates/          # HTML-шаблоны веб-интерфейса
    │   └── index.html
    ├── syslog.log          # Файл для записи логов (создаётся автоматически)
    ├── README.md           # Документация
    └── LICENSE.TXT         # Лицензия GPL v3


## 🚀 Установка и запуск

### Требования

- Python 3.7 или выше
- pip (менеджер пакетов Python)

### 1. Клонирование репозитория

```bash
git clone https://github.com/Alex2078/kat_syslog.git
cd kat_syslog
```

pip install flask

### 3. Настройка (опционально)

Откройте config.py и при необходимости измените параметры:

# Параметры syslog-сервера
SYSLOG_HOST = '0.0.0.0'          # Интерфейс для приёма syslog
SYSLOG_PORT = 514                # Порт UDP для syslog
SYSLOG_LOG_FILE = 'syslog.log'   # Файл для записи логов

# Параметры веб-интерфейса
FLASK_HOST = '0.0.0.0'           # Интерфейс для веб-сервера
FLASK_PORT = 5000                # Порт веб-интерфейса
FLASK_DEBUG = False              # Режим отладки Flask

⚠️ Важно: Для запуска на портах < 1024 (например, стандартный syslog-порт 514) требуются права root.
Варианты решения:

    Запустить с sudo: sudo python3 app.py
    Использовать непривилегированный порт (например, 1514) и перенаправить трафик через iptables
    Настроить capabilities для Python: sudo setcap 'cap_net_bind_service=+ep' $(which python3.x)

### 4. Запуск приложения

```bash
python3 app.py
```

### 5. После запуска:

    📡 Syslog-слушатель начнёт принимать сообщения на UDP 514
    🌐 Веб-интерфейс будет доступен по адресу: http://localhost:5000

### 6. 🌐 Использование веб-интерфейса

Откройте в браузере: http://<ваш_сервер>:5000
Просматривайте последние записи лога (автоматическое обновление)
Используйте поле Filter by IP для фильтрации сообщений
Нажмите Download Log для скачивания полного файла syslog.log

### 7. 📄 Лицензия

### 8. 🐳 Docker Hub

Official image: [`alex2078/kat_syslog`](https://hub.docker.com/r/alex2078/kat_syslog)

### 8.1 Quick start

```bash
# Pull the image
docker pull alex2078/kat_syslog:latest
```

## 8.2 Run with docker run
```bash
docker run -d \
  --name kat_syslog \
  -p 5000:5000 \
  -p 514:514/udp \
  -v $(pwd)/syslog.log:/app/syslog.log \
  alex2078/kat_syslog:latest
```

## 8.3 Or with docker-compose
```bash
wget https://raw.githubusercontent.com/Alex2078/kat_syslog/main/docker-compose.yml
docker-compose up -d
```bash

Проект распространяется под лицензией GNU General Public License v3.0.
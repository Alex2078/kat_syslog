# Параметры syslog-сервера
SYSLOG_HOST = '0.0.0.0'          # слушаем все интерфейсы
SYSLOG_PORT = 514               # стандартный порт syslog
SYSLOG_LOG_FILE = 'syslog.log'  # файл для записи сообщений

# Параметры Flask-приложения
FLASK_HOST = '0.0.0.0'          # хост для веб-интерфейса
FLASK_PORT = 5000              # порт веб-интерфейса
# FLASK_DEBUG = True             # режим отладки (отключить на проде)
FLASK_DEBUG = False             # режим отладки (отключить на проде)
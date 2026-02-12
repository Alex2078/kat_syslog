#!/usr/bin/env python3
"""
Модуль syslog-сервера.
Слушает UDP порт (по умолчанию 514) на всех интерфейсах,
принимает сообщения и дописывает их в файл syslog.log.
"""
import socket
import datetime
import sys
import os
import signal
import time

DEFAULT_LOG_FILE = 'syslog.log'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 514
BUFFER_SIZE = 65535

def run_listener(log_file=DEFAULT_LOG_FILE, host=DEFAULT_HOST, port=DEFAULT_PORT):
    """
    Запуск UDP-сервера для приёма syslog-сообщений.
    Блокирует выполнение (бесконечный цикл).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((host, port))
    except Exception as e:
        print(f"[listener] Ошибка привязки к {host}:{port} - {e}")
        sys.exit(1)
    
    print(f"[listener] Syslog listener запущен на {host}:{port}")
    print(f"[listener] Запись в файл: {log_file}")

    # Обработка сигналов завершения
    def signal_handler(sig, frame):
        print("[listener] Получен сигнал завершения, закрываем сокет...")
        sock.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            if data:
                message = data.decode('utf-8', errors='ignore').strip()
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                log_entry = f"{timestamp} [syslog] from {addr[0]}:{addr[1]} - {message}\n"
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                
                print(log_entry.strip())  # для отладки
        except socket.error:
            continue
        except Exception as e:
            print(f"[listener] Ошибка обработки: {e}")
            time.sleep(0.1)
            continue

if __name__ == '__main__':
    # При самостоятельном запуске можно передать путь к логу, хост и порт
    log_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG_FILE
    host = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_HOST
    port = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_PORT
    run_listener(log_file, host, port)
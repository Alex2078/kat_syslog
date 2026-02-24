import ctypes, sys, os

# def is_admin():
#     try:
#         return ctypes.windll.shell32.IsUserAnAdmin()
#     except:
#         return False

# if not is_admin():
#     # Перезапуск скрипта с правами администратора
#     ctypes.windll.shell32.ShellExecuteW(
#         None, runas", sys.executable, " ".join([__file__] + sys.argv[1:]), None, 1
#     )
#     sys.exit(0)
    
# import os
import time
from flask import Flask, render_template, request, jsonify, send_file
import re
import chardet
import multiprocessing
import threading
import atexit

# Импортируем конфигурацию
from config import (
    SYSLOG_HOST, SYSLOG_PORT, SYSLOG_LOG_FILE,
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG
)

from syslog_listener import run_listener

app = Flask(__name__)

LOG_FILE = SYSLOG_LOG_FILE          # файл лога (из конфига)
LAST_LINES = 100

# --- Управление процессом-прослушивателем ---
listener_process = None
monitor_thread = None
listener_running = False

def start_listener():
    """Запуск дочернего процесса с syslog-сервером"""
    global listener_process
    if listener_process is None or not listener_process.is_alive():
        listener_process = multiprocessing.Process(
            target=run_listener,
            args=(LOG_FILE, SYSLOG_HOST, SYSLOG_PORT),
            daemon=True
        )
        listener_process.start()
        print(f"[app] Syslog listener запущен, PID={listener_process.pid}, порт={SYSLOG_PORT}")

def stop_listener():
    """Корректная остановка процесса-прослушивателя"""
    global listener_process
    if listener_process and listener_process.is_alive():
        print("[app] Останавливаем listener...")
        listener_process.terminate()
        listener_process.join(timeout=5)
        if listener_process.is_alive():
            print("[app] Принудительное завершение listener")
            listener_process.kill()
        print("[app] Listener остановлен")

def monitor_listener():
    """Фоновая задача: проверяет состояние процесса и перезапускает при падении"""
    global listener_process, listener_running
    restart_delay = 5
    while listener_running:
        if listener_process is None or not listener_process.is_alive():
            print("[app] Процесс listener не отвечает, перезапуск...")
            start_listener()
            time.sleep(restart_delay)
            if listener_process and listener_process.is_alive():
                restart_delay = 5
            else:
                restart_delay = min(restart_delay * 2, 60)
        else:
            restart_delay = 5
        time.sleep(5)

def init_listener():
    global listener_running, monitor_thread
    listener_running = True
    start_listener()
    monitor_thread = threading.Thread(target=monitor_listener, daemon=True)
    monitor_thread.start()
    atexit.register(stop_listener)

# --- Функции для работы с лог-файлом ---
def detect_line_encoding(line_bytes):
    try:
        result = chardet.detect(line_bytes)
        if result['confidence'] > 0.5:
            return result['encoding'] if result['encoding'] else 'utf-8'
    except:
        pass
    return 'utf-8'

def decode_line_with_detection(line_bytes):
    if not line_bytes:
        return ""
    encoding = detect_line_encoding(line_bytes)
    encodings_to_try = [
        encoding, 'utf-8', 'cp1251', 'koi8-r',
        'iso-8859-5', 'cp866', 'mac_cyrillic', 'latin-1'
    ]
    encodings_to_try = list(dict.fromkeys(encodings_to_try))
    for enc in encodings_to_try:
        try:
            return line_bytes.decode(enc, errors='strict')
        except (UnicodeDecodeError, LookupError):
            continue
    return line_bytes.decode('utf-8', errors='replace')

def get_last_n_lines_binary(file_path, n=100):
    try:
        with open(file_path, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            buffer_size = 8192
            lines_found = []
            buffer = b''
            position = file_size
            while position > 0 and len(lines_found) < n:
                read_size = min(buffer_size, position)
                position -= read_size
                f.seek(position)
                chunk = f.read(read_size)
                buffer = chunk + buffer
                while b'\n' in buffer:
                    pos = buffer.rfind(b'\n')
                    if pos == len(buffer) - 1:
                        buffer = buffer[:-1]
                        continue
                    line = buffer[pos + 1:] if pos != -1 else buffer
                    buffer = buffer[:pos]
                    if line.strip():
                        lines_found.append(line)
                    if len(lines_found) >= n:
                        break
            if buffer.strip() and len(lines_found) < n:
                lines_found.append(buffer)
            return lines_found[::-1]
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"[app] Ошибка чтения файла: {e}")
        return []

def extract_ips_from_line(line):
    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    return ip_pattern.findall(line)

def get_log_lines(filter_ip=None):
    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w', encoding='utf-8'):
                pass
            return []
        binary_lines = get_last_n_lines_binary(LOG_FILE, LAST_LINES)
        decoded_lines = []
        for line_bytes in binary_lines:
            line = decode_line_with_detection(line_bytes)
            decoded_lines.append(line)
        if filter_ip:
            filtered = []
            for line in decoded_lines:
                ips = extract_ips_from_line(line)
                if any(filter_ip in ip for ip in ips):
                    filtered.append(line)
            decoded_lines = filtered
        return decoded_lines[::-1]
    except Exception as e:
        return [f"Ошибка чтения файла: {str(e)}"]

def tail_log_with_encoding(file_path, filter_ip=None):
    with open(file_path, 'rb') as f:
        f.seek(0, 2)
        while True:
            line_bytes = f.readline()
            if not line_bytes:
                time.sleep(0.1)
                continue
            line = decode_line_with_detection(line_bytes)
            if filter_ip:
                ips = extract_ips_from_line(line)
                if not any(filter_ip in ip for ip in ips):
                    continue
            yield line

# --- Маршруты Flask ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_log')
def get_log():
    filter_ip = request.args.get('filter_ip', '').strip()
    lines = get_log_lines(filter_ip if filter_ip else None)
    return jsonify({'lines': lines})

@app.route('/get_updates')
def get_updates():
    filter_ip = request.args.get('filter_ip', '').strip()
    def generate():
        for line in tail_log_with_encoding(LOG_FILE, filter_ip if filter_ip else None):
            yield f"data: {line}\n\n"
    return generate(), {'Content-Type': 'text/event-stream'}

@app.route('/download')
def download_log():
    """Отдать весь файл лога для скачивания"""
    if not os.path.exists(LOG_FILE):
        return "Файл лога не найден", 404
    try:
        return send_file(
            LOG_FILE,
            as_attachment=True,
            download_name='syslog.log',
            mimetype='text/plain'
        )
    except Exception as e:
        return str(e), 500

# --- Запуск приложения ---
if __name__ == '__main__':
    init_listener()
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8'):
            pass
    app.run(
        debug=FLASK_DEBUG,
        threaded=True,
        host=FLASK_HOST,
        port=FLASK_PORT
    )
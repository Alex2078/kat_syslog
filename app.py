import os
import time
from flask import Flask, render_template, request, jsonify
import re
import chardet
from datetime import datetime

app = Flask(__name__)

LOG_FILE = 'syslog.log'
LAST_LINES = 100

def detect_line_encoding(line_bytes):
    """Определение кодировки для одной строки"""
    try:
        result = chardet.detect(line_bytes)
        if result['confidence'] > 0.5:
            encoding = result['encoding']
            return encoding if encoding else 'utf-8'
    except:
        pass
    return 'utf-8'

def decode_line_with_detection(line_bytes):
    """Декодирование строки с определением кодировки"""
    if not line_bytes:
        return ""
    
    encoding = detect_line_encoding(line_bytes)
    
    encodings_to_try = [
        encoding,
        'utf-8',
        'cp1251',
        'koi8-r',
        'iso-8859-5',
        'cp866',
        'mac_cyrillic',
        'latin-1',
        'cp1252'
    ]
    
    encodings_to_try = list(dict.fromkeys(encodings_to_try))
    
    for enc in encodings_to_try:
        try:
            decoded = line_bytes.decode(enc, errors='strict')
            return decoded
        except (UnicodeDecodeError, LookupError):
            continue
    
    try:
        return line_bytes.decode('utf-8', errors='replace')
    except:
        return f"[Невозможно декодировать строку: {repr(line_bytes[:100])}]"

def extract_ips_from_line(line):
    """Извлечение всех IP-адресов из строки"""
    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    return ip_pattern.findall(line)

def get_last_n_lines_binary(file_path, n=100):
    """Эффективное чтение последних N строк в бинарном режиме"""
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
        print(f"Ошибка чтения файла: {e}")
        return []

def get_log_lines(filter_ip=None):
    """Чтение последних 100 строк лога с возможной фильтрации по IP"""
    try:
        if not os.path.exists(LOG_FILE):
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
    """Генератор для отслеживания новых строк с определением кодировки"""
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

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/get_log')
def get_log():
    """API для получения лога"""
    filter_ip = request.args.get('filter_ip', '').strip()
    lines = get_log_lines(filter_ip if filter_ip else None)
    return jsonify({'lines': lines})

@app.route('/get_stats')
def get_stats():
    """API для получения статистики по IP-адресам"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({'ip_stats': {}})
        
        binary_lines = get_last_n_lines_binary(LOG_FILE, 500)  # Берем больше строк для статистики
        
        ip_counter = {}
        for line_bytes in binary_lines:
            line = decode_line_with_detection(line_bytes)
            ips = extract_ips_from_line(line)
            for ip in ips:
                ip_counter[ip] = ip_counter.get(ip, 0) + 1
        
        # Сортируем по частоте
        sorted_ips = sorted(ip_counter.items(), key=lambda x: x[1], reverse=True)
        
        return jsonify({'ip_stats': dict(sorted_ips[:20])})  # Топ 20 IP
        
    except Exception as e:
        return jsonify({'ip_stats': {}, 'error': str(e)})

@app.route('/get_updates')
def get_updates():
    """API для получения обновлений в реальном времени (SSE)"""
    filter_ip = request.args.get('filter_ip', '').strip()
    
    def generate():
        for line in tail_log_with_encoding(LOG_FILE, filter_ip if filter_ip else None):
            yield f"data: {line}\n\n"
    
    return generate(), {'Content-Type': 'text/event-stream'}

if __name__ == '__main__':
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"{datetime.now()} [INFO] Система запущена\n")
            f.write(f"{datetime.now()} [INFO] SSH подключение от 192.168.1.100\n")
            f.write(f"{datetime.now()} [ERROR] Ошибка аутентификации от 10.0.0.5\n")
            f.write(f"{datetime.now()} [WARN] Подозрительная активность от 192.168.1.150\n")
            f.write(f"{datetime.now()} [INFO] DHCP назначен IP 10.0.0.10\n")
    
    app.run(debug=True, threaded=True, port=5000)
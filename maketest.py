# test_encoding.py - создание тестового файла с разными кодировками
encodings = ['utf-8', 'cp1251', 'koi8-r', 'cp866']
lines = [
    "2024-01-01 10:00:00 [INFO] Подключение с IP 192.168.1.1\n",
    "2024-01-01 10:01:00 [ERROR] Ошибка с IP 10.0.0.1\n", 
    "2024-01-01 10:02:00 [DEBUG] Отладка с IP 172.16.0.1\n",
    "2024-01-01 10:03:00 [WARN] Предупреждение с IP 192.168.0.100\n",
]

with open('syslog.log', 'wb') as f:
    for i, line in enumerate(lines):
        encoding = encodings[i % len(encodings)]
        f.write(line.encode(encoding))
        print(f"Записана строка {i+1} в кодировке {encoding}")
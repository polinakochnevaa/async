# импортируем необходимые модули
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # для прогресс-бара

# запрашиваем у пользователя имя хоста или IP-адрес для сканирования
host = input("пожалуйста, введите имя хоста или IP-адрес для сканирования: ")

# пытаемся разрешить имя хоста в IP-адрес
try:
    host_ip = socket.gethostbyname(host)
except socket.gaierror:
    print(f"имя хоста '{host}' не может быть разрешено. выход.")
    sys.exit()

# определяем диапазон портов для сканирования
start_port = 1  # начальный номер порта
end_port = 1024  # конечный номер порта
# примечание: измените end_port на 65535, чтобы сканировать все возможные порты

# информируем пользователя о начале сканирования
print(f"начинаем сканирование хоста {host} ({host_ip}) с порта {start_port} до {end_port}")

# определяем функцию, которая будет сканировать один порт
def scan_port(port):
    # пытается подключиться к заданному хосту на указанном порту. возвращает номер порта, если он открыт
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # Таймаут в секундах
    result = sock.connect_ex((host_ip, port))
    sock.close()
    if result == 0:
        # если попытка подключения возвращает 0, порт открыт
        return port
    else:
        # порт закрыт или фильтруется
        return None

# список для хранения открытых портов
open_ports = []

try:
    # используем ThreadPoolExecutor для управления пулом потоков
    with ThreadPoolExecutor(max_workers=100) as executor:
        # словарь для отслеживания соответствия future и порта
        future_to_port = {executor.submit(scan_port, port): port for port in range(start_port, end_port + 1)}

        # создаем прогресс-бар
        with tqdm(total=end_port - start_port + 1, desc="сканирование портов") as pbar:
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    result = future.result()
                    if result is not None:
                        open_ports.append(result)
                except KeyboardInterrupt:
                    print("\nсканирование прервано пользователем.")
                    sys.exit()
                except Exception as exc:
                    print(f"порт {port} вызвал исключение: {exc}")
                finally:
                    pbar.update(1)
except KeyboardInterrupt:
    print("\nсканирование прервано пользователем.")
    sys.exit()
except socket.error as e:
    print(f"ошибка сокета: {e}")
    sys.exit()

# после сканирования выводим открытые порты по порядку
open_ports.sort()
if open_ports:
    print("открытые порты:")
    for port in open_ports:
        print(f"порт {port} открыт")
else:
    print("в указанном диапазоне не найдено открытых портов.")

# информируем пользователя о завершении сканирования
print("сканирование завершено.")
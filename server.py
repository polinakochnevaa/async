import socket  # модуль для работы с сокетами
import threading  # модуль для работы с потоками
import sys  # модуль для доступа к некоторым функциям и переменным интерпретатора Python
import signal  # модуль для обработки сигналов (например, Ctrl+C)
import logging  # модуль для логирования
import os  # модуль для работы с файловой системой

# файл для хранения идентификации
IDENTIFICATION_FILE = 'identification.txt'

# настройка логирования
logging.basicConfig(filename='server.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# глобальные флаги
server_running = True  # флаг состояния сервера (работает или завершен)
server_paused = False  # флаг состояния прослушивания (активно или на паузе)

# список для хранения активных клиентских потоков
client_threads = []

def client_handler(conn, addr):
    # функция для обработки взаимодействия с клиентом в отдельном потоке
    logging.info(f"подключен клиент {addr}")
    # записываем информацию об идентификации клиента в файл
    with open(IDENTIFICATION_FILE, 'a') as f:
        f.write(f"клиент {addr} подключился.\n")

    try:
        while True:
            # бесконечный цикл для приема данных от клиента
            data = conn.recv(1024)
            # получаем данные размером до 1024 байт
            if not data:
                # если данных нет, значит клиент отключился
                break
            msg = data.decode()
            # декодируем байтовые данные в строку
            logging.info(f"сообщение от {addr}: {msg}")
            conn.send(data)
            # отправляем данные обратно клиенту (эхо)
    except ConnectionResetError:
        # обработка ситуации, когда клиент неожиданно отключился
        logging.warning(f"соединение с клиентом {addr} было разорвано")
    finally:
        logging.info(f"клиент {addr} отключился")
        conn.close()
        # закрываем соединение с данным клиентом

def server_listener(sock):
    # функция для прослушивания входящих подключений, выполняется в отдельном потоке
    global server_running, server_paused

    while server_running:
        if server_paused:
            # если сервер на паузе, ждем перед проверкой снова
            threading.Event().wait(1)
            continue

        try:
            conn, addr = sock.accept()
            # принимаем новое входящее подключение
            client_thread = threading.Thread(target=client_handler, args=(conn, addr))
            # создаем новый поток для обслуживания клиента
            client_thread.start()
            # запускаем поток
            client_threads.append(client_thread)
            # добавляем поток в список активных потоков
        except socket.timeout:
            # если время ожидания соединения истекло, проверяем состояние сервера
            continue
        except OSError:
            # если сокет был закрыт, выходим из цикла
            break

def main():
    global server_running, server_paused
    sock = socket.socket()
    # создаем TCP-сокет, устанавливаем опцию SO_REUSEADDR, чтобы переиспользовать адрес и порт
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(('', 9090))
    # связываем сокет с адресом и портом.
    sock.listen()
    # переводим сокет в режим прослушивания входящих подключений
    sock.settimeout(1)  # устанавливаем таймаут для accept(), чтобы проверять флаги

    print("сервер запущен и ожидает подключений...")
    logging.info("сервер запущен и ожидает подключений...")

    # запускаем поток для прослушивания входящих соединений
    listener_thread = threading.Thread(target=server_listener, args=(sock,))
    listener_thread.start()

    # основной поток программы для принятия команд от пользователя
    try:
        while True:
            command = input("введите команду (shutdown, pause, resume, show logs, clear logs, clear id): ").strip().lower()

            if command == 'shutdown':
                # завершение работы сервера
                print("завершение работы сервера...")
                logging.info("сервер завершает работу по команде shutdown.")
                server_running = False
                server_paused = False  # на случай, если сервер был на паузе
                sock.close()  # закрываем сокет, чтобы выйти из accept()
                break
            elif command == 'pause':
                if not server_paused:
                    server_paused = True
                    print("сервер поставлен на паузу. Новые подключения не принимаются.")
                    logging.info("сервер поставлен на паузу по команде pause.")
                else:
                    print("сервер уже находится на паузе.")
            elif command == 'resume':
                if server_paused:
                    server_paused = False
                    print("сервер возобновил прием подключений.")
                    logging.info("сервер возобновил работу по команде resume.")
                else:
                    print("сервер и так работает.")
            elif command == 'show logs':
                # показываем содержимое файла логов
                if os.path.exists('server.log'):
                    with open('server.log', 'r') as log_file:
                        print("\n=== содержимое логов ===")
                        print(log_file.read())
                        print("=== конец логов ===\n")
                else:
                    print("лог-файл отсутствует.")
            elif command == 'clear logs':
                # очищаем файл логов
                if os.path.exists('server.log'):
                    open('server.log', 'w').close()
                    print("логи очищены.")
                    logging.info("логи были очищены по команде clear logs.")
                else:
                    print("лог-файл отсутствует.")
            elif command == 'clear id':
                # очищаем файл идентификации
                if os.path.exists(IDENTIFICATION_FILE):
                    open(IDENTIFICATION_FILE, 'w').close()
                    print("файл идентификации очищен.")
                    logging.info("файл идентификации был очищен по команде clear id.")
                else:
                    print("файл идентификации отсутствует.")
            else:
                print("неизвестная команда. доступные команды: shutdown, pause, resume, show logs, clear logs, clear id.")

    except KeyboardInterrupt:
        # обработка сигнала Ctrl+C
        print("\nзавершение работы сервера...")
        logging.info("сервер завершает работу по сигналу Ctrl+C.")
        server_running = False
        server_paused = False
        sock.close()

    # ожидаем завершения потока прослушивания
    listener_thread.join()

    # ожидаем завершения всех клиентских потоков
    for t in client_threads:
        t.join()

    print("сервер остановлен.")
    logging.info("сервер остановлен.")

if __name__ == "__main__":
    main()
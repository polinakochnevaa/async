import asyncio

HOST = 'localhost'  # хост для подключения
PORT = 9095         # порт для подключения

async def tcp_echo_client():
    # асинхронная функция для подключения к серверу и обмена сообщениями
    reader = None
    writer = None

    loop = asyncio.get_running_loop()

    try:
        while True:
            # устанавливаем соединение с сервером
            try:
                reader, writer = await asyncio.open_connection(HOST, PORT)
                print(f"подключено к серверу {HOST}:{PORT}")
                break  # если подключились, выходим из цикла подключения
            except ConnectionRefusedError:
                # если не удалось подключиться, выводим сообщение и ждем 5 секунд
                print(f"не удалось подключиться к серверу {HOST}:{PORT}. повтор через 5 секунд...")
                await asyncio.sleep(5)

        while True:
            # читаем сообщение от пользователя в отдельном потоке, чтобы не блокировать цикл событий
            message = await loop.run_in_executor(None, input, "введите сообщение (или 'exit' для выхода): ")
            if message.lower() == 'exit':
                # если введена команда 'exit', выходим из цикла
                print("отключение от сервера.")
                break

            # Отправляем сообщение серверу
            writer.write(message.encode())
            await writer.drain()  # Ждем, пока данные будут отправлены

            # ожидаем ответ от сервера
            data = await reader.read(100)
            if not data:
                # если данных нет, сервер закрыл соединение
                print("сервер закрыл соединение.")
                break
            print(f"получено эхо: {data.decode()!r}")

    except KeyboardInterrupt:
        # обрабатываем прерывание по Ctrl+C
        print("\nклиент прерван пользователем (Ctrl+C)")
    except ConnectionResetError:
        # обрабатываем случай, когда соединение было разорвано
        print("соединение было закрыто сервером.")
    finally:
        if writer is not None:
            writer.close()  # закрываем соединение
            await writer.wait_closed()
        print("Клиент завершил работу.")

if __name__ == '__main__':
    # запускаем асинхронную функцию tcp_echo_client с помощью asyncio.run()
    asyncio.run(tcp_echo_client())
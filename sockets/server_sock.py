import socket
import time

from core import config

settings = config.get_settings()


def server_program():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((settings.socket_host, settings.socket_port))

        server_socket.listen()
        print("Ожидание подключения клиента...")

        while True:
            try:
                conn, address = server_socket.accept()
                with conn:
                    print("Подключено к:", address)
                    while True:
                        data = conn.recv(8192)
                        if not data:
                            print("No data received. Closing connection.")
                            break

                        print(f"Received from client: {data.decode('utf-8')}")

                        response = f"Message received: {data.decode('utf-8')}"
                        conn.sendall(response.encode('utf-8'))
                        time.sleep(0.1)
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                print("Connection closed.")


if __name__ == '__main__':
    server_program()

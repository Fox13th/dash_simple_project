import socket
import time


def server_program(host: str = '127.0.0.1', port: int = 5002):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))

        server_socket.listen()
        print("Ожидание подключения клиента...")

        while True:
            try:
                conn, address = server_socket.accept()
                with conn:
                    print("Подключено к:", address)
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            print("No data received. Closing connection.")
                            break

                        print(f"Received from client: {data.decode()}")

                        response = f"Message received: {data.decode()}"
                        conn.sendall(response.encode())
                        time.sleep(0.1)
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                print("Connection closed.")


if __name__ == '__main__':
    server_program()

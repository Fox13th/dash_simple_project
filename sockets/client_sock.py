import logging
import socket
import time

import redis

from core import config

settings = config.get_settings()


def client_program(redis_db: redis.Redis, redis_cache_result: redis.Redis):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((settings.socket_host, settings.socket_port))
            while True:

                msg = redis_db.lpop('message_queue')
                if msg:
                    uuid_from_queue = msg.decode('utf-8')[:36]
                    message_to_send = msg.decode('utf-8')[36:]
                    if message_to_send == '':
                        message_to_send = ' '

                    if not uuid_from_queue == '000000000000000000000000000000000000':
                        print(f'Отправка сообщения: {message_to_send}')

                    client_socket.sendall(message_to_send.encode('utf-8'))
                    if not uuid_from_queue == '000000000000000000000000000000000000':
                        print(f'Сообщение отправлено: {message_to_send}')

                    recv_msg = client_socket.recv(1024)
                    if not uuid_from_queue == '000000000000000000000000000000000000':
                        print(f"Сообщение от сервера для {uuid_from_queue}:", f'{recv_msg.decode("utf-8")}\n')

                        cache_value = redis_cache_result.get(uuid_from_queue)
                        if cache_value is not None:
                            res_value = f'{cache_value.decode('utf-8')}\n{recv_msg.decode("utf-8")}'
                        else:
                            res_value = recv_msg.decode("utf-8")

                        redis_cache_result.set(uuid_from_queue, res_value, settings.redis_expiration)

                    time.sleep(1)

    except Exception as err:
        logging.error("Произошла ошибка: %s", err)

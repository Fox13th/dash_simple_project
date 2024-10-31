import logging
import queue
import threading
import time
import uuid
import socket

import redis
from dash import Dash, dcc, html, Input, Output, State
from flask import Flask, session, request

# Создаем сервер Flask
server = Flask(__name__)
server.secret_key = 'your_secret_key'  # Задаем секретный ключ для сессий
messages_queue = queue.Queue()

redis_db = redis.Redis(host='127.0.0.1', port=6379, db=0)


def client_program(host: str = '127.0.0.1', port: int = 5002):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            while True:

                msg = redis_db.lpop('message_queue')
                if msg:
                    print(f'Отправка сообщения: {msg}')
                    client_socket.sendall(msg)
                    print(f'Сообщение отправлено: {msg}')
                    recv_msg = client_socket.recv(1024).decode()
                    print("Сообщение от сервера:", recv_msg)
                print('Cплю')
                time.sleep(3)

    except Exception as err:
        logging.error("Произошла ошибка: %s", err)
    finally:
        print('3')
        messages_queue.task_done()


threading.Thread(target=client_program, daemon=True).start()

# Создаем приложение Dash
app = Dash(__name__, server=server)

# Определяем макет приложения
app.layout = html.Div([
    dcc.Store(id='uuid-store'),  # Хранение UUID
    dcc.Input(id='input-text', type='text', placeholder='Введите текст для перевода...'),
    dcc.Dropdown(
        id='language-dropdown',
        options=[
            {'label': 'Английский', 'value': 'en'},
            {'label': 'Русский', 'value': 'ru'},
            {'label': 'Испанский', 'value': 'es'}
        ],
        placeholder='Выберите язык'
    ),
    html.Button('', id='translate-button',
                style={
                    'display': 'block',
                    'width': '75px',
                    'height': '75px',
                    'border': 'none',
                    'margin-top': '20px',
                    'margin-left': '20px',
                    'border-radius': '40px',
                    'box-shadow': '1px 1px 5px black',
                    'background': 'none',
                    'background-image': "url('./assets/icon.svg')",
                    'background-size': 'cover',
                    'background-repeat': 'no-repeat'
                }),
    html.Div(id='output-text')
])


@app.callback(
    Output('uuid-store', 'data'),
    Input('uuid-store', 'data')  # Вызываем callback при загрузке
)
def generate_uuid(existing_uuid):
    if existing_uuid is None:
        uuid_session = str(uuid.uuid4())
        logging.info(uuid_session)
        print(uuid_session)
        return uuid_session  # Генерация UUID
    return existing_uuid


# Коллбэк для обработки перевода
@app.callback(
    Output('output-text', 'children'),
    Input('translate-button', 'n_clicks'),
    State('input-text', 'value'),
    State('language-dropdown', 'value'),
    State('uuid-store', 'data')
)
def translate_text(n_clicks, input_text, target_language, uuid_value):
    if n_clicks is None:
        return "Введите текст и выберите язык для перевода."

    print(request.remote_addr + ' ' + uuid_value)
    if target_language:
        msg = f'Переведенный текст на {target_language}: {input_text} на {target_language}'
        redis_db.rpush('message_queue', msg)
        #redis_db.set('key', msg)
        # messages_queue.put(msg)
        return msg
    return "Пожалуйста, выберите язык."


# Запускаем сервер
if __name__ == '__main__':
    app.run_server(debug=True)

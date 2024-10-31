import logging
import threading
import time
import uuid
import socket

import redis
from dash import Dash, dcc, html, Input, Output, State
from flask import Flask

# Создаем сервер Flask
server = Flask(__name__)
server.secret_key = 'your_secret_key'  # Задаем секретный ключ для сессий

redis_db = redis.Redis(host='127.0.0.1', port=6379, db=0)


def client_program(host: str = '127.0.0.1', port: int = 5002):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            while True:

                msg = redis_db.lpop('message_queue')
                if msg:
                    uuid_from_queue = msg.decode('utf-8')[:36]
                    message_to_send = msg.decode('utf-8')[36:]
                    if not uuid_from_queue == '000000000000000000000000000000000000':
                        print(f'Отправка сообщения: {message_to_send}')

                    client_socket.sendall(message_to_send.encode('utf-8'))
                    if not uuid_from_queue == '000000000000000000000000000000000000':
                        print(f'Сообщение отправлено: {message_to_send}')

                    recv_msg = client_socket.recv(1024)
                    if not uuid_from_queue == '000000000000000000000000000000000000':
                        print(f"Сообщение от сервера для {uuid_from_queue}:", f'{recv_msg.decode("utf-8")}\n')
                    time.sleep(1)

    except Exception as err:
        print("Произошла ошибка: %s", err)


# threading.Thread(target=client_program, daemon=True).start()

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

    if target_language:
        msg = f'{uuid_value}Переведенный текст на {target_language}: {input_text} на {target_language}'
        redis_db.rpush('message_queue', msg)
        return msg[36:]
    return "Пожалуйста, выберите язык."


# Запускаем сервер
if __name__ == '__main__':
    # Обязательно нужна для калибровки
    redis_db.rpush('message_queue', f'000000000000000000000000000000000000 ')

    threading.Thread(target=client_program).start()
    app.run_server(debug=True)

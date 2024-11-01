import threading
import uuid

import redis
from dash import Dash, dcc, html, Input, Output, State
from flask import Flask

from client_sock import client_program

# Создаем сервер Flask
server = Flask(__name__)
server.secret_key = 'your_secret_key'  # Задаем секретный ключ для сессий

redis_db = redis.Redis(host='127.0.0.1', port=6379, db=0)
redis_cache_result = redis.Redis(host='127.0.0.1', port=6379, db=1)


# Создаем приложение Dash
app = Dash(__name__, server=server)

# Определяем макет приложения
app.layout = html.Div([
    dcc.Store(id='uuid-store'),  # Хранение UUID
    dcc.Dropdown(
        id='language-dropdown',
        options=[
            {'label': 'Английский', 'value': 'en'},
            {'label': 'Русский', 'value': 'ru'},
            {'label': 'Испанский', 'value': 'es'}
        ],
        placeholder='Выберите язык'
    ),
    dcc.Textarea(id='text_in',
                 value='',
                 placeholder='Введите текст здесь...',
                 style={'width': '100%', 'height': 200}),
    dcc.Textarea(id='text_out',
                 value='',
                 placeholder='Здесь будет обработанный',
                 readOnly=True,
                 style={'width': '100%', 'height': 200}),
    dcc.Interval(
        id='interval-component',
        interval=1000,  # Интервал в миллисекундах (1000 мс = 1 секунда)
        n_intervals=0  # Начальное количество интервалов
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
    html.Div(id='output-text'),
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
    State('language-dropdown', 'value'),
    State('uuid-store', 'data'),
    State('text_in', 'value')
)
def translate_text(n_clicks: int, target_language: str, uuid_value: str, text_in_textarea: str) -> str:
    if n_clicks is None:
        return "Введите текст и выберите язык для перевода."

    if target_language and text_in_textarea:
        redis_cache_result.delete(uuid_value)

        paragraphs = text_in_textarea.split('\n')
        for paragraph in paragraphs:
            redis_db.rpush('message_queue', f'{uuid_value}{paragraph}')
        return 'Отправлено в очередь'
    return "Пожалуйста, выберите язык."


@app.callback(
    Output('text_out', 'value'),
    Input('interval-component', 'n_intervals'),
    State('uuid-store', 'data')
)
def show_result_in_cache(n_inter: int, uuid_data: str) -> str | None:
    if uuid_data:
        result_session = redis_cache_result.get(uuid_data)
        if result_session:
            return result_session.decode('utf-8')
        else:
            return None
    else:
        return None


# Запускаем сервер
if __name__ == '__main__':
    # Обязательно нужна для калибровки
    redis_db.rpush('message_queue', f'000000000000000000000000000000000000 ')
    threading.Thread(target=client_program, args=(redis_db, redis_cache_result)).start()
    app.run_server(debug=True)

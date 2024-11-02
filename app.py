import threading
import uuid

import redis
from dash import Dash, dcc, html, Input, Output, State
from flask import Flask

from services.converters import PDF2DOCX
from sockets.client_sock import client_program
from core import config

settings = config.get_settings()

redis_db = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)
redis_cache_result = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=1)

server = Flask(__name__)
server.secret_key = 'your_secret_key'  # Задаем секретный ключ для сессий

app = Dash(__name__, server=server, prevent_initial_callbacks='initial_duplicate')

app.layout = html.Div(style={'display': 'flex'})

sidebar = html.Div(
    [
        html.H2("Боковая панель"),
        html.Ul([
            html.Li("Ссылка 1"),
            html.Li("Ссылка 2"),
            html.Li("Ссылка 3"),
        ])
    ],
    style={
        'width': '200px',  # Ширина боковой панели
        'padding': '20px',
        'background-color': '#f8f9fa',  # Цвет фона
        'border-right': '1px solid #dee2e6'  # Граница справа
    }
)

# Определяем макет приложения
content = html.Div([

    dcc.Store(id='uuid-store'),  # Хранение UUID
    html.Div(style={'display': 'flex', 'flexDirection': 'row', 'gap': '10px', 'margin-top': '15px'},
             children=[
                 dcc.Dropdown(
                     id='language-dropdown',
                     options=[
                         {'label': 'Английский', 'value': 'en'},
                         {'label': 'Русский', 'value': 'ru'},
                         {'label': 'Испанский', 'value': 'es'}
                     ],
                     placeholder='Выберите язык',
                     style={'width': '300px', 'height': '30px'}
                 ),
                 dcc.Dropdown(
                     id='language-dst',
                     options=[
                         {'label': 'Английский', 'value': 'en'},
                         {'label': 'Русский', 'value': 'ru'},
                         {'label': 'Испанский', 'value': 'es'}
                     ],
                     placeholder='Выберите язык',
                     style={'width': '300px', 'height': '30px'}
                 ),
             ]),

    html.Div(style={'display': 'flex', 'flexDirection': 'row', 'gap': '10px', 'margin-top': '15px'},
             children=[
                 dcc.Textarea(id='text_in',
                              value='',
                              placeholder='Введите текст здесь...',
                              style={'width': '100%', 'height': '200px'}),
                 dcc.Textarea(id='text_out',
                              value='',
                              placeholder='Здесь будет обработанный',
                              readOnly=True,
                              style={'width': '100%', 'height': '200px'}),
             ]),
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

app.layout.children = [sidebar, content]


@app.callback(

    Output('uuid-store', 'data'),
    Input('uuid-store', 'data')  # Вызываем callback при загрузке
)
def generate_uuid(existing_uuid):
    if existing_uuid is None:
        uuid_session = str(uuid.uuid4())
        return uuid_session
    return existing_uuid


# Коллбэк для обработки перевода
@app.callback(
    Output('output-text', 'children'),
    Output('translate-button', 'disabled', allow_duplicate=True),
    Input('translate-button', 'n_clicks'),
    State('language-dropdown', 'value'),
    State('uuid-store', 'data'),
    State('text_in', 'value')
)
def translate_text(n_clicks: int, target_language: str, uuid_value: str, text_in_textarea: str):
    if n_clicks is None:
        return "Введите текст и выберите язык для перевода.", False

    PDF2DOCX().func_covert('1.pdf', '1.docx')

    if target_language and text_in_textarea:
        redis_cache_result.delete(uuid_value)

        paragraphs = text_in_textarea.split('\n')
        for paragraph in paragraphs:
            redis_db.rpush('message_queue', f'{uuid_value}{paragraph}')
        return 'Отправлено в очередь', True
    return "Пожалуйста, выберите язык.", False


@app.callback(
    Output('text_out', 'value'),
    Output('translate-button', 'disabled', allow_duplicate=True),
    Input('interval-component', 'n_intervals'),
    State('uuid-store', 'data'),
    State('text_in', 'value'),
    State('text_out', 'value')
)
def show_result_in_cache(n_inter: int, uuid_data: str, text_in_ta: str, text_out_ta: str):
    if uuid_data:
        if text_in_ta and text_out_ta:
            if len(text_out_ta.split('\n')) < len(text_in_ta.split('\n')):
                but_enable = True
            else:
                but_enable = False
        else:
            but_enable = False

        result_session = redis_cache_result.get(uuid_data)
        if result_session:
            return result_session.decode('utf-8'), but_enable
        else:
            return None, False
    else:
        return None, False


# Запускаем сервер
if __name__ == '__main__':
    # Обязательно нужна для калибровки
    redis_db.rpush('message_queue', f'000000000000000000000000000000000000 ')
    threading.Thread(target=client_program, args=(redis_db, redis_cache_result)).start()
    app.run_server(debug=settings.debug)

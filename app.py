import os
import shutil
import sys
import threading
import time
import urllib
import uuid

import dash
import redis
from dash import Dash, dcc, html, Input, Output, State
from dotenv import set_key, load_dotenv
from flask import Flask
from pdf2docx import Converter

from services.converters import PDF2DOCX
from services.file_reader import TXTReader, DocxReader
from services.lang_detect import LangDetect
from sockets.client_sock import client_program
from core import config

settings = config.get_settings()

redis_db = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)
redis_cache_result = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=1)

server = Flask(__name__)
server.secret_key = 'your_secret_key'  # Задаем секретный ключ для сессий

app = Dash(__name__, server=server, prevent_initial_callbacks='initial_duplicate')

app.layout = html.Div(style={'display': 'flex'})

DIRECTORY_PATH = settings.docs_directory

load_dotenv()


def create_links(dir_path: str) -> list:
    files = os.listdir(dir_path)

    links = []
    for file in files:
        file_ext = file[file.rfind('.') + 1:]
        if file_ext in ['doc', 'docx', 'pdf', 'txt']:
            file_path = os.path.join(dir_path, file)
            if file_ext == 'docx':
                file_ext = 'doc'
            links.append(html.Li(dcc.Link(children=[html.Img(src=f'./assets/{file_ext}.svg',
                                                           style={'width': '30px',
                                                                  'height': '30px',
                                                                  'marginRight': '10px'}),
                                                  file],
                                        href=f'{file}',
                                        id=f'{file.replace('.', '/')}',
                                        style={
                                            'display': 'flex',
                                            'alignItems': 'center',
                                            'color': '#E0115F',
                                            'textDecoration': 'none'}),
                                 id=f'li_ref',
                                 style={
                                     'transition': 'transform .6s ease'
                                 }),
                         )
    return links


sidebar = html.Div(
    [
        html.Div(children=[
            html.H2("Ссылки на файлы", style={'color': '#E0115F'}),
            dcc.Location(id='url', refresh=False),
            dcc.Loading(
                id='load_button',
                type='circle',
                color='#E0115F',
                children=[
                    html.Button('', id='all-button',
                                className='button',
                                style={
                                    'display': 'flex',
                                    'width': '55px',
                                    'height': '55px',
                                    'border': 'none',
                                    'margin-left': '20px',
                                    'border-radius': '40px',
                                    'box-shadow': '1px 1px 5px black',
                                    'background': 'none',
                                    'background-image': "url('./assets/play.svg')",
                                    'background-size': 'cover',
                                    'background-repeat': 'no-repeat',

                                    'transition': 'transform 0.1s'
                                }),
                ]
            ),

        ], style={'display': 'flex',
                  'flexDirection': 'row',
                  'alignItems': 'center',
                  'justifyContent': 'center',
                  }),
        html.Div(style={'display': 'flex',
                        'flexDirection': 'row',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        },
                 children=[
                     dcc.Input(id='input_dir', value=DIRECTORY_PATH, style={'width': '195px'}),
                     html.Button('', id='refresh-button',
                                 className='button',
                                 style={
                                     'display': 'flex',
                                     'width': '25px',
                                     'height': '25px',
                                     'border': 'none',
                                     'margin-left': '20px',
                                     'border-radius': '40px',
                                     'background': 'none',
                                     'background-image': "url('./assets/refresh.svg')",
                                     'background-size': 'cover',
                                     'background-repeat': 'no-repeat',

                                     'transition': 'transform 0.1s'
                                 }),
                 ]
                 ),
        html.Hr(),
        html.Ul(create_links(DIRECTORY_PATH), style={'list-style': 'none'}, id='links-list')
    ],
    style={
        'width': '25vw',  # Ширина боковой панели
        'padding': '20px',
        'background-color': '#f9f6f6',  # Цвет фона
        'border-right': '1px solid #dee2e6',  # Граница справа
        'maxHeight': '100vh',
        'overflowY': 'auto',
        'boxShadow': '2px 2px 10px rgba(0, 0, 0, 0.1)'
    }
)

# Определяем макет приложения
content = html.Div([

    dcc.Store(id='uuid-store'),  # Хранение UUID
    html.Div(style={'background-color': '#8f060a',
                    'height': '250px',
                    'justifyContent': 'center',
                    'width': '75vw',
                    },
             children=[
                 html.H2('asdadsad', style={'margin-top': '0px',
                                            'text-align': 'center',
                                            'padding': '10px',
                                            'color': '#f6e4da'}),
                 html.H2('asdadsad', style={
                     'text-align': 'center',
                     'color': '#f6e4da'}),
                 html.Div(style={'display': 'flex',
                                 'flexDirection': 'row',
                                 'alignItems': 'center',
                                 'justifyContent': 'center',
                                 'gap': '10px',
                                 'margin': '340px',
                                 'margin-top': '100px',
                                 'background-color': '#f8f9fa',
                                 'border': '2px solid lightgray',
                                 'padding': '10px',
                                 'borderRadius': '5px',
                                 'boxShadow': '2px 2px 10px rgba(0, 0, 0, 0.1)'
                                 },
                          children=[
                              html.Div(children=[
                                  html.Label('Выберите язык (исходный):'),
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
                              ]),

                              html.Div(children=[
                                  html.Div(children=[
                                      html.Label("Выберите язык (Целевой):"),
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
                                  ])
                              ]),

                              html.Button('', id='translate-button',
                                          className='button',
                                          style={
                                              'display': 'flex',
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
                                              'background-repeat': 'no-repeat',
                                              'transition': 'transform 0.1s'
                                          }),
                          ]),
             ]),

    html.Div(style={'display': 'flex',
                    'flexDirection': 'row',
                    'gap': '10px',
                    'height': '40vh',
                    'margin': '100px',
                    'margin-top': '150px',
                    'background-color': '#f8f9fa',
                    'border': '2px solid lightgray',
                    'padding': '10px',
                    'borderRadius': '5px',
                    'boxShadow': '2px 2px 10px rgba(0, 0, 0, 0.1)'
                    },
             children=[
                 dcc.Textarea(id='text_in',
                              value='',
                              placeholder='Введите текст здесь...',
                              style={'width': '100%', 'height': '39.5vh'}),
                 dcc.Textarea(id='text_out',
                              value='',
                              placeholder='Здесь будет обработанный',
                              readOnly=True,
                              style={'width': '100%', 'height': '39.5vh'}),
             ]),
    dcc.Interval(
        id='interval-component',
        interval=1000,  # Интервал в миллисекундах (1000 мс = 1 секунда)
        n_intervals=0  # Начальное количество интервалов
    ),
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

    # PDF2DOCX().func_covert('1.pdf', '1.docx')

    if target_language and text_in_textarea:
        redis_cache_result.delete(uuid_value)

        paragraphs = text_in_textarea.split('\n')
        for paragraph in paragraphs:
            lang_parag = LangDetect().detection(paragraph)
            redis_db.rpush('message_queue', f'{uuid_value}{lang_parag['language']}{paragraph}')
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
            return result_session.decode('utf-8'), but_enable  # , links
        else:
            return None, False
    else:
        return None, False


@app.callback(
    Output('links-list', 'children', allow_duplicate=True),
    Input('refresh-button', 'n_clicks'),
    State('url', 'href'),
    State('input_dir', 'value')
)
def refresh_docs(n_click: int | None, href: str, dir_docs: str):

    if n_click is not None:
        if n_click > 0:
            if not os.path.exists(dir_docs):
                return [html.Li(html.A(children=[html.Img(src=f'./assets/error-page.svg',
                                                          style={'width': '30px',
                                                                 'height': '30px',
                                                                 'marginRight': '10px'}),
                                                 'Указанная директория не существует!'],
                                       href='error-page',
                                       target="_blank",
                                       id=f'error-page',
                                       style={
                                           'display': 'flex',
                                           'alignItems': 'center',
                                           'color': '#E0115F',
                                           'textDecoration': 'none'}),
                                )]
            files = os.listdir(dir_docs)
            supported_files = [file for file in files if file[file.rfind('.') + 1:] in ['doc', 'docx', 'pdf', 'txt']]
            if len(supported_files) == 0:
                return [html.Li(html.A(children=[html.Img(src=f'./assets/error.svg',
                                                          style={'width': '30px',
                                                                 'height': '30px',
                                                                 'marginRight': '10px'}),
                                                 'Указанная директория не содержит файлов поддерживаемых форматов!'],
                                       href='empty-dir',
                                       target="_blank",
                                       id=f'empty-dir',
                                       style={
                                           'display': 'flex',
                                           'alignItems': 'center',
                                           'color': '#E0115F',
                                           'textDecoration': 'none'}),
                                )]
            set_key('.env', 'DOCS_DIRECTORY', dir_docs)
            DIRECTORY_PATH = dir_docs

            # Пока что нащел радикальное решение просто перезапустить приложение
            # os.execl(sys.executable, sys.executable, *sys.argv)
            return create_links(DIRECTORY_PATH)


@app.callback(
    Output('all-button', 'disabled'),
    Input('all-button', 'n_clicks'),
    State('all-button', 'disabled')
)
def translate_docs(n_clicks: int, is_disabled: bool):
    if n_clicks > 0 and not is_disabled:
        is_disabled = True
        for file_name in os.listdir(DIRECTORY_PATH):
            file_ext = file_name[file_name.rfind('.') + 1:]
            if file_ext in ['pdf']:
                if not os.path.exists('./temp'):
                    os.mkdir('./temp')

                PDF2DOCX().func_covert(os.path.join(DIRECTORY_PATH, file_name),
                                       f'./temp/{file_name[:file_name.rfind('.')]}.docx')
            elif file_ext == 'docx':
                copy_file_name = f'{file_name[:file_name.rfind('.')]}_translated.docx'
                shutil.copy(os.path.join(DIRECTORY_PATH, file_name), os.path.join(DIRECTORY_PATH, copy_file_name))

        is_disabled = False
        return is_disabled

    return is_disabled


@app.callback(
    Output('text_in', 'value'),
    Output('links-list', 'children', allow_duplicate=True),
    Input('url', 'pathname')
)
def select_ref(pathname: str):
    links = create_links(DIRECTORY_PATH)
    if not pathname or pathname == '/':
        return "", links

    try:
        # file_name = pathname[1:].replace('%20', ' ')
        file_name = urllib.parse.unquote(pathname[1:])
        file_ext = file_name[file_name.rfind('.') + 1:]
        file_path = os.path.join(DIRECTORY_PATH, file_name)

        if file_ext == 'txt':
            data_str = TXTReader(method=1).file_read(file_path)
        elif file_ext == 'docx':
            data_str = DocxReader(method=1).file_read(file_path)
        elif file_ext == 'pdf':
            converted_file = os.path.join(os.path.abspath('.'), 'temp', f'{file_name[:file_name.rfind('.')]}.docx')
            if not os.path.exists(converted_file):
                PDF2DOCX().func_covert(file_path, converted_file)
            data_str = DocxReader(method=1).file_read(converted_file)
        else:
            data_str = f'Файл {file_name} не поддерживается'
        return data_str, links
    except Exception as e:
        return f'Ошибка при обработке файла: {str(e)}'


# Запускаем сервер
if __name__ == '__main__':
    if settings.clear_queue:
        redis_db.delete('message_queue')
    # Обязательно нужна для калибровки
    redis_db.rpush('message_queue', f'000000000000000000000000000000000000 ')
    threading.Thread(target=client_program, args=(redis_db, redis_cache_result)).start()
    app.run_server(debug=settings.debug)

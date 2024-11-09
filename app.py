import os
import shutil
import threading
import time
import urllib
import uuid

import redis
from dash import Dash, html, Input, Output, State
from dotenv import set_key, load_dotenv
from flask import Flask
from pdf2docx import Converter

from layouts.content import get_content
from layouts.links import create_links
from layouts.sidebar import get_sidebar
from services.converters import PDF2DOCX
from services.file_reader import TXTReader, DocxReader
from services.lang_detect import LangDetect
from sockets.client_sock import client_program
from core import config

settings = config.get_settings()

DIRECTORY_PATH = settings.docs_directory

redis_db = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

redis_cache_result = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=1)

server = Flask(__name__)
server.secret_key = 'your_secret_key'  # Задаем секретный ключ для сессий

app = Dash(__name__, server=server, prevent_initial_callbacks='initial_duplicate')
app.layout = html.Div(style={'display': 'flex'})
app.layout.children = [get_sidebar(DIRECTORY_PATH), get_content()]

load_dotenv()


@app.callback(
    Output('uuid-store', 'data'),
    Input('uuid-store', 'data')  # Вызываем callback при загрузке
)
def generate_uuid(existing_uuid):
    if existing_uuid is None:
        uuid_session = str(uuid.uuid4())
        return uuid_session
    return existing_uuid


# Коллбэк для обработки обычного перевода
@app.callback(
    Output('output-text', 'children'),
    Output('translate-button', 'disabled', allow_duplicate=True),
    Input('translate-button', 'n_clicks'),
    State('language-dropdown', 'value'),
    State('uuid-store', 'data'),
    State('text_in', 'value'),
    State('checklist', 'value')
)
def translate_text(n_clicks: int, target_language: str, uuid_value: str, text_in_textarea: str, auto_detect: list):
    if n_clicks is None:
        return "Введите текст и выберите язык для перевода.", False

    if (target_language or len(auto_detect) > 0) and text_in_textarea:
        redis_cache_result.delete(uuid_value)

        paragraphs = text_in_textarea.split('\n')
        print(paragraphs)
        for paragraph in paragraphs:

            if len(auto_detect) > 0:
                lang_parag = LangDetect().detection(paragraph)
                lang_src = lang_parag['language']
            else:
                lang_src = target_language

            redis_db.rpush('message_queue', f'{uuid_value}{lang_src}{paragraph}')
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
            # Здесь надо придумать что-то, чтобы при повторной передаче не приходили остатки
            if len(text_out_ta.split('\n')) < len(text_in_ta.split('\n')):
                but_enable = False
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
    global DIRECTORY_PATH
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
            settings.docs_directory = dir_docs
            # Пока что нащел радикальное решение просто перезапустить приложение
            # os.execl(sys.executable, sys.executable, *sys.argv)
            return create_links(DIRECTORY_PATH)


def add_queue_docx_part(part_doc: list, uuid: str, name_count: int, name: str, type_part: str):
    for i in range(len(part_doc)):
        if type_part == 'text':
            text_doc = part_doc[i].text
        else:
            text_doc = part_doc[i]

        if type_part == 'tabl':
            txt_cell = part_doc[i][part_doc[i].find('text:') + 5:]
            lang_old = LangDetect().detection(txt_cell)
        else:
            lang_old = LangDetect().detection(text_doc)

        if len(lang_old['language']) == 2:
            lang_src = f'{lang_old['language']} '
        else:
            lang_src = lang_old['language']

        string_to_send = f'{uuid}{name_count}{name}{i}{type_part}{lang_src}{text_doc}'
        redis_db.rpush('docx_queue', string_to_send)


@app.callback(
    Output('all-button', 'disabled'),
    Input('all-button', 'n_clicks'),
    State('all-button', 'disabled'),
    State('uuid-store', 'data'),
)
def translate_docs(n_clicks: int, is_disabled: bool, uuid_value: str):
    global DIRECTORY_PATH

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
                only_name = f'{file_name[:file_name.rfind('.')]}_translated.docx'

                count_name = str(len(only_name))
                if len(count_name) < 3:
                    for i in range(3 - len(count_name)):
                        count_name += " "

                copy_file_name = os.path.join(DIRECTORY_PATH, only_name)
                shutil.copy(os.path.join(DIRECTORY_PATH, file_name), copy_file_name)

                old_paragraphs = DocxReader(method=2).file_read(copy_file_name)
                old_header, old_footer = DocxReader(method=2).colontituls_read(copy_file_name)
                old_table, old_n_table = DocxReader(method=2).table_read(copy_file_name)

                add_queue_docx_part(old_header, uuid_value, count_name, only_name, 'ucln')
                add_queue_docx_part(old_footer, uuid_value, count_name, only_name, 'dcln')
                add_queue_docx_part(old_paragraphs, uuid_value, count_name, only_name, 'text')
                add_queue_docx_part(old_table, uuid_value, count_name, only_name, 'tabl')
                add_queue_docx_part(old_n_table, uuid_value, count_name, only_name, 'tabl')

            elif file_ext == 'txt':
                only_name = f'{file_name[:file_name.rfind('.')]}_translated.txt'

                count_name = str(len(only_name))
                if len(count_name) < 3:
                    for i in range(3 - len(count_name)):
                        count_name += " "

                txt_lines = TXTReader(2).file_read(os.path.join(DIRECTORY_PATH, file_name))

                for i_line, line in enumerate(txt_lines):
                    lang_old = LangDetect().detection(line.replace('\n', ''))
                    string_to_send = f'{uuid_value}{count_name}{only_name}{i_line}_txt{lang_old['language']}{line}'
                    redis_db.rpush('docx_queue', string_to_send)

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
        redis_db.delete('docx_queue')
    # Обязательно нужна для калибровки
    redis_db.rpush('message_queue', f'000000000000000000000000000000000000 ')
    # redis_db.rpush('docx_queue', f'000000000000000000000000000000000000 ')

    threading.Thread(target=client_program, args=(redis_db, redis_cache_result)).start()
    app.run_server(debug=settings.debug)

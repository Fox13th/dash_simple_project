import base64
import logging
import os
import shutil
import threading
import time
import urllib
import uuid

import redis
from dash import Dash, html, Input, Output, State, dash, dcc
from dash.dependencies import ALL

from dotenv import set_key, load_dotenv
from flask import Flask

from layouts.content import get_content
from layouts.links import create_links
from layouts.sidebar import get_sidebar
from services.converters import PDF2DOCX, DOC2DOCX, ODT2DOCX, RTF2DOCX, PPTX2DOCX, PDF2TXT
from services.file_reader import TXTReader, DocxReader, PDFReader
from services.lang_detect import LangDetect
from sockets.client_sock import client_program
from core import config

load_dotenv()
settings = config.get_settings()

DIRECTORY_PATH = os.environ.get('DOCS_DIRECTORY')

redis_db = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

redis_cache_result = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=1)

server = Flask(__name__)
server.secret_key = 'your_secret_key'  # Задаем секретный ключ для сессий

app = Dash(__name__, server=server, update_title=None, prevent_initial_callbacks='initial_duplicate')

app.title = 'SDT "Переводчик"'
app._favicon = "icon.ico"

app.layout = html.Div(style={'display': 'flex'})

app.layout.children = [get_sidebar(DIRECTORY_PATH), get_content()]

load_dotenv()


@app.callback(
    Output('output-text', 'children', allow_duplicate=True),
    Input('save-button', 'n_clicks'),
    State({'type': 'checkbox', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def save_transl(n_clicks, chk_box):
    if n_clicks > 0:
        files_save = []
        for i in range(len(chk_box)):
            try:
                files_save.append(chk_box[i][0])
            except IndexError:
                continue

        for file in files_save:
            return dcc.send_file(
                f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.docx'
            )
            # if file.endswith(('docx', 'doc', 'odt', 'rtf', 'ppt', 'pptx')):
            #    if os.path.exists(f'{settings.docs_directory}/{file}'):
            #        os.remove(f'{settings.docs_directory}/{file}')
            #    if os.path.exists(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated.docx'):
            #        os.remove(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated.docx')
            #    if os.path.exists(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.docx'):
            #        os.remove(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.docx')
        #
        # if file.endswith(('pdf', 'txt')):
        #    if os.path.exists(f'{settings.docs_directory}/{file}'):
        #        os.remove(f'{settings.docs_directory}/{file}')
        #    if os.path.exists(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated.txt'):
        #        os.remove(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated.txt')
        #    if os.path.exists(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.txt'):
        #        os.remove(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.txt')
        return ''


@app.callback(
    Output('output-text', 'children', allow_duplicate=True),
    Input('delete-button', 'n_clicks'),
    State({'type': 'checkbox', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def delete_transl(n_clicks, chk_box):
    if n_clicks > 0:
        files_delete = []
        for i in range(len(chk_box)):
            try:
                files_delete.append(chk_box[i][0])
            except IndexError:
                continue

        for file in files_delete:
            if file.endswith(('docx', 'doc', 'odt', 'rtf', 'ppt', 'pptx')):
                if os.path.exists(f'{settings.docs_directory}/{file}'):
                    os.remove(f'{settings.docs_directory}/{file}')
                if os.path.exists(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated.docx'):
                    os.remove(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated.docx')
                if os.path.exists(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.docx'):
                    os.remove(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.docx')

            if file.endswith(('pdf', 'txt')):
                if os.path.exists(f'{settings.docs_directory}/{file}'):
                    os.remove(f'{settings.docs_directory}/{file}')
                if os.path.exists(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated.txt'):
                    os.remove(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated.txt')
                if os.path.exists(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.txt'):
                    os.remove(f'{settings.docs_directory}/{file[:file.rfind('.')]}_translated_done.txt')
        return ''


@app.callback(
    Output('output-text', 'value', allow_duplicate=True),
    Input('upload-data', 'contents'),
    Input('upload-data', 'filename'),
    prevent_initial_call=True
)
def save_file(contents, filenames):
    if contents is not None:

        for content, filename in zip(contents, filenames):
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            file_path = os.path.join(DIRECTORY_PATH, filename)

            with open(file_path, 'wb') as f:
                f.write(decoded)

        return f'Файлы успешно загружены'


@app.callback(
    Output('checkbox-store', 'data'),
    Output({'type': 'checkbox', 'index': ALL}, 'value'),
    Input('btn-select-files', 'n_clicks'),
    State({'type': 'checkbox', 'index': ALL}, 'value'),
    State('input_dir', 'value'),
    State('checkbox-store', 'data'),
    prevent_initial_call=True
)
def select_unselect(n_clicks: int, chk_box: list, dir_path: str, checkbox_states):
    if n_clicks > 0:
        files = os.listdir(dir_path)
        # Получаем список всех файлов, которые могут быть выбраны
        selectable_files = [file for file in files if not file.endswith(('_translated.docx', '_translated_done.docx',
                                                                         '_translated.txt', '_translated_done.txt')) and not os.path.isdir(
            os.path.join(DIRECTORY_PATH, file))]

        if n_clicks % 2 == 0:
            # Если четное нажатие, снимаем все галочки
            return [], [[] for _ in selectable_files]
        else:
            # Если нечетное нажатие, выбираем все файлы
            chk_selected = [[file] for file in selectable_files]
            return chk_selected, chk_selected
    return checkbox_states, chk_box

@app.callback(
    Output('text_in', 'value', allow_duplicate=True),
    Output('text_out', 'value', allow_duplicate=True),
    Output('url', 'href'),
    Input('clear-button', 'n_clicks'),
    prevent_initial_call=True
)
def insert_input_text(n_clicks: int):
    if n_clicks:
        if int(n_clicks) > 0:
            return '', '', f'/'
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output('uuid-store', 'data'),
    Input('uuid-store', 'data')  # Вызываем callback при загрузке
)
def generate_uuid(existing_uuid):
    if existing_uuid is None:
        uuid_session = str(uuid.uuid4())
        return uuid_session
    return existing_uuid


@app.callback(Output('output-text', 'children', allow_duplicate=True),
              Output('translate-button', 'disabled'),
              Input('translate-button', 'n_clicks'),
              prevent_initial_call=True
              )
def transl_but_pushed(n_clicks: int):
    if n_clicks > 0:
        return 'Добавляем в очередь', True
    return False


# Коллбэк для обработки обычного перевода
@app.callback(
    Output('output-text', 'children'),
    Output('text_out', 'value', allow_duplicate=True),
    Output('translate-button', 'disabled', allow_duplicate=True),
    Output('button-state', 'data', allow_duplicate=True),
    Output('text_in', 'readOnly', allow_duplicate=True),
    Input('output-text', 'children'),
    # Input('translate-button', 'n_clicks'),
    State('language-dropdown', 'value'),
    State('uuid-store', 'data'),
    State('button-state', 'data'),
    State('text_in', 'value'),
    State('checklist', 'value'),
    State('language-dst', 'value'),
    State('checklist_base', 'value'),
    prevent_initial_call=True
)
def translate_text(mark: str, target_language: str, uuid_value: str, button_state: dict, text_in_textarea: str,
                   auto_detect: list, lang_dst: str, base_model):
    # if n_clicks is None:
    #    return "Введите текст и выберите язык для перевода.", False
    if not mark == 'Добавляем в очередь':
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if (target_language or len(auto_detect) > 0) and text_in_textarea:
        redis_cache_result.delete(uuid_value)

        button_state['disabled'] = True
        paragraphs = text_in_textarea.split('\n')

        for paragraph in paragraphs:

            if len(auto_detect) > 0:
                lang_parag = LangDetect().detection(paragraph)
                lang_src = lang_parag['language']
            else:
                lang_src = target_language

            if paragraph == "":
                paragraph = "<%!@#emt#@!%>"

            lang_code_from = lang_src
            if len(lang_code_from) == 3:
                lang_space = ""
            else:
                lang_space = " "

            lang_code_to = lang_dst
            worked_space = len(lang_code_from) + len(lang_space) + len(lang_code_to) + len(lang_space) + 1
            head_space = ""
            for i in range(30 - worked_space):
                head_space += " "

            if base_model == ['checked']:
                b_model = 'f'
            else:
                b_model = ' '

            redis_db.rpush('message_queue',
                           f'{uuid_value}{lang_code_from}{lang_space}{lang_code_to}{lang_space}{b_model}{head_space}{paragraph}')
        return 'Добавлено в очередь', '', button_state['disabled'], button_state, True
    # return "Пожалуйста, выберите язык.", dash.no_update


@app.callback(
    Output('text_out', 'value'),
    Output('translate-button', 'disabled', allow_duplicate=True),
    Output('button-state', 'data', allow_duplicate=True),
    Output('text_in', 'readOnly', allow_duplicate=True),
    Input('interval-component', 'n_intervals'),
    State('uuid-store', 'data'),
    State('button-state', 'data'),
    State('text_in', 'value'),
    State('text_out', 'value'),
)
def show_result_in_cache(n_inter: int, uuid_data: str, button_state: dict, text_in_ta: str, text_out_ta: str):
    if uuid_data:

        result_session = redis_cache_result.get(uuid_data)
        if result_session:
            if len(result_session.decode('utf-8').split('\n')) < len(text_in_ta.split('\n')):
                button_state['disabled'] = True
                return result_session.decode('utf-8'), button_state['disabled'], button_state, True
            else:
                button_state['disabled'] = False
                return result_session.decode('utf-8'), button_state['disabled'], button_state, False
        else:
            return None, dash.no_update, button_state, dash.no_update
    else:
        return None, dash.no_update, button_state, dash.no_update


@app.callback(
    Output('translate-button', 'disabled', allow_duplicate=True),
    Output('button-state', 'data', allow_duplicate=True),
    Input('text_in', 'value'),
    State('button-state', 'data'),
    State('uuid-store', 'data')
)
def update_text_in(text_in: str, button_state: dict, uuid: str):
    button_state['disabled'] = False
    redis_cache_result.delete(uuid)
    return button_state['disabled'], button_state


@app.callback(
    Output('clear-button', 'disabled'),
    Input('text_in', 'readOnly')
)
def update_text_in(text_in_state):
    if text_in_state:
        return True
    else:
        return False


@app.callback(
    Output('links-list', 'children', allow_duplicate=True),
    Output('input_dir', 'value'),
    Output('url', 'href', allow_duplicate=True),
    Input('interval-component', 'n_intervals'),
    Input('refresh-button', 'n_clicks'),
    State('url', 'href'),
    State('input_dir', 'value'),
    State('checkbox-store', 'data'),
    prevent_initial_call=True
)
def refresh_docs(n_interv: int, n_click: int | None, href: str, dir_docs: str, checkbox_states: list):
    global DIRECTORY_PATH

    if n_click:
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
                                )], dir_docs, '/'
            files = os.listdir(dir_docs)
            supported_files = [file for file in files if
                               file[file.rfind('.') + 1:] in ['doc', 'docx', 'pdf', 'txt', 'odt', 'rtf', 'ppt', 'pptx']]
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
                                )], dir_docs, '/'
            set_key('.env', 'DOCS_DIRECTORY', dir_docs)
            DIRECTORY_PATH = dir_docs
            settings.docs_directory = dir_docs

            return create_links(DIRECTORY_PATH, checkbox_states), settings.docs_directory, '/'

    return create_links(DIRECTORY_PATH, checkbox_states), dash.no_update, dash.no_update


def add_queue_docx_part(part_doc: list, uuid: str, name_count: int, name: str, type_part: str, lang_dst: str, base_m):
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

        if text_doc == "":
            text_doc = "<%!@#emt#@!%>"

        lang_code_from = lang_src
        if len(lang_code_from) == 3:
            lang_space = ""
        else:
            lang_space = " "

        lang_code_to = lang_dst
        worked_space = len(lang_code_from) + len(lang_space) + len(lang_code_to) + len(lang_space) + 1
        head_space = ""
        for j in range(30 - worked_space):
            head_space += " "
        # изменить
        # f'{uuid_value}{lang_code_from}{lang_space}{lang_code_to}{lang_space}f{head_space}{paragraph}')
        string_to_send = f'{uuid}{name_count}{name}{i}{type_part}{lang_code_from}{lang_space}{lang_code_to}{lang_space}{base_m}{head_space}{text_doc}'
        redis_db.rpush('docx_queue', string_to_send)
        time.sleep(0.1)


def docx_processing(file_name: str, uuid: str, lang_dst: str, base_m, tmp_path: str = DIRECTORY_PATH):
    global DIRECTORY_PATH
    # Возможно ошибка тут
    load_dotenv('.env')
    os.environ.get('DOCS_DIRECTORY')
    DIRECTORY_PATH = settings.docs_directory
    # print(f'but {DIRECTORY_PATH}')
    # print(f'but2 {DIRECTORY_PATH}')

    only_name = f'{file_name[:file_name.rfind('.')]}_translated.docx'

    count_name = str(len(only_name))
    if len(count_name) < 3:
        for i in range(3 - len(count_name)):
            count_name += " "

    copy_file_name = os.path.join(DIRECTORY_PATH, only_name)
    # print(copy_file_name)
    if not tmp_path == './temp':
        tmp_path = settings.docs_directory

    shutil.copy(os.path.join(tmp_path, file_name), copy_file_name)
    # print('1')
    old_paragraphs = DocxReader(method=2).file_read(copy_file_name)
    old_header, old_footer = DocxReader(method=2).colontituls_read(copy_file_name)
    old_table, old_n_table = DocxReader(method=2).table_read(copy_file_name)

    add_queue_docx_part(old_header, uuid, count_name, only_name, 'ucln', lang_dst, base_m)
    add_queue_docx_part(old_footer, uuid, count_name, only_name, 'dcln', lang_dst, base_m)
    add_queue_docx_part(old_table, uuid, count_name, only_name, 'tabl', lang_dst, base_m)
    add_queue_docx_part(old_n_table, uuid, count_name, only_name, 'tabl', lang_dst, base_m)
    add_queue_docx_part(old_paragraphs, uuid, count_name, only_name, 'text', lang_dst, base_m)


@app.callback(
    Output('all-button', 'disabled'),
    Input('all-button', 'n_clicks'),
    State('all-button', 'disabled'),
    State('uuid-store', 'data'),
    State('input_dir', 'value'),
    State({'type': 'checkbox', 'index': ALL}, 'value'),
    State('language-dst', 'value'),
    State('checklist_base', 'value'),
    prevent_initial_call=True
)
def translate_docs(n_clicks: int, is_disabled: bool, uuid_value: str, input_dir: str, chkbox, lang_dst: str,
                   base_model):
    global DIRECTORY_PATH

    pipeline = redis_db.pipeline()
    load_dotenv('.env')
    DIRECTORY_PATH = settings.docs_directory

    files_translate = []
    if n_clicks > 0 and not is_disabled:
        for i in range(len(chkbox)):
            try:
                files_translate.append(chkbox[i][0])
            except IndexError:
                continue

        is_disabled = True
        for file_name in files_translate:  # os.listdir(DIRECTORY_PATH):
            file_ext = file_name[file_name.rfind('.') + 1:]
            only_name = f'{file_name[:file_name.rfind('.')]}_translated.docx'
            only_name_done = f'{file_name[:file_name.rfind('.')]}_translated_done.docx'

            if base_model == ['checked']:
                b_model = 'f'
            else:
                b_model = ' '

            try:
                if file_ext in ['pdf']:
                    if not os.path.exists('./temp'):
                        os.mkdir('./temp')

                    converted_path = f'./temp/{file_name[:file_name.rfind('.')]}.txt'

                    only_name = f'{file_name[:file_name.rfind('.')]}_translated.txt'
                    only_name_done = f'{file_name[:file_name.rfind('.')]}_translated_done.txt'

                    if not os.path.exists(f'{DIRECTORY_PATH}/{only_name}') or not os.path.exists(
                            f'{DIRECTORY_PATH}/{only_name_done}'):
                        PDF2TXT().func_covert(f'{DIRECTORY_PATH}/{file_name}', converted_path)

                        count_name = str(len(only_name))
                        if len(count_name) < 3:
                            for i in range(3 - len(count_name)):
                                count_name += " "

                        # print(converted_path)
                        txt_lines = TXTReader(2).file_read(converted_path)
                        # print(txt_lines)

                        for i_line, line in enumerate(txt_lines):
                            lang_old = LangDetect().detection(line.replace('\n', ''))

                            if line == "":
                                line = "<%!@#emt#@!%>"

                            lang_code_from = lang_old['language']
                            if len(lang_code_from) == 3:
                                lang_space = ""
                            else:
                                lang_space = " "

                            lang_code_to = lang_dst
                            worked_space = len(lang_code_from) + len(lang_space) + len(lang_code_to) + len(
                                lang_space) + 1
                            head_space = ""
                            for i in range(30 - worked_space):
                                head_space += " "

                            string_to_send = f'{uuid_value}{count_name}{only_name}{i_line}_txt{lang_code_from}{lang_space}{lang_code_to}{lang_space}{b_model}{head_space}{line}'
                            redis_db.rpush('docx_queue', string_to_send)

                elif file_ext == 'doc':

                    converted_path = f'./temp/{file_name[:file_name.rfind('.')]}.docx'
                    if not os.path.exists(converted_path):
                        DOC2DOCX().func_covert(f'{DIRECTORY_PATH}/{file_name}', './temp')

                    if not os.path.exists(os.path.join(DIRECTORY_PATH, only_name)) and not os.path.exists(
                            os.path.join(DIRECTORY_PATH, only_name_done)):
                        docx_processing(f'{file_name[:file_name.rfind('.')]}.docx', uuid_value, lang_dst, b_model,
                                        './temp')

                elif file_ext == 'odt':

                    converted_path = f'./temp/{file_name[:file_name.rfind('.')]}.docx'
                    if not os.path.exists(converted_path):
                        ODT2DOCX().func_covert(f'{DIRECTORY_PATH}/{file_name}', './temp')

                    if not os.path.exists(os.path.join(DIRECTORY_PATH, only_name)) and not os.path.exists(
                            os.path.join(DIRECTORY_PATH, only_name_done)):
                        docx_processing(f'{file_name[:file_name.rfind('.')]}.docx', uuid_value, lang_dst, b_model,
                                        './temp')

                elif file_ext == 'rtf':

                    converted_path = f'./temp/{file_name[:file_name.rfind('.')]}.docx'
                    if not os.path.exists(converted_path):
                        RTF2DOCX().func_covert(f'{DIRECTORY_PATH}/{file_name}', './temp')

                    if not os.path.exists(os.path.join(DIRECTORY_PATH, only_name)) and not os.path.exists(
                            os.path.join(DIRECTORY_PATH, only_name_done)):
                        docx_processing(f'{file_name[:file_name.rfind('.')]}.docx', uuid_value, lang_dst, b_model,
                                        './temp')

                elif file_ext == 'ppt' or file_ext == 'pptx':

                    converted_path = f'./temp/{file_name[:file_name.rfind('.')]}.docx'
                    if not os.path.exists(converted_path):
                        PPTX2DOCX().func_covert(f'{DIRECTORY_PATH}/{file_name}', './temp')

                    if not os.path.exists(os.path.join(DIRECTORY_PATH, only_name)) and not os.path.exists(
                            os.path.join(DIRECTORY_PATH, only_name_done)):
                        docx_processing(f'{file_name[:file_name.rfind('.')]}.docx', uuid_value, lang_dst, b_model,
                                        './temp')

                elif file_ext == 'docx':

                    if (not file_name.endswith('_translated.docx') or not file_name.endswith(
                            '_translated_done.docx')) and (not os.path.exists(
                        os.path.join(DIRECTORY_PATH, only_name)) and not os.path.exists(
                        os.path.join(DIRECTORY_PATH, only_name_done))):
                        docx_processing(file_name, uuid_value, lang_dst, b_model, )

                elif file_ext == 'txt' and not file_name.endswith(('_translated.txt', '_translated_done.txt')):
                    only_name = f'{file_name[:file_name.rfind('.')]}_translated.txt'
                    only_name_done = f'{file_name[:file_name.rfind('.')]}_translated_done.txt'

                    if not os.path.exists(os.path.join(DIRECTORY_PATH, only_name)) and not os.path.exists(
                            os.path.join(DIRECTORY_PATH, only_name_done)):
                        count_name = str(len(only_name))
                        if len(count_name) < 3:
                            for i in range(3 - len(count_name)):
                                count_name += " "

                        txt_lines = TXTReader(2).file_read(os.path.join(DIRECTORY_PATH, file_name))

                        for i_line, line in enumerate(txt_lines):
                            lang_old = LangDetect().detection(line.replace('\n', ''))

                            if line == "":
                                line = "<%!@#emt#@!%>"

                            lang_code_from = lang_old['language']
                            if len(lang_code_from) == 3:
                                lang_space = ""
                            else:
                                lang_space = " "

                            lang_code_to = lang_dst
                            worked_space = len(lang_code_from) + len(lang_space) + len(lang_code_to) + len(
                                lang_space) + 1
                            head_space = ""
                            for i in range(30 - worked_space):
                                head_space += " "

                            # f'{uuid_value}{lang_code_from}{lang_space}{lang_code_to}{lang_space}f{head_space}{paragraph}')
                            string_to_send = f'{uuid_value}{count_name}{only_name}{i_line}_txt{lang_code_from}{lang_space}{lang_code_to}{lang_space}{b_model}{head_space}{line}'
                            redis_db.rpush('docx_queue', string_to_send)

            except Exception as err:
                logging.error(f'Возникла ошибка при обрабработки документа: {err}')
                continue

        is_disabled = False
        return is_disabled

    return is_disabled


@app.callback(
    Output('text_in', 'value'),
    Output('text_out', 'value', allow_duplicate=True),
    Output('input_dir', 'value', allow_duplicate=True),
    Input('url', 'href'),
    State('url', 'pathname')
)
def select_ref(href: str, pathname: str):
    transl_str = ''

    if href == f'/':
        return "", transl_str, DIRECTORY_PATH

    try:
        file_name = urllib.parse.unquote(pathname[1:])
        file_ext = file_name[file_name.rfind('.') + 1:]
        file_path = os.path.join(DIRECTORY_PATH, file_name)

        if file_ext == 'txt':
            data_str = TXTReader(method=1).file_read(file_path)
            transl_path = os.path.join(DIRECTORY_PATH, f'{file_name[:file_name.rfind('.')]}_translated.{file_ext}')
            transl_path_done = os.path.join(DIRECTORY_PATH,
                                            f'{file_name[:file_name.rfind('.')]}_translated_done.{file_ext}')

            if os.path.exists(transl_path):
                transl_str = TXTReader(method=1).file_read(transl_path)
            elif os.path.exists(transl_path_done):
                transl_str = TXTReader(method=1).file_read(transl_path_done)
        elif file_ext == 'pdf':
            if not os.path.exists(f'./temp/{file_name}'):
                data_str = PDFReader(method=1).file_read(file_path)
            else:
                data_str = TXTReader(method=1).file_read(f'./temp/{file_name[:-3]}txt')

            transl_path = os.path.join(DIRECTORY_PATH, f'{file_name[:file_name.rfind('.')]}_translated.txt')
            transl_path_done = os.path.join(DIRECTORY_PATH,
                                            f'{file_name[:file_name.rfind('.')]}_translated_done.txt')

            if os.path.exists(transl_path):
                transl_str = TXTReader(method=1).file_read(transl_path)
            elif os.path.exists(transl_path_done):
                transl_str = TXTReader(method=1).file_read(transl_path_done)

        elif file_ext == 'docx':
            data_str = DocxReader(method=1).file_read(file_path)
            transl_path = os.path.join(DIRECTORY_PATH, f'{file_name[:file_name.rfind('.')]}_translated.{file_ext}')
            transl_path_done = os.path.join(DIRECTORY_PATH,
                                            f'{file_name[:file_name.rfind('.')]}_translated_done.{file_ext}')

            if os.path.exists(transl_path):
                transl_str = DocxReader(method=1).file_read(transl_path)
            elif os.path.exists(transl_path_done):
                transl_str = DocxReader(method=1).file_read(transl_path_done)

        elif file_ext in ['doc', 'odt', 'rtf', 'ppt', 'pptx', 'pdf']:
            converted_file = os.path.join(os.path.abspath('.'), 'temp', f'{file_name[:file_name.rfind('.')]}.docx')
            if not os.path.exists(converted_file):

                match file_ext:
                    case 'doc':
                        DOC2DOCX().func_covert(f'{DIRECTORY_PATH}/{file_name}', './temp')
                    case 'pdf':
                        # PDF2DOCX().func_covert(file_path, converted_file)
                        pass
                    case 'odt':
                        ODT2DOCX().func_covert(f'{DIRECTORY_PATH}/{file_name}', './temp')
                    case 'rtf':
                        RTF2DOCX().func_covert(f'{DIRECTORY_PATH}/{file_name}', './temp')
                    case 'ppt' | 'pptx':
                        PPTX2DOCX().func_covert(f'{DIRECTORY_PATH}/{file_name}', './temp')

            data_str = DocxReader(method=1).file_read(converted_file)
            transl_path = os.path.join(DIRECTORY_PATH, f'{file_name[:file_name.rfind('.')]}_translated.docx')
            transl_path_done = os.path.join(DIRECTORY_PATH,
                                            f'{file_name[:file_name.rfind('.')]}_translated_done.docx')

            if os.path.exists(transl_path):
                transl_str = DocxReader(method=1).file_read(transl_path)
            elif os.path.exists(transl_path_done):
                transl_str = DocxReader(method=1).file_read(transl_path_done)

        else:
            data_str = f'Файл {file_name} не поддерживается'
        return data_str, transl_str, DIRECTORY_PATH
    except Exception as e:
        return f'Ошибка при обработке файла: {str(e)}'


# Запускаем сервер
if __name__ == '__main__':
    load_dotenv('.env')
    os.environ.get('DOCS_DIRECTORY')

    if settings.clear_queue:
        redis_db.delete('message_queue')
        redis_db.delete('docx_queue')
    # Обязательно нужна для калибровки
    for i in range(9):
        redis_db.rpush('message_queue', f'000000000000000000000000000000000000 ')
    # redis_db.rpush('docx_queue', f'000000000000000000000000000000000000 ')

    threading.Thread(target=client_program, args=(redis_db, redis_cache_result)).start()
    app.run_server(host=settings.ip_web_server,
                   port=settings.port_web_server,
                   debug=settings.debug)

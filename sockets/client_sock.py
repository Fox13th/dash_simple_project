import logging
import os
import pathlib
import socket
import time

import dotenv
import redis
from requests.compat import chardet

from core import config
from services.list_docs import replace_text_in_docx, replace_header_footer_text, replace_text_in_table

settings = config.get_settings()


def find_mark(text: str):
    mark = ''
    min_index = len(text)
    for substring in ['text', 'tabl', 'ucln', 'dcln', '_txt']:
        index = text.find(substring)
        if index != -1 and index < min_index:
            min_index = index
            mark = substring
    return min_index, mark


def send_message(conn, message: str, docx: bool):
    uuid_from_queue = message.decode('utf-8')[:36]
    if docx:
        count_name_docx = message.decode('utf-8')[36:39]
        clear_count = int(str(count_name_docx).replace(' ', ''))
        file_name = message.decode('utf-8')[39:39 + clear_count]

        min_index, mark = find_mark(message.decode('utf-8')[39 + clear_count:])

        num_parag = message.decode('utf-8')[39 + clear_count:39 + clear_count + min_index]
        message_to_send = message.decode('utf-8')[39 + clear_count + min_index + 4:]
        if message_to_send == '':
            message_to_send = ' '

        if mark == 'tabl':
            num_table = int(message_to_send[message_to_send.find('table:') + 6:message_to_send.find('row:')])
            num_row = int(message_to_send[message_to_send.find('row:') + 4:message_to_send.find('cell:')])
            num_cell = int(message_to_send[message_to_send.find('cell:') + 5:message_to_send.find('n_table:')])

            nested_table = int(message_to_send[message_to_send.find('n_table:') + 8:message_to_send.find('n_row:')])
            nested_row = int(message_to_send[message_to_send.find('n_row:') + 6:message_to_send.find('n_cell:')])
            nested_cell = int(message_to_send[message_to_send.find('n_cell:') + 7:message_to_send.find('index:')])

            num_parag = message_to_send[message_to_send.find('index:') + 6:message_to_send.find('text:')]
            only_msg = message_to_send[message_to_send.find('text:') + 5:]
            message_to_send = f'{message_to_send[:message_to_send.find('table:')]}{only_msg}'
    else:
        message_to_send = ' '

    conn.sendall(message_to_send.encode('utf-8'))
    # recv_msg = conn.recv(8192)

    recv_msg = conn.recv(8192).decode('utf-8')

    result = ""
    start_time = time.time()
    while not recv_msg[-13:] == "<%!@#end#@!%>":
        end_time = time.time() - start_time
        rec_data = conn.recv(8192).decode("utf-8")
        if rec_data == "" and end_time >= int(os.environ.get('TIMEOUT', '120')):
            conn.close()
            return "Ошибка соединения! Удаленный сервер разорвал соединение..."

        elif not rec_data == "":
            start_time = time.time()
        recv_msg = f'{recv_msg} {rec_data}'

    recv_msg = f'{recv_msg.replace("<%!@#end#@!%>", "").replace("<unk>", "")}'
    if mark == '_txt':
        recv_msg = f'{recv_msg}\n'

    result += recv_msg
    #print(result)
    dotenv.load_dotenv('../.env')
    os.environ.get('DOCS_DIRECTORY')
    # print(settings.docs_directory)
    #print(mark)
    if docx:
        match mark:
            case 'text':
                file_path = pathlib.Path(os.path.join(settings.docs_directory, file_name))
                done_if = replace_text_in_docx(file_path,
                                     int(num_parag),
                                     result)
                if done_if:
                    file_path.rename(os.path.join(settings.docs_directory, f'{file_name[:-5]}_done.docx'))
            case 'tabl':
                replace_text_in_table(doc_path=os.path.join(settings.docs_directory, file_name),
                                      table_index=num_table,
                                      row_index=num_row,
                                      cell_index=num_cell,
                                      n_index=nested_table,
                                      n_row_index=nested_row,
                                      n_cell_index=nested_cell,
                                      index=int(num_parag),
                                      new_text=result)
            case 'ucln':
                replace_header_footer_text(os.path.join(settings.docs_directory, file_name),
                                           'up',
                                           int(num_parag),
                                           result)
            case 'dcln':
                replace_header_footer_text(os.path.join(settings.docs_directory, file_name),
                                           'down',
                                           int(num_parag),
                                           result)
            case '_txt':

                f_path = os.path.join(settings.docs_directory, file_name)
                orig_f_name = f'{file_name[:-15]}.txt'
                if os.path.exists(f'./temp/{orig_f_name}'):
                    orig_file = f'./temp/{orig_f_name}'
                else:
                    orig_file = os.path.join(settings.docs_directory, f'{file_name[:-15]}.txt')

                with open(f_path, 'a', encoding='utf-8') as f_write:
                    f_write.write(result)

                with open(f_path, 'r', encoding='utf-8') as f_read:
                    line_count = sum(1 for line in f_read)

                with open(orig_file, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']

                with open(orig_file, 'r', encoding=encoding) as f_read:
                    line_count_orig = sum(1 for line in f_read)

                with open(f'{settings.docs_directory}/{orig_f_name}.log', 'w', encoding='utf-8') as f_log:
                    f_log.write(str(int(line_count / line_count_orig * 100)))

                if line_count >= line_count_orig:
                    file_pth = pathlib.Path(os.path.join(settings.docs_directory, file_name))
                    file_pth.rename(os.path.join(settings.docs_directory, f'{file_name[:-4]}_done.txt'))


def client_program(redis_db: redis.Redis, redis_cache_result: redis.Redis):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((settings.socket_host, settings.socket_port))
                logging.info('Connection established')
                while True:

                    msg = redis_db.lpop('message_queue')
                    msg_docx = redis_db.lpop('docx_queue')

                    if msg:
                        uuid_from_queue = msg.decode('utf-8')[:36]
                        message_to_send = msg.decode('utf-8')[36:]
                        if message_to_send == '':
                            message_to_send = ' '

                        if not uuid_from_queue == '000000000000000000000000000000000000':
                            pass
                            #print(f'Отправка сообщения: {message_to_send}')

                        client_socket.sendall(message_to_send.encode('utf-8'))
                        if not uuid_from_queue == '000000000000000000000000000000000000':
                            pass
                            #print(f'Сообщение отправлено: {message_to_send}')

                        recv_msg = client_socket.recv(8192).decode('utf-8')

                        result = ""
                        start_time = time.time()
                        while not recv_msg[-13:] == "<%!@#end#@!%>":
                            end_time = time.time() - start_time
                            rec_data = client_socket.recv(8192).decode("utf-8")
                            if rec_data == "" and end_time >= int(os.environ.get('TIMEOUT', '120')):
                                client_socket.close()
                                return "Ошибка соединения! Удаленный сервер разорвал соединение..."

                            elif not rec_data == "":
                                start_time = time.time()
                            recv_msg = f'{recv_msg} {rec_data}'

                        recv_msg = f'{recv_msg.replace("<%!@#end#@!%>", "").replace("<unk>", "")}\n'
                        result += recv_msg

                        if not uuid_from_queue == '000000000000000000000000000000000000':
                            #print(f"Сообщение от сервера для {uuid_from_queue}:", f'{result}\n')

                            cache_value = redis_cache_result.get(uuid_from_queue)
                            if cache_value is not None:
                                res_value = f'{cache_value.decode('utf-8')}{result}'
                            else:
                                res_value = result

                            redis_cache_result.set(uuid_from_queue, res_value, settings.redis_expiration)

                        time.sleep(0.1)

                    if msg_docx:
                        try:
                            send_message(client_socket, msg_docx, docx=True)
                        except IndexError:
                            continue

        except Exception as err:
            logging.error("Произошла ошибка: %s", err)
            time.sleep(5)

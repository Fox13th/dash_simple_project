import os

from dash import html, dcc


def create_links(dir_path: str, checkbox_states: list) -> list:
    files = os.listdir(dir_path)

    links = []
    for file in files:
        file_ext = file[file.rfind('.') + 1:]
        not_end = ('_translated.docx', '_translated.txt', '_translated_done.txt', '_translated_done.docx')
        if file_ext in ['doc', 'docx', 'pdf', 'txt', 'odt', 'rtf', 'ppt', 'pptx'] and not file.endswith(not_end):
            file_path = os.path.join(dir_path, file)
            #if file_ext == 'docx':
                #file_ext = 'doc'
            style_links = {
                'display': 'flex',
                'alignItems': 'center',
                'color': '#E0115F',
                'textDecoration': 'none'}

            if (os.path.exists(os.path.join(dir_path, f'{file[:file.rfind('.')]}_translated.docx')) and file_ext in [
                'docx', 'doc', 'odt', 'rtf', 'ppt', 'pptx']) or (os.path.exists(
                os.path.join(dir_path, f'{file[:file.rfind('.')]}_translated.txt')) and file_ext in ['txt', 'docx', 'pdf']):
                style_links['color'] = '#ffa500'
            elif (os.path.exists(os.path.join(dir_path, f'{file[:file.rfind('.')]}_translated_done.docx')) and file_ext in [
                'docx', 'doc', 'pdf', 'odt', 'rtf', 'ppt', 'pptx']) or (os.path.exists(
                os.path.join(dir_path, f'{file[:file.rfind('.')]}_translated_done.txt')) and file_ext in ['txt', 'docx', 'pdf']):
                style_links['color'] = 'green'
            else:
                style_links['color'] = '#E0115F'

            is_checked = [file] in checkbox_states

            style_progress = {
                'color': '#ffa500',
                'marginRight': '10px'
                }
            if os.path.exists(f'{file_path[:file_path.rfind(".") + 1]}log'):
                with open(f'{file_path[:file_path.rfind(".") + 1]}log', 'r', encoding='utf-8') as f_read:
                    progress_str = f'{f_read.readline()}%'
                    if progress_str == '100%':
                        style_progress['color'] = 'green'
            else:
                progress_str = ''
                
            if file_ext == 'docx':
                file_ext = 'doc'

            links.append(html.Li(
                children=[
                    html.Div(
                        children=[
                            html.Div(id=f'progress_{file}',
                                     children=progress_str.replace('\n', ''),
                                     style=style_progress),
                            dcc.Checklist(
                                options=[{'label': ' ', 'value': file}],  # Без метки, только галочка
                                value=[file] if is_checked else [],
                                #value=[],  # Галочка выбрана по умолчанию
                                id={'type': 'checkbox', 'index': file},  # ID для каждого чекбокса
                                inline=True,  # Горизонтальное расположение
                                style={'marginRight': '10px'},
                                persistence=True,  # Сохраняйте состояние между сессиями
                                persistence_type='memory'  # Храните в памяти
                            ),
                            dcc.Link(children=[
                                html.Img(src=f'./assets/{file_ext}.svg',
                                         style={'width': '30px',
                                                'height': '30px',
                                                'marginRight': '10px'}),
                                file],
                                href=f'{file}',
                                id=f'{file.replace('.', '/')}',
                                style=style_links)
                        ],
                        style={'display': 'flex', 'alignItems': 'center'}
                    )
                ],

                #id=f'li_ref',
                className='li_ref',
                style={
                    'transition': 'transform .6s ease'
                }),
            )
    return links

import os

from dash import html, dcc


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
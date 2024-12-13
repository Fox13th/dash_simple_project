import os

import dotenv
from dash import html, dcc

from core import config
from layouts.links import create_links

settings = config.get_settings()

dotenv.load_dotenv()


def get_sidebar(path_dir: str):
    path_dir = os.environ.get('DOCS_DIRECTORY')

    return html.Div(
        [
            dcc.Store(id='file-store', data=[]),
            dcc.Store(id='checkbox-store', data=[]),
            dcc.Download(id="download-zip"),
            html.Div(id='checkbox-container'),
            html.Div(children=[
                html.H2("Ссылки на файлы", style={'color': '#4d705c'}),
                dcc.Location(id='url', refresh=False),
                dcc.Loading(
                    id='load_button',
                    type='circle',
                    color='#00a86b',#00a86b',
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
                html.Button('', id='queue-clear',
                            className='button',
                            style={
                                'display': 'flex',
                                'width': '55px',
                                'height': '55px',
                                'border': 'none',
                                'margin-left': '20px',
                                'border-radius': '40px',
                                'background': 'none',
                                'background-image': "url('./assets/stop.svg')",
                                'background-size': 'cover',
                                'background-repeat': 'no-repeat',

                                'transition': 'transform 0.1s'
                            }),

            ], style={'display': 'flex',
                      'flexDirection': 'row',
                      'alignItems': 'center',
                      'justifyContent': 'center',
                      }),
            html.Div(style={'display': 'flex',
                            'flexDirection': 'row',
                            'alignItems': 'left',
                            'justifyContent': 'left',
                            },
                     children=[
                         html.Button('', id="btn-select-files",
                                     n_clicks=0,
                                     className='button',
                                     style={
                                         'display': 'flex',
                                         'width': '20px',
                                         'height': '20px',
                                         'border': 'none',
                                         'margin-left': '40px',
                                         #'margin-right': '40px',
                                         'border-radius': '5px',
                                         'background': 'none',
                                         'background-image': "url('./assets/select.svg')",
                                         'background-size': 'cover',
                                         'background-repeat': 'no-repeat',
                                         'transition': 'transform 0.1s'
                                     }),
                         dcc.Input(id='input_dir', value=path_dir, style={'width': '195px', 'display': 'none'}),
                         dcc.Upload(
                             id='upload-data',
                             children=html.Button('', id="btn-select-dir",
                                                  n_clicks=0,
                                                  className='button',
                                                  style={
                                                      'display': 'flex',
                                                      'width': '25px',
                                                      'height': '25px',
                                                      'border': 'none',
                                                      'margin-left': '20px',
                                                      'border-radius': '5px',
                                                      'background': 'none',
                                                      'background-image': "url('./assets/folder_open.svg')",
                                                      'background-size': 'cover',
                                                      'background-repeat': 'no-repeat',
                                                      'transition': 'transform 0.1s'
                                                  }),
                             multiple=True  # разрешить загрузку только одного файла
                         ),
                         html.Button('', id="save-button",
                                     n_clicks=0,
                                     className='button',
                                     style={
                                         'display': 'flex',
                                         'width': '25px',
                                         'height': '25px',
                                         'border': 'none',
                                         'margin-left': '20px',
                                         'border-radius': '5px',
                                         'background': 'none',
                                         'background-image': "url('./assets/save.svg')",
                                         'background-size': 'cover',
                                         'background-repeat': 'no-repeat',
                                         'transition': 'transform 0.1s'
                                     }),
                         html.Button('', id='refresh-button',
                                     className='button',
                                     style={
                                         'display': 'none',
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
                         html.Button('', id='delete-button',
                                     className='button',
                                     style={
                                         'display': 'flex',
                                         'width': '25px',
                                         'height': '25px',
                                         'border': 'none',
                                         'margin-left': '20px',
                                         'border-radius': '5px',
                                         'background': 'none',
                                         'background-image': "url('./assets/delete.svg')",
                                         'background-size': 'cover',
                                         'background-repeat': 'no-repeat',

                                         'transition': 'transform 0.1s'
                                     }),
                     ]
                     ),
            html.Hr(),
            html.Ul(create_links(path_dir, []), style={'list-style': 'none'}, id='links-list')
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

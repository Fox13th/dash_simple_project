from dash import html, dcc

from layouts.links import create_links


def get_sidebar(path_dir: str):
    return html.Div(
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
                         dcc.Input(id='input_dir', value=path_dir, style={'width': '195px'}),
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
            html.Ul(create_links(path_dir), style={'list-style': 'none'}, id='links-list')
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

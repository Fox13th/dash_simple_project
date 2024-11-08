from dash import dcc, html


def get_content():
    return html.Div([

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
                                      dcc.Checklist(
                                          id='my-checklist',
                                          options=[
                                              {'label': 'Автоопределение', 'value': 'checked'}
                                          ],
                                          value=[],
                                          # Значения по умолчанию (пустой список означает, что флажок не установлен)
                                          inline=True  # Отображение в одну строку
                                      )
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
                                          html.Label('  aaa')
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

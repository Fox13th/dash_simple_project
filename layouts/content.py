from dash import dcc, html

from core import config

settings = config.get_settings()


def read_list_lang() -> dict[str]:
    lang_list = {}
    with open(settings.lang_list, 'r', encoding='utf-8') as f:
        f_lines = f.readlines()
    for line in f_lines:
        lang_l = line.replace("\"", "").replace(",", "").replace("\n", "").split(":")
        lang_list[lang_l[0]] = lang_l[1]
    return lang_list


def get_content():
    return html.Div([
        # dbc.Toast(
        #    "Это уведомление",
        #    id="toast",
        #    is_open=False,
        #    header="Уведомление",
        #    duration=4000,  # Время отображения (в миллисекундах)
        #    style={"position": "fixed", "top": 20, "right": 20}
        # ),
        dcc.Store(id='uuid-store'),  # Хранение UUID
        html.Div(style={'background-color': '#4d705c', #B22222
                        'height': '250px',
                        'justifyContent': 'center',
                        'width': '75vw',
                        },
                 children=[
                     html.H1('система перевода документов', style={'margin-top': '0px',
                                                                                     'text-align': 'center',
                                                                                     'padding': '1px',
                                                                                     'color': '#f6e4da'}),
                     html.P('Осуществление перевода текстов на разных языках', style={
                         'text-align': 'center',
                         'color': '#f6e4da'}),
                     html.Div(style={'display': 'flex',
                                     'flexDirection': 'row',
                                     'alignItems': 'center',
                                     'justifyContent': 'center',
                                     'gap': '10px',
                                     'margin': '350px auto',
                                     'maxWidth': '800px',
                                     'margin-top': '100px',
                                     'background-color': '#f8f9fa',
                                     'border': '2px solid lightgray',
                                     'padding': '20px',
                                     'borderRadius': '5px',
                                     'boxShadow': '2px 2px 10px rgba(0, 0, 0, 0.1)'
                                     },
                              children=[
                                  html.Div(children=[
                                      html.Label('Выберите язык (исходный):'),
                                      dcc.Dropdown(
                                          id='language-dropdown',
                                          options=read_list_lang(),
                                          className='dash-dropdown',
                                          placeholder='Выберите язык',
                                          style={'width': '300px', 'height': '30px'}
                                      ),
                                      dcc.Checklist(
                                          id='checklist',
                                          options=[
                                              {'label': 'Автоопределение', 'value': 'checked'}
                                          ],
                                          value=['checked'],
                                          # Значения по умолчанию (пустой список означает, что флажок не установлен)
                                          inline=True,
                                          style={'margin-top': '10px'}
                                      )
                                  ]),

                                  html.Div(children=[
                                      html.Div(children=[
                                          html.Label("Выберите язык (целевой):"),
                                          dcc.Dropdown(
                                              id='language-dst',
                                              options=[
                                                  {'label': 'Английский', 'value': 'en'},
                                                  {'label': 'Русский', 'value': 'ru'},

                                              ],
                                              value='ru',
                                              placeholder='Выберите язык',
                                              style={'width': '300px', 'height': '30px'}
                                          ),
                                      ],
                                          style={'margin-bottom': '30px'})
                                  ]),
                                  html.Div(
                                      children=[
                                          html.Button(
                                              children=[
                                                  html.Img(id='img_transl', src='./assets/translate-hover.svg',
                                                           style={'height': '30px', 'marginRight': '10px'}),
                                                  'Перевести'
                                              ],
                                              id='translate-button',
                                              className='button',
                                              style={
                                                  'display': 'flex',
                                                  'alignItems': 'center',
                                                  'width': '120px',
                                                  'height': '40px',
                                                  'border': 'none',
                                              #    'margin-bottom': '30px',
                                                  'margin-left': '20px',
                                                  'border-radius': '5px',
                                                  'box-shadow': '1px 1px 5px black',
                                                  'transition': 'transform 0.1s'
                                              }),
                                          dcc.Checklist(
                                              id='checklist_base',
                                              options=[
                                                  {'label': 'base-модель', 'value': 'checked'}
                                              ],
                                              value=['checked'],
                                              # Значения по умолчанию (пустой список означает, что флажок не установлен)
                                              inline=True,
                                              style={
                                                     'margin-top': '10px',
                                                     'margin-left': '15px'}
                                          )
                                      ],
                                      style={'margin-top': '25px'}
                                  )

                              ]),
                 ]),

        html.Div(style={'display': 'flex',
                        'flexDirection': 'row',
                        'gap': '10px',
                        'height': '50vh',
                        'margin': '10px auto',
                        'maxWidth': '1300px',
                        'margin-top': '100px',
                        'background-color': '#f8f9fa',
                        'border': '2px solid lightgray',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'boxShadow': '2px 2px 10px rgba(0, 0, 0, 0.1)'
                        },
                 children=[
                     html.Div(
                         children=[
                             dcc.Textarea(id='text_in',
                                          value='',
                                          placeholder='Введите текст здесь...',
                                          style={'width': '100%', 'height': '49.5vh', 'resize': 'none'}),
                             html.Button(
                                 '',
                                 id='clear-button',
                                 className='button',
                                 style={
                                     'position': 'absolute',
                                     'top': '10px',
                                     'right': '5px',
                                     'width': '20px',
                                     'height': '20px',
                                     'backgroundColor': '#4CAF50',
                                     'color': 'white',
                                     'border': 'none',
                                     'padding': '5px 10px',
                                     'cursor': 'pointer',
                                     'background': 'none',
                                     'background-image': "url('./assets/close.svg')",
                                     'background-size': 'cover',
                                     'background-repeat': 'no-repeat'
                                 }
                             ),
                         ],
                         style={'position': 'relative', 'width': '1200px', 'height': '150px'}
                     ),

                     dcc.Textarea(id='text_out',
                                  value='',
                                  placeholder='Здесь будет обработанный',
                                  readOnly=True,
                                  style={'width': '100%', 'height': '49.5vh', 'resize': 'none'}),
                 ]
                 ),
        html.P('Версия от 16.11.2024',
               style={'margin-top': '10px',
                      'text-align': 'center',
                      'color': 'grey'}),

        dcc.Interval(
            id='interval-component',
            interval=500,
            n_intervals=0
        ),
        dcc.Store(id='button-state', data={'disabled': False}),
        dcc.Store(id='qaz'),
        html.Div(id='output-text'),
    ])

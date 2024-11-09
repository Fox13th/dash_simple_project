from docx import Document


def replace_text_in_docx(doc_path: str, index: int, new_text: str):
    """Замена обычного текста в docx по индексу"""

    doc = Document(doc_path)

    if index < len(doc.paragraphs):
        para = doc.paragraphs[index]
        inline = para.runs
        for i in range(len(inline)):
            inline[i].text = new_text

    doc.save(doc_path)


# Пример использования
# replace_text_in_docx('../test/1_test.docx', 1, 'Message received: en')


# Функция для замены текста в колонтитулах
def replace_header_footer_text(doc_path: str, type_col: str, index: int, new_text):
    doc = Document(doc_path)

    for section in doc.sections:

        match type_col:
            case 'up':
                colont = section.header
            case _:
                colont = section.footer

        if index < len(colont.paragraphs):
            para = colont.paragraphs[index]
            inline = para.runs
            for i in range(len(inline)):
                inline[i].text = new_text

    doc.save(doc_path)


#replace_header_footer_text('../test/1_test.docx', 'down', 1, 'Message received: en')


# Заменяем текст в колонтитулах


# Таблица
def replace_text_in_cell_by_index(cell, old_text, new_text):
    """Заменить текст в ячейке, включая вложенные таблицы."""
    # Заменить текст в ячейке
    if old_text in cell.text:
        cell.text = cell.text.replace(old_text, new_text)

    # Проверить наличие вложенных таблиц в ячейке
    for table in cell.tables:
        replace_text_in_table_by_index(table, old_text, new_text)


def replace_text_in_table_by_index(table, old_text, new_text):
    """Заменить текст в таблице по индексу (включая вложенные таблицы)."""
    # Проходим по строкам таблицы
    for row_index, row in enumerate(table.rows):
        # Проходим по ячейкам в строках
        for cell_index, cell in enumerate(row.cells):
            # Если индексы строки и ячейки совпадают, заменяем текст
            replace_text_in_cell_by_index(cell, old_text, new_text)


def replace_text_in_docx_by_index(file_path, old_text, new_text, table_index=None, row_index=None, cell_index=None):
    """Заменить текст в документе, включая вложенные таблицы, по индексу."""
    # Загружаем документ
    doc = Document(file_path)

    # Обрабатываем таблицу по индексу (если указаны индексы таблицы, строки и ячейки)
    if table_index is not None:
        # Получаем таблицу по индексу
        table = doc.tables[table_index]
        # Если указаны индексы строки и ячейки, заменяем только в этой ячейке
        if row_index is not None and cell_index is not None:
            cell = table.rows[row_index].cells[cell_index]
            replace_text_in_cell_by_index(cell, old_text, new_text)
        # Если указан только индекс строки, заменяем во всей строке
        elif row_index is not None:
            for cell in table.rows[row_index].cells:
                replace_text_in_cell_by_index(cell, old_text, new_text)
        # Если не указан индекс строки, заменяем в таблице
        else:
            replace_text_in_table_by_index(table, old_text, new_text)

    # Сохраняем документ
    doc.save('modified_' + file_path)

# Пример использования
# replace_text_in_docx_by_index('example.docx', 'старый текст', 'новый текст', table_index=0, row_index=1, cell_index=2)

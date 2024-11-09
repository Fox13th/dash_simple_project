from docx import Document


def replace_text_in_docx(doc_path: str, index: int, new_text: str):
    """Замена обычного текста в docx по индексу"""

    doc = Document(doc_path)

    if index < len(doc.paragraphs):
        para = doc.paragraphs[index]
        inline = para.runs
        for i in range(len(inline)):
            if i > 0:
                inline[i].text = ''
            else:
                inline[0].text = new_text

    doc.save(doc_path)


def replace_header_footer_text(doc_path: str, type_col: str, index: int, new_text):
    """Замена текста в колонтитулах docx по индексу"""
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
                if i > 0:
                    inline[i].text = ''
                else:
                    inline[0].text = new_text

    doc.save(doc_path)


# Таблица
# Функция для замены текста в таблицах
def replace_text_in_table(doc_path: str, table_index: int, row_index, cell_index, n_index: int, n_row_index: int,
                          n_cell_index: int, index: int, new_text):
    doc = Document(doc_path)
    if doc.tables:
        table = doc.tables[table_index]
        cell = table.cell(row_index, cell_index)

        if cell.tables and not n_index == -1:
            n_table = cell.tables[n_index]
            n_cell = n_table.cell(n_row_index, n_cell_index)

            if index < len(n_cell.paragraphs):
                para = n_cell.paragraphs[index]
                inline = para.runs

                for i in range(len(inline)):
                    if i > 0:
                        inline[i].text = ''
                    else:
                        inline[0].text = new_text

        else:

            if index < len(cell.paragraphs):
                para = cell.paragraphs[index]
                inline = para.runs

                for i in range(len(inline)):
                    if i > 0:
                        inline[i].text = ''
                    else:
                        inline[0].text = new_text

        doc.save(doc_path)
